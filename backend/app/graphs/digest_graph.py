from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from app.config import Settings
from app.contracts.workflow import DigestWorkflowResult, Proposal, WorkflowInvokeRequest
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
from app.indexing.store import connect_sqlite, initialize_index_db, save_proposal_record
from app.services.digest import build_digest_approval_proposal, run_minimal_digest


@dataclass(frozen=True)
class DigestGraphExecution(WorkflowGraphExecution):
    digest_result: DigestWorkflowResult
    proposal: Proposal | None
    approval_required: bool


def invoke_digest_graph(
    request: WorkflowInvokeRequest,
    *,
    settings: Settings,
    thread_id: str,
    run_id: str,
    trace_hook: TraceHook | None = None,
) -> DigestGraphExecution:
    initial_state = build_initial_digest_state(
        request=request,
        thread_id=thread_id,
        run_id=run_id,
    )
    runtime_trace_hook = build_workflow_runtime_trace_hook(settings, trace_hook)
    _reject_waiting_digest_resume(
        settings=settings,
        request=request,
        thread_id=thread_id,
    )

    if _should_emit_digest_approval_proposal(request) and not request.resume_from_checkpoint:
        execution = _invoke_digest_graph_with_approval(
            initial_state=initial_state,
            settings=settings,
            trace_hook=runtime_trace_hook,
        )
    else:
        with open_sqlite_checkpointer(settings.index_db_path) as checkpointer:
            graph = build_digest_graph(
                settings=settings,
                trace_hook=runtime_trace_hook,
                checkpointer=checkpointer,
            )
            execution = invoke_checkpointed_compiled_graph(
                graph_name="digest_graph",
                graph=graph,
                initial_state=initial_state,
                checkpoint_db_path=settings.index_db_path,
                resume_from_checkpoint=request.resume_from_checkpoint,
                trace_hook=runtime_trace_hook,
                required_terminal_fields=("digest_result",),
            )
    final_state = execution.state

    digest_result = final_state.get("digest_result")
    if digest_result is None:
        raise RuntimeError("digest_graph completed without producing digest_result.")

    if (
        not _should_emit_digest_approval_proposal(request)
        and not (
            execution.checkpoint_used
            and execution.resumed_from_status == WorkflowCheckpointStatus.COMPLETED
        )
    ):
        save_business_checkpoint_safely(
            db_path=settings.index_db_path,
            graph_name="digest_graph",
            checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
            last_completed_node=_resolve_last_completed_node(final_state),
            next_node_name=None,
            state=final_state,
        )

    shared_execution = build_workflow_graph_execution(
        graph_name="digest_graph",
        action_type=request.action_type,
        final_state=final_state,
        checkpoint_run=execution,
    )
    return DigestGraphExecution(
        graph_name=shared_execution.graph_name,
        action_type=shared_execution.action_type,
        thread_id=shared_execution.thread_id,
        run_id=shared_execution.run_id,
        state=shared_execution.state,
        trace_events=shared_execution.trace_events,
        checkpoint_used=shared_execution.checkpoint_used,
        resumed_from_node=shared_execution.resumed_from_node,
        digest_result=digest_result,
        proposal=cast(Proposal | None, final_state.get("proposal")),
        approval_required=bool(final_state.get("approval_required", False)),
    )


def build_initial_digest_state(
    *,
    request: WorkflowInvokeRequest,
    thread_id: str,
    run_id: str,
) -> StewardState:
    if request.note_path or request.note_paths:
        raise ValueError(
            "DAILY_DIGEST currently summarizes the indexed vault as a whole; "
            "note_path/note_paths scoping is not implemented yet."
        )

    return build_base_workflow_state(
        request,
        thread_id=thread_id,
        run_id=run_id,
    )


def build_digest_graph(
    *,
    settings: Settings,
    trace_hook: TraceHook | None = None,
    checkpointer: Any | None = None,
):
    workflow = StateGraph(StewardState)
    steps = _build_digest_steps(settings=settings, trace_hook=trace_hook)
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


