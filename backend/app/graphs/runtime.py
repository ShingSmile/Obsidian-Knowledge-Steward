from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Callable, TypedDict, cast

from app.config import Settings
from app.contracts.workflow import (
    ApprovalDecision,
    AskCitation,
    AskResultMode,
    AskWorkflowResult,
    DigestSourceNote,
    DigestWorkflowResult,
    GuardrailAction,
    IngestAnalysisFinding,
    IngestAnalysisResult,
    IngestWorkflowResult,
    PatchOp,
    PostWritebackSyncResult,
    Proposal,
    ProposalEvidence,
    RetrievalMetadataFilter,
    RetrievedChunkCandidate,
    RiskLevel,
    SafetyChecks,
    WorkflowAction,
    WorkflowInvokeRequest,
    WritebackResult,
)
from app.graphs.checkpoint import (
    WorkflowCheckpointStatus,
    hydrate_business_checkpoint_state,
    load_graph_checkpoint,
    save_graph_checkpoint,
)
from app.graphs.state import StewardState
from app.indexing.store import initialize_index_db
from app.observability import (
    build_jsonl_trace_hook,
    build_sqlite_trace_hook,
    compose_trace_hooks,
)
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph


class RuntimeTraceEvent(TypedDict):
    graph_name: str
    node_name: str
    event_type: str
    thread_id: str
    run_id: str
    action_type: str
    timestamp: str
    details: dict[str, object]


TraceHook = Callable[[RuntimeTraceEvent], None]
GraphNode = Callable[[StewardState], dict[str, object]]

CHECKPOINT_MSGPACK_ALLOWLIST = (
    ApprovalDecision,
    AskCitation,
    AskResultMode,
    AskWorkflowResult,
    DigestSourceNote,
    DigestWorkflowResult,
    GuardrailAction,
    IngestAnalysisFinding,
    IngestAnalysisResult,
    IngestWorkflowResult,
    PatchOp,
    PostWritebackSyncResult,
    Proposal,
    ProposalEvidence,
    RetrievalMetadataFilter,
    RetrievedChunkCandidate,
    RiskLevel,
    SafetyChecks,
    WorkflowAction,
    WritebackResult,
)


@dataclass(frozen=True)
class GraphStep:
    name: str
    node: GraphNode


@dataclass(frozen=True)
class CheckpointedGraphRun:
    state: StewardState
    checkpoint_used: bool
    resumed_from_node: str | None
    resumed_from_status: WorkflowCheckpointStatus | None


@dataclass(frozen=True)
class WorkflowGraphExecution:
    graph_name: str
    action_type: WorkflowAction
    thread_id: str
    run_id: str
    state: StewardState
    trace_events: list[RuntimeTraceEvent]
    checkpoint_used: bool
    resumed_from_node: str | None


def build_base_workflow_state(
    request: WorkflowInvokeRequest,
    *,
    thread_id: str,
    run_id: str,
) -> StewardState:
    """Build the shared invoke-state envelope before each workflow adds its own fields."""

    return {
        "thread_id": thread_id,
        "run_id": run_id,
        "action_type": request.action_type,
        "note_path": request.note_path,
        "note_paths": list(request.note_paths),
        "user_query": request.user_query,
        "provider_preference": request.provider_preference,
        "retrieval_filter": request.retrieval_filter,
        "request_metadata": dict(request.metadata),
        "approval_required": False,
        "trace_events": [],
        "errors": [],
        "transient_prompt_context": {},
    }


def build_workflow_runtime_trace_hook(
    settings: Settings,
    trace_hook: TraceHook | None,
) -> TraceHook | None:
    # ask / ingest / digest 当前共用同一套 trace sink，是为了先统一 runtime 观测协议；
    # `ask_runtime_trace_path` 这个名字只是历史残留，不应再让 graph 各自复制一遍组装逻辑。
    return compose_trace_hooks(
        build_jsonl_trace_hook(settings.ask_runtime_trace_path),
        build_sqlite_trace_hook(settings.index_db_path),
        trace_hook,
    )


def build_workflow_graph_execution(
    *,
    graph_name: str,
    action_type: WorkflowAction,
    final_state: StewardState,
    checkpoint_run: CheckpointedGraphRun,
) -> WorkflowGraphExecution:
    return WorkflowGraphExecution(
        graph_name=graph_name,
        action_type=action_type,
        thread_id=cast(str, final_state["thread_id"]),
        run_id=cast(str, final_state["run_id"]),
        state=final_state,
        trace_events=cast(list[RuntimeTraceEvent], final_state.get("trace_events", [])),
        checkpoint_used=checkpoint_run.checkpoint_used,
        resumed_from_node=checkpoint_run.resumed_from_node,
    )


