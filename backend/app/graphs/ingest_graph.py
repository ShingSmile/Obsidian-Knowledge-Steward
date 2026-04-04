from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from app.config import Settings
from app.contracts.workflow import (
    IngestAnalysisResult,
    IngestWorkflowResult,
    Proposal,
    WorkflowInvokeRequest,
)
from app.graphs.checkpoint import (
    WorkflowCheckpointStatus,
    load_graph_checkpoint,
    save_graph_checkpoint,
    save_graph_checkpoint_record,
)
from app.graphs.runtime import (
    CheckpointedGraphRun,
    END,
    START,
    GraphStep,
    StateGraph,
    TraceHook,
    WorkflowGraphExecution,
    append_trace_event,
    build_base_workflow_state,
    build_workflow_graph_execution,
    build_workflow_runtime_trace_hook,
    invoke_checkpointed_compiled_graph,
    open_sqlite_checkpointer,
    save_business_checkpoint_safely,
)
from app.graphs.state import StewardState
from app.indexing.ingest import ingest_vault, resolve_requested_markdown_notes
from app.indexing.store import connect_sqlite, initialize_index_db, save_proposal_record
from app.path_semantics import normalize_to_vault_relative
from app.services.ingest_proposal import build_scoped_ingest_approval_proposal


@dataclass(frozen=True)
class IngestGraphExecution(WorkflowGraphExecution):
    ingest_result: IngestWorkflowResult
    analysis_result: IngestAnalysisResult | None
    proposal: Proposal | None
    approval_required: bool


def invoke_ingest_graph(
    request: WorkflowInvokeRequest,
    *,
    settings: Settings,
    thread_id: str,
    run_id: str,
    trace_hook: TraceHook | None = None,
) -> IngestGraphExecution:
    initial_state = build_initial_ingest_state(
        request=request,
        settings=settings,
        thread_id=thread_id,
        run_id=run_id,
    )
    runtime_trace_hook = build_workflow_runtime_trace_hook(settings, trace_hook)
    _reject_waiting_ingest_resume(
        settings=settings,
        request=request,
        thread_id=thread_id,
    )

    if _should_emit_ingest_approval_proposal(request) and not request.resume_from_checkpoint:
        execution = _invoke_ingest_graph_with_approval(
            initial_state=initial_state,
            settings=settings,
            trace_hook=runtime_trace_hook,
        )
    else:
        with open_sqlite_checkpointer(settings.index_db_path) as checkpointer:
            graph = build_ingest_graph(
                settings=settings,
                trace_hook=runtime_trace_hook,
                checkpointer=checkpointer,
            )
            execution = invoke_checkpointed_compiled_graph(
                graph_name="ingest_graph",
                graph=graph,
                initial_state=initial_state,
                checkpoint_db_path=settings.index_db_path,
                resume_from_checkpoint=request.resume_from_checkpoint,
                trace_hook=runtime_trace_hook,
                required_terminal_fields=("ingest_result",),
                resume_match_fields=("note_paths",),
            )
    final_state = execution.state

    ingest_result = final_state.get("ingest_result")
    if ingest_result is None:
        raise RuntimeError("ingest_graph completed without producing ingest_result.")

    if (
        not _should_emit_ingest_approval_proposal(request)
        and not (
            execution.checkpoint_used
            and execution.resumed_from_status == WorkflowCheckpointStatus.COMPLETED
        )
    ):
        save_business_checkpoint_safely(
            db_path=settings.index_db_path,
            graph_name="ingest_graph",
            checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
            last_completed_node=_resolve_last_completed_node(final_state),
            next_node_name=None,
            state=final_state,
        )

    shared_execution = build_workflow_graph_execution(
        graph_name="ingest_graph",
        action_type=request.action_type,
        final_state=final_state,
        checkpoint_run=execution,
    )
    return IngestGraphExecution(
        graph_name=shared_execution.graph_name,
        action_type=shared_execution.action_type,
        thread_id=shared_execution.thread_id,
        run_id=shared_execution.run_id,
        state=shared_execution.state,
        trace_events=shared_execution.trace_events,
        checkpoint_used=shared_execution.checkpoint_used,
        resumed_from_node=shared_execution.resumed_from_node,
        ingest_result=ingest_result,
        analysis_result=cast(IngestAnalysisResult | None, final_state.get("analysis_result")),
        proposal=cast(Proposal | None, final_state.get("proposal")),
        approval_required=bool(final_state.get("approval_required", False)),
    )


