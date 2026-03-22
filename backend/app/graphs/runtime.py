from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypedDict, cast

from app.config import Settings
from app.contracts.workflow import WorkflowAction, WorkflowInvokeRequest
from app.graphs.checkpoint import (
    WorkflowCheckpointStatus,
    load_graph_checkpoint,
    save_graph_checkpoint,
)
from app.graphs.state import StewardState
from app.observability import (
    build_jsonl_trace_hook,
    build_sqlite_trace_hook,
    compose_trace_hooks,
)


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


try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    START = "__start__"
    END = "__end__"

    class _CompiledStateGraph:
        """Minimal linear runner used when LangGraph is not yet installed locally."""

        def __init__(
            self,
            *,
            nodes: dict[str, GraphNode],
            edges: dict[str, str],
        ) -> None:
            self._nodes = nodes
            self._edges = edges

        def invoke(self, state: StewardState) -> StewardState:
            current_state = dict(state)
            next_node = self._edges.get(START)
            while next_node and next_node != END:
                updates = self._nodes[next_node](cast(StewardState, current_state))
                if updates:
                    current_state.update(updates)
                next_node = self._edges.get(next_node)
            return cast(StewardState, current_state)

    class StateGraph:  # type: ignore[override]
        """Compatibility shim that preserves the minimal API used in this repository."""

        def __init__(self, _state_type: object) -> None:
            self._nodes: dict[str, GraphNode] = {}
            self._edges: dict[str, str] = {}

        def add_node(self, name: str, node: GraphNode) -> None:
            self._nodes[name] = node

        def add_edge(self, source: str, target: str) -> None:
            self._edges[source] = target

        def compile(self) -> _CompiledStateGraph:
            return _CompiledStateGraph(nodes=self._nodes, edges=self._edges)


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
    used_langgraph: bool
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
        used_langgraph=LANGGRAPH_AVAILABLE,
        checkpoint_used=checkpoint_run.checkpoint_used,
        resumed_from_node=checkpoint_run.resumed_from_node,
    )


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


def invoke_checkpointed_linear_graph(
    *,
    graph_name: str,
    steps: list[GraphStep],
    initial_state: StewardState,
    checkpoint_db_path: Path,
    resume_from_checkpoint: bool,
    trace_hook: TraceHook | None,
    required_terminal_fields: tuple[str, ...] = (),
    resume_match_fields: tuple[str, ...] = (),
) -> CheckpointedGraphRun:
    current_state = cast(StewardState, dict(initial_state))
    start_index = 0
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
            resumed_state = _hydrate_state_from_checkpoint(
                current_state=current_state,
                checkpoint_state=checkpoint.state,
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

            resume_index = _resolve_resume_index(
                steps=steps,
                next_node_name=checkpoint.next_node_name,
                last_completed_node=checkpoint.last_completed_node,
            )
            if (
                checkpoint.checkpoint_status == WorkflowCheckpointStatus.COMPLETED
                and _has_required_terminal_fields(resumed_state, required_terminal_fields)
            ):
                # 已完成 checkpoint 直接短路返回，避免 ask 重打模型、ingest 重跑整库。
                return CheckpointedGraphRun(
                    state=resumed_state,
                    checkpoint_used=True,
                    resumed_from_node=None,
                    resumed_from_status=checkpoint.checkpoint_status,
                )

            if checkpoint.checkpoint_status == WorkflowCheckpointStatus.COMPLETED:
                current_state = _build_fresh_state_after_invalid_checkpoint(
                    initial_state=initial_state,
                    previous_state=resumed_state,
                    message=(
                        "Completed checkpoint did not contain the required terminal state; "
                        "starting a fresh execution."
                    ),
                )
                start_index = 0
                checkpoint_used = False
                resumed_from_status = None
                resumed_from_node = None
            else:
                current_state = resumed_state
                start_index = resume_index
                checkpoint_used = True
                resumed_from_status = checkpoint.checkpoint_status
                resumed_from_node = steps[resume_index].name if resume_index < len(steps) else None

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

    for step_index in range(start_index, len(steps)):
        step = steps[step_index]
        try:
            updates = step.node(current_state)
        except Exception as exc:
            current_state["errors"] = _append_graph_error(
                current_state,
                error_source="checkpoint_runtime",
                message=(
                    f"{graph_name}.{step.name} raised {exc.__class__.__name__}: {exc}"
                ),
            )
            _save_checkpoint_safely(
                db_path=checkpoint_db_path,
                graph_name=graph_name,
                checkpoint_status=WorkflowCheckpointStatus.FAILED,
                last_completed_node=steps[step_index - 1].name if step_index > 0 else None,
                next_node_name=step.name,
                state=current_state,
            )
            raise

        if updates:
            current_state.update(updates)

        next_node_name = steps[step_index + 1].name if step_index + 1 < len(steps) else None
        checkpoint_status = (
            WorkflowCheckpointStatus.COMPLETED
            if next_node_name is None
            else WorkflowCheckpointStatus.IN_PROGRESS
        )
        _save_checkpoint_safely(
            db_path=checkpoint_db_path,
            graph_name=graph_name,
            checkpoint_status=checkpoint_status,
            last_completed_node=step.name,
            next_node_name=next_node_name,
            state=current_state,
        )

    return CheckpointedGraphRun(
        state=current_state,
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


def _hydrate_state_from_checkpoint(
    *,
    current_state: StewardState,
    checkpoint_state: StewardState,
) -> StewardState:
    resumed_state = cast(StewardState, dict(checkpoint_state))
    # 恢复的是“业务状态”，不是把上一次 run 原封不动复制回来；
    # 当前 run_id 和本次 trace 必须重新生成，否则一次恢复会和历史执行混成同一轮。
    resumed_state["thread_id"] = current_state["thread_id"]
    resumed_state["run_id"] = current_state["run_id"]
    resumed_state["action_type"] = current_state["action_type"]
    resumed_state["trace_events"] = []
    resumed_state["transient_prompt_context"] = {}
    return resumed_state


def _resolve_resume_index(
    *,
    steps: list[GraphStep],
    next_node_name: str | None,
    last_completed_node: str | None,
) -> int:
    if next_node_name:
        for index, step in enumerate(steps):
            if step.name == next_node_name:
                return index
    if last_completed_node:
        for index, step in enumerate(steps):
            if step.name == last_completed_node:
                return min(index + 1, len(steps))
    return 0


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


def _build_fresh_state_after_invalid_checkpoint(
    *,
    initial_state: StewardState,
    previous_state: StewardState,
    message: str,
) -> StewardState:
    fresh_state = cast(StewardState, dict(initial_state))
    fresh_state["trace_events"] = list(
        cast(list[RuntimeTraceEvent], previous_state.get("trace_events", []))
    )
    fresh_state["errors"] = list(cast(list[dict[str, object]], previous_state.get("errors", [])))
    fresh_state["errors"] = _append_graph_error(
        fresh_state,
        error_source="checkpoint_validation",
        message=message,
    )
    return fresh_state