@contextmanager
def open_sqlite_checkpointer(db_path: Path) -> Iterator[SqliteSaver]:
    normalized_db_path = initialize_index_db(db_path)
    connection = sqlite3.connect(str(normalized_db_path), check_same_thread=False)
    try:
        checkpointer = SqliteSaver(
            connection,
            serde=JsonPlusSerializer(
                allowed_msgpack_modules=CHECKPOINT_MSGPACK_ALLOWLIST,
            ),
        )
        yield checkpointer
    finally:
        connection.close()


def build_graph_run_config(
    *,
    thread_id: str,
    checkpoint_id: str | None = None,
) -> dict[str, dict[str, str]]:
    configurable = {"thread_id": thread_id}
    if checkpoint_id is not None:
        configurable["checkpoint_id"] = checkpoint_id
    return {"configurable": configurable}


def invoke_compiled_state_graph(
    *,
    graph: Any,
    state: StewardState,
    thread_id: str,
) -> StewardState:
    return cast(
        StewardState,
        graph.invoke(
            state,
            config=build_graph_run_config(thread_id=thread_id),
        ),
    )


def load_compiled_graph_state(
    *,
    graph: Any,
    thread_id: str,
) -> StewardState | None:
    state_snapshot = graph.get_state(build_graph_run_config(thread_id=thread_id))
    snapshot_values = getattr(state_snapshot, "values", None)
    if not snapshot_values:
        return None
    return cast(StewardState, dict(snapshot_values))


def append_trace_event(
    state: StewardState,
    *,
    graph_name: str,
    node_name: str,
    event_type: str,
    details: dict[str, object],
    trace_hook: TraceHook | None,
) -> list[RuntimeTraceEvent]:
    event: RuntimeTraceEvent = {
        "graph_name": graph_name,
        "node_name": node_name,
        "event_type": event_type,
        "thread_id": state["thread_id"],
        "run_id": state["run_id"],
        "action_type": state["action_type"].value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }
    trace_events = list(cast(list[RuntimeTraceEvent], state.get("trace_events", [])))
    trace_events.append(event)

    if trace_hook is not None:
        try:
            # tracing 是观测通道，不应该反向拖垮主链路。
            trace_hook(event)
        except Exception:
            pass

    return trace_events


def invoke_checkpointed_compiled_graph(
    *,
    graph_name: str,
    graph: Any,
    initial_state: StewardState,
    checkpoint_db_path: Path,
    resume_from_checkpoint: bool,
    trace_hook: TraceHook | None,
    required_terminal_fields: tuple[str, ...] = (),
    resume_match_fields: tuple[str, ...] = (),
) -> CheckpointedGraphRun:
    current_state = cast(StewardState, dict(initial_state))
    checkpoint_used = False
    resumed_from_node: str | None = None
    resumed_from_status: WorkflowCheckpointStatus | None = None

    if resume_from_checkpoint:
        checkpoint = _load_checkpoint_safely(
            db_path=checkpoint_db_path,
            graph_name=graph_name,
            state=current_state,
        )
        matches_resume_fields, mismatched_resume_fields = _checkpoint_matches_resume_fields(
            current_state=current_state,
            checkpoint_state=checkpoint.state if checkpoint is not None else None,
            resume_match_fields=resume_match_fields,
        )
        if (
            checkpoint is not None
            and checkpoint.action_type == current_state["action_type"]
            and matches_resume_fields
        ):
            persisted_state = _load_compiled_graph_state_safely(
                graph=graph,
                state=current_state,
            )
            resumed_state = hydrate_business_checkpoint_state(
                current_state=current_state,
                restored_state=persisted_state or checkpoint.state,
            )
            trace_events = append_trace_event(
                resumed_state,
                graph_name=graph_name,
                node_name="checkpoint_resume",
                event_type="hit",
                details={
                    "checkpoint_status": checkpoint.checkpoint_status.value,
                    "last_completed_node": checkpoint.last_completed_node or "",
                    "next_node_name": checkpoint.next_node_name or "",
                    "checkpoint_run_id": checkpoint.last_run_id,
                },
                trace_hook=trace_hook,
            )
            resumed_state["trace_events"] = trace_events

            if (
                checkpoint.checkpoint_status == WorkflowCheckpointStatus.COMPLETED
                and _has_required_terminal_fields(resumed_state, required_terminal_fields)
            ):
                return CheckpointedGraphRun(
                    state=resumed_state,
                    checkpoint_used=True,
                    resumed_from_node=None,
                    resumed_from_status=checkpoint.checkpoint_status,
                )

            current_state = resumed_state
            checkpoint_used = True
            resumed_from_status = checkpoint.checkpoint_status
            resumed_from_node = checkpoint.next_node_name or checkpoint.last_completed_node
        else:
            mismatch_details: dict[str, object] = {
                "resume_requested": True,
            }
            if checkpoint is not None:
                mismatch_details["checkpoint_found"] = True
                mismatch_details["checkpoint_action_type"] = checkpoint.action_type.value
                if mismatched_resume_fields:
                    mismatch_details["mismatched_resume_fields"] = mismatched_resume_fields
            else:
                mismatch_details["checkpoint_found"] = False
            trace_events = append_trace_event(
                current_state,
                graph_name=graph_name,
                node_name="checkpoint_resume",
                event_type="miss",
                details=mismatch_details,
                trace_hook=trace_hook,
            )
            current_state["trace_events"] = trace_events

    final_state = invoke_compiled_state_graph(
        graph=graph,
        state=current_state,
        thread_id=cast(str, current_state["thread_id"]),
    )
    return CheckpointedGraphRun(
        state=final_state,
        checkpoint_used=checkpoint_used,
        resumed_from_node=resumed_from_node,
        resumed_from_status=resumed_from_status,
    )