def build_initial_ingest_state(
    *,
    request: WorkflowInvokeRequest,
    settings: Settings,
    thread_id: str,
    run_id: str,
) -> StewardState:
    scoped_note_paths: list[str] = []
    if request.note_path or request.note_paths:
        scoped_note_paths = [
            normalize_to_vault_relative(
                note_path,
                vault_root=settings.sample_vault_dir,
            )
            for note_path in resolve_requested_markdown_notes(
                settings.sample_vault_dir,
                note_path=request.note_path,
                note_paths=request.note_paths,
            )
        ]

    return {
        **build_base_workflow_state(
            request,
            thread_id=thread_id,
            run_id=run_id,
        ),
        # 这里把 single / multi scoped ingest 都收敛成规范化后的 note_paths 列表，
        # 是为了让 checkpoint 恢复判断只依赖一个稳定字段，避免同一 scope 因参数形态不同而串味。
        "note_path": None,
        "note_paths": scoped_note_paths,
        "analysis_result": None,
    }


def build_ingest_graph(
    *,
    settings: Settings,
    trace_hook: TraceHook | None = None,
    checkpointer: Any | None = None,
):
    workflow = StateGraph(StewardState)
    steps = _build_ingest_steps(settings=settings, trace_hook=trace_hook)
    for current_step in steps:
        workflow.add_node(current_step.name, current_step.node)
    workflow.add_edge(START, steps[0].name)
    for current_step, next_step in zip(steps, steps[1:]):
        workflow.add_edge(current_step.name, next_step.name)
    workflow.add_edge(steps[-1].name, END)
    return workflow.compile(checkpointer=checkpointer)


def _resolve_last_completed_node(state: StewardState) -> str | None:
    trace_events = state.get("trace_events", [])
    if not trace_events:
        return None
    return trace_events[-1]["node_name"]