def _build_digest_steps(
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> list[GraphStep]:
    return [
        GraphStep(
            name="prepare_digest",
            node=lambda state: _prepare_digest_node(state, settings=settings, trace_hook=trace_hook),
        ),
        GraphStep(
            name="build_digest",
            node=lambda state: _build_digest_node(state, settings=settings, trace_hook=trace_hook),
        ),
        GraphStep(
            name="finalize_digest",
            node=lambda state: _finalize_digest_node(state, trace_hook=trace_hook),
        ),
    ]


def _prepare_digest_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    trace_events = append_trace_event(
        state,
        graph_name="digest_graph",
        node_name="prepare_digest",
        event_type="entered",
        details={
            "digest_scope": "indexed_vault",
            "db_file_name": settings.index_db_path.name,
            "request_metadata_keys": sorted(dict(state.get("request_metadata", {})).keys()),
        },
        trace_hook=trace_hook,
    )
    return {
        "approval_required": False,
        "trace_events": trace_events,
        "transient_prompt_context": {
            "graph_name": "digest_graph",
            "thread_id": state["thread_id"],
            "run_id": state["run_id"],
        },
    }


def _build_digest_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    # 首版先输出“可验证的模板化 digest”，是为了把 graph 边界、fallback 和 source_notes contract
    # 先钉死，而不是在 digest 主线还没稳定前就把质量完全绑到外部模型可用性上。
    digest_result = run_minimal_digest(settings=settings)
    trace_events = append_trace_event(
        state,
        graph_name="digest_graph",
        node_name="build_digest",
        event_type="completed",
        details={
            "source_note_count": digest_result.source_note_count,
            "fallback_used": digest_result.fallback_used,
            "fallback_reason": digest_result.fallback_reason or "",
        },
        trace_hook=trace_hook,
    )
    return {
        "digest_result": digest_result,
        "trace_events": trace_events,
    }


def _finalize_digest_node(
    state: StewardState,
    *,
    trace_hook: TraceHook | None,
) -> StewardState:
    digest_result = state.get("digest_result")
    trace_events = append_trace_event(
        state,
        graph_name="digest_graph",
        node_name="finalize_digest",
        event_type="completed",
        details={
            "result_present": digest_result is not None,
            "trace_event_count_before_finalize": len(state.get("trace_events", [])),
        },
        trace_hook=trace_hook,
    )
    return {
        "trace_events": trace_events,
    }


def _invoke_digest_graph_with_approval(
    *,
    initial_state: StewardState,
    settings: Settings,
    trace_hook: TraceHook | None,
):
    current_state = cast(StewardState, dict(initial_state))
    for node in (
        lambda state: _prepare_digest_node(state, settings=settings, trace_hook=trace_hook),
        lambda state: _build_digest_node(state, settings=settings, trace_hook=trace_hook),
    ):
        updates = node(current_state)
        if updates:
            current_state.update(updates)

    digest_result = cast(DigestWorkflowResult | None, current_state.get("digest_result"))
    if digest_result is None:
        raise RuntimeError("digest_graph approval path did not produce digest_result.")

    proposal = build_digest_approval_proposal(
        settings=settings,
        thread_id=cast(str, current_state["thread_id"]),
        digest_result=digest_result,
    )
    if proposal is None:
        finalize_updates = _finalize_digest_node(current_state, trace_hook=trace_hook)
        if finalize_updates:
            current_state.update(finalize_updates)
        save_graph_checkpoint(
            settings.index_db_path,
            graph_name="digest_graph",
            checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
            last_completed_node="finalize_digest",
            next_node_name=None,
            state=current_state,
        )
        return CheckpointedGraphRun(
            state=current_state,
            checkpoint_used=False,
            resumed_from_node=None,
            resumed_from_status=None,
        )

    proposal_updates = _build_digest_proposal_node(
        current_state,
        proposal=proposal,
        trace_hook=trace_hook,
    )
    if proposal_updates:
        current_state.update(proposal_updates)

    normalized_db_path = initialize_index_db(settings.index_db_path)
    connection = connect_sqlite(normalized_db_path)
    try:
        # proposal 与 waiting checkpoint 必须原子落盘，否则插件可能拿到 proposal_id，
        # 但 thread 状态还没进入 waiting_for_approval，后续 resume 会直接失配。
        with connection:
            save_proposal_record(
                connection,
                thread_id=cast(str, current_state["thread_id"]),
                proposal=proposal,
                approval_required=True,
                run_id=cast(str, current_state["run_id"]),
                idempotency_key=f"digest_waiting:{current_state['thread_id']}",
            )
            save_graph_checkpoint_record(
                connection,
                graph_name="digest_graph",
                checkpoint_status=WorkflowCheckpointStatus.WAITING_FOR_APPROVAL,
                last_completed_node="build_digest_proposal",
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


def _build_digest_proposal_node(
    state: StewardState,
    *,
    proposal: Proposal,
    trace_hook: TraceHook | None,
) -> StewardState:
    trace_events = append_trace_event(
        state,
        graph_name="digest_graph",
        node_name="build_digest_proposal",
        event_type="completed",
        details={
            "proposal_id": proposal.proposal_id,
            "target_note_path": proposal.target_note_path,
            "patch_op_count": len(proposal.patch_ops),
            "evidence_count": len(proposal.evidence),
        },
        trace_hook=trace_hook,
    )
    trace_events = append_trace_event(
        {
            **state,
            "trace_events": trace_events,
        },
        graph_name="digest_graph",
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


def _reject_waiting_digest_resume(
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
        graph_name="digest_graph",
    )
    if checkpoint is None:
        return
    if checkpoint.checkpoint_status == WorkflowCheckpointStatus.WAITING_FOR_APPROVAL:
        raise ValueError(
            "This DAILY_DIGEST thread is waiting for approval; use /workflows/resume instead of resume_from_checkpoint."
        )


def _should_emit_digest_approval_proposal(
    request: WorkflowInvokeRequest,
) -> bool:
    approval_mode = request.metadata.get("approval_mode")
    return request.require_approval and approval_mode == "proposal"