def _load_checkpoint_safely(
    *,
    db_path: Path,
    graph_name: str,
    state: StewardState,
):
    try:
        return load_graph_checkpoint(
            db_path,
            thread_id=state["thread_id"],
            graph_name=graph_name,
        )
    except Exception as exc:
        state["errors"] = _append_graph_error(
            state,
            error_source="checkpoint_load",
            message=f"Failed to load checkpoint: {exc.__class__.__name__}: {exc}",
        )
        return None


def _save_checkpoint_safely(
    *,
    db_path: Path,
    graph_name: str,
    checkpoint_status: WorkflowCheckpointStatus,
    last_completed_node: str | None,
    next_node_name: str | None,
    state: StewardState,
) -> None:
    try:
        save_graph_checkpoint(
            db_path,
            graph_name=graph_name,
            checkpoint_status=checkpoint_status,
            last_completed_node=last_completed_node,
            next_node_name=next_node_name,
            state=state,
        )
    except Exception as exc:
        # checkpoint 是恢复增强，不应该让单个写盘失败掐断主链路。
        state["errors"] = _append_graph_error(
            state,
            error_source="checkpoint_save",
            message=f"Failed to save checkpoint: {exc.__class__.__name__}: {exc}",
        )


def save_business_checkpoint_safely(
    *,
    db_path: Path,
    graph_name: str,
    checkpoint_status: WorkflowCheckpointStatus,
    last_completed_node: str | None,
    next_node_name: str | None,
    state: StewardState,
) -> None:
    _save_checkpoint_safely(
        db_path=db_path,
        graph_name=graph_name,
        checkpoint_status=checkpoint_status,
        last_completed_node=last_completed_node,
        next_node_name=next_node_name,
        state=state,
    )

def _load_compiled_graph_state_safely(
    *,
    graph: Any,
    state: StewardState,
) -> StewardState | None:
    try:
        return load_compiled_graph_state(
            graph=graph,
            thread_id=cast(str, state["thread_id"]),
        )
    except Exception as exc:
        state["errors"] = _append_graph_error(
            state,
            error_source="checkpoint_load",
            message=f"Failed to load compiled graph state: {exc.__class__.__name__}: {exc}",
        )
        return None


def _has_required_terminal_fields(
    state: StewardState,
    required_terminal_fields: tuple[str, ...],
) -> bool:
    return all(state.get(field_name) is not None for field_name in required_terminal_fields)


def _checkpoint_matches_resume_fields(
    *,
    current_state: StewardState,
    checkpoint_state: StewardState | None,
    resume_match_fields: tuple[str, ...],
) -> tuple[bool, list[str]]:
    if checkpoint_state is None or not resume_match_fields:
        return True, []

    mismatched_fields: list[str] = []
    for field_name in resume_match_fields:
        if checkpoint_state.get(field_name) != current_state.get(field_name):
            mismatched_fields.append(field_name)

    return not mismatched_fields, mismatched_fields


def _append_graph_error(
    state: StewardState,
    *,
    error_source: str,
    message: str,
) -> list[dict[str, object]]:
    errors = list(cast(list[dict[str, object]], state.get("errors", [])))
    errors.append(
        {
            "source": error_source,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    return errors