def _build_ingest_steps(
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> list[GraphStep]:
    return [
        GraphStep(
            name="prepare_ingest",
            node=lambda state: _prepare_ingest_node(state, settings=settings, trace_hook=trace_hook),
        ),
        GraphStep(
            name="execute_ingest",
            node=lambda state: _execute_ingest_node(state, settings=settings, trace_hook=trace_hook),
        ),
        GraphStep(
            name="finalize_ingest",
            node=lambda state: _finalize_ingest_node(state, trace_hook=trace_hook),
        ),
    ]


def _prepare_ingest_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    scoped_note_paths = [Path(note_path) for note_path in state.get("note_paths", [])]
    ingest_scope = "scoped_notes" if scoped_note_paths else "full_vault"
    trace_events = append_trace_event(
        state,
        graph_name="ingest_graph",
        node_name="prepare_ingest",
        event_type="entered",
        details={
            "ingest_scope": ingest_scope,
            "requested_note_count": len(scoped_note_paths),
            "requested_note_paths": [str(note_path) for note_path in scoped_note_paths],
            "vault_dir_name": settings.sample_vault_dir.name,
            "db_file_name": settings.index_db_path.name,
            "request_metadata_keys": sorted(dict(state.get("request_metadata", {})).keys()),
        },
        trace_hook=trace_hook,
    )
    return {
        "approval_required": False,
        "trace_events": trace_events,
        "transient_prompt_context": {
            "graph_name": "ingest_graph",
            "thread_id": state["thread_id"],
            "run_id": state["run_id"],
        },
    }


def _execute_ingest_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    scoped_note_paths = [Path(note_path) for note_path in state.get("note_paths", [])]
    # 这里仍保持“ingest 作为一个业务节点”而不是继续拆细，是为了守住 TASK-026 的边界：
    # 只把 scoped note 入口打通，不顺手扩成 proposal、partial checkpoint 或更复杂的增量调度。
    stats = ingest_vault(
        vault_path=settings.sample_vault_dir,
        db_path=settings.index_db_path,
        note_paths=scoped_note_paths,
        settings=settings,
    )
    ingest_scope = "scoped_notes" if scoped_note_paths else "full_vault"
    ingest_result = IngestWorkflowResult(
        vault_path=stats.vault_path,
        db_path=stats.db_path,
        scanned_notes=stats.scanned_notes,
        created_notes=stats.created_notes,
        updated_notes=stats.updated_notes,
        current_chunk_count=stats.current_chunk_count,
        replaced_chunk_count=stats.replaced_chunk_count,
    )
    trace_events = append_trace_event(
        state,
        graph_name="ingest_graph",
        node_name="execute_ingest",
        event_type="completed",
        details={
            "ingest_scope": ingest_scope,
            "requested_note_count": len(scoped_note_paths),
            "requested_note_paths": [str(note_path) for note_path in scoped_note_paths],
            "vault_dir_name": Path(stats.vault_path).name,
            "db_file_name": Path(stats.db_path).name,
            "scanned_notes": stats.scanned_notes,
            "created_notes": stats.created_notes,
            "updated_notes": stats.updated_notes,
            "current_chunk_count": stats.current_chunk_count,
            "replaced_chunk_count": stats.replaced_chunk_count,
        },
        trace_hook=trace_hook,
    )
    return {
        "ingest_result": ingest_result,
        "trace_events": trace_events,
    }


def _finalize_ingest_node(
    state: StewardState,
    *,
    trace_hook: TraceHook | None,
) -> StewardState:
    ingest_result = state.get("ingest_result")
    trace_events = append_trace_event(
        state,
        graph_name="ingest_graph",
        node_name="finalize_ingest",
        event_type="completed",
        details={
            "result_present": ingest_result is not None,
            "trace_event_count_before_finalize": len(state.get("trace_events", [])),
        },
        trace_hook=trace_hook,
    )
    return {
        "trace_events": trace_events,
    }


def _invoke_ingest_graph_with_approval(
    *,
    initial_state: StewardState,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> CheckpointedGraphRun:
    current_state = cast(StewardState, dict(initial_state))
    for node in (
        lambda state: _prepare_ingest_node(state, settings=settings, trace_hook=trace_hook),
        lambda state: _execute_ingest_node(state, settings=settings, trace_hook=trace_hook),
    ):
        updates = node(current_state)
        if updates:
            current_state.update(updates)

    ingest_result = cast(IngestWorkflowResult | None, current_state.get("ingest_result"))
    if ingest_result is None:
        raise RuntimeError("ingest_graph approval path did not produce ingest_result.")

    build_result = build_scoped_ingest_approval_proposal(
        thread_id=cast(str, current_state["thread_id"]),
        note_paths=cast(list[str], current_state.get("note_paths", [])),
        db_path=settings.index_db_path,
        settings=settings,
        provider_preference=cast(str | None, current_state.get("provider_preference")),
    )
    current_state.update(
        {
            "note_meta": build_result.note_meta,
            "analysis_result": build_result.analysis_result,
            "analysis_issues": build_result.analysis_issues,
        }
    )

    if build_result.proposal is None:
        skipped_updates = _record_ingest_proposal_skipped_node(
            current_state,
            skip_reason=build_result.skip_reason or "proposal_not_generated",
            trace_hook=trace_hook,
        )
        if skipped_updates:
            current_state.update(skipped_updates)
        finalize_updates = _finalize_ingest_node(current_state, trace_hook=trace_hook)
        if finalize_updates:
            current_state.update(finalize_updates)
        save_graph_checkpoint(
            settings.index_db_path,
            graph_name="ingest_graph",
            checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
            last_completed_node="finalize_ingest",
            next_node_name=None,
            state=current_state,
            settings=settings,
        )
        return CheckpointedGraphRun(
            state=current_state,
            checkpoint_used=False,
            resumed_from_node=None,
            resumed_from_status=None,
        )

    proposal = build_result.proposal
    proposal_updates = _build_ingest_proposal_node(
        current_state,
        proposal=proposal,
        trace_hook=trace_hook,
    )
    if proposal_updates:
        current_state.update(proposal_updates)

    normalized_db_path = initialize_index_db(
        settings.index_db_path,
        settings=settings,
    )
    connection = connect_sqlite(normalized_db_path)
    try:
        # proposal 与 waiting checkpoint 必须原子落盘，否则插件可能先拿到 proposal，
        # 但 thread 还停在 completed/in_progress，后续 pending inbox 与 resume 会直接失配。
        with connection:
            save_proposal_record(
                connection,
                thread_id=cast(str, current_state["thread_id"]),
                proposal=proposal,
                approval_required=True,
                settings=settings,
                run_id=cast(str, current_state["run_id"]),
                idempotency_key=f"ingest_waiting:{current_state['thread_id']}",
            )
            save_graph_checkpoint_record(
                connection,
                graph_name="ingest_graph",
                checkpoint_status=WorkflowCheckpointStatus.WAITING_FOR_APPROVAL,
                last_completed_node="build_ingest_proposal",
                next_node_name="human_approval",
                state=current_state,
            )
    finally:
        connection.close()

    return CheckpointedGraphRun(
        state=current_state,
        checkpoint_used=False,
        resumed_from_node=None,
        resumed_from_status=None,
    )


def _build_ingest_proposal_node(
    state: StewardState,
    *,
    proposal: Proposal,
    trace_hook: TraceHook | None,
) -> StewardState:
    trace_events = append_trace_event(
        state,
        graph_name="ingest_graph",
        node_name="build_ingest_proposal",
        event_type="completed",
        details={
            "proposal_id": proposal.proposal_id,
            "target_note_path": proposal.target_note_path,
            "patch_op_count": len(proposal.patch_ops),
            "evidence_count": len(proposal.evidence),
            "analysis_issue_count": len(state.get("analysis_issues", [])),
            "related_candidate_count": len(
                cast(
                    IngestAnalysisResult | None,
                    state.get("analysis_result"),
                ).related_candidates
            )
            if state.get("analysis_result") is not None
            else 0,
        },
        trace_hook=trace_hook,
    )
    trace_events = append_trace_event(
        {
            **state,
            "trace_events": trace_events,
        },
        graph_name="ingest_graph",
        node_name="human_approval",
        event_type="waiting",
        details={
            "proposal_id": proposal.proposal_id,
            "approval_required": True,
        },
        trace_hook=trace_hook,
    )
    return {
        "proposal": proposal,
        "approval_required": True,
        "approval_decision": None,
        "patch_plan": [patch_op.model_dump(mode="json") for patch_op in proposal.patch_ops],
        "before_hash": proposal.safety_checks.before_hash,
        "trace_events": trace_events,
    }


def _record_ingest_proposal_skipped_node(
    state: StewardState,
    *,
    skip_reason: str,
    trace_hook: TraceHook | None,
) -> StewardState:
    note_meta = cast(dict[str, object], state.get("note_meta", {}))
    trace_events = append_trace_event(
        state,
        graph_name="ingest_graph",
        node_name="build_ingest_proposal",
        event_type="skipped",
        details={
            "skip_reason": skip_reason,
            "requested_note_count": len(state.get("note_paths", [])),
            "analysis_issue_count": len(state.get("analysis_issues", [])),
            "related_candidate_count": len(
                cast(
                    IngestAnalysisResult | None,
                    state.get("analysis_result"),
                ).related_candidates
            )
            if state.get("analysis_result") is not None
            else 0,
            "target_note_path": note_meta.get("target_note_path", ""),
        },
        trace_hook=trace_hook,
    )
    return {
        "approval_required": False,
        "trace_events": trace_events,
    }


def _reject_waiting_ingest_resume(
    *,
    settings: Settings,
    request: WorkflowInvokeRequest,
    thread_id: str,
) -> None:
    if not request.resume_from_checkpoint:
        return

    checkpoint = load_graph_checkpoint(
        settings.index_db_path,
        thread_id=thread_id,
        graph_name="ingest_graph",
    )
    if checkpoint is None:
        return
    if checkpoint.checkpoint_status == WorkflowCheckpointStatus.WAITING_FOR_APPROVAL:
        raise ValueError(
            "This INGEST_STEWARD thread is waiting for approval; use /workflows/resume instead of resume_from_checkpoint."
        )


def _should_emit_ingest_approval_proposal(
    request: WorkflowInvokeRequest,
) -> bool:
    approval_mode = request.metadata.get("approval_mode")
    return request.require_approval and approval_mode == "proposal"
