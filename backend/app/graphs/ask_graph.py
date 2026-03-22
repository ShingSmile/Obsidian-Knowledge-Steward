from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.contracts.workflow import (
    AskWorkflowResult,
    RetrievalMetadataFilter,
    WorkflowInvokeRequest,
)
from app.graphs.runtime import (
    END,
    START,
    GraphStep,
    StateGraph,
    TraceHook,
    append_trace_event,
    build_base_workflow_state,
    build_workflow_graph_execution,
    build_workflow_runtime_trace_hook,
    invoke_checkpointed_linear_graph,
    WorkflowGraphExecution,
)
from app.graphs.state import StewardState
from app.services.ask import run_minimal_ask


@dataclass(frozen=True)
class AskGraphExecution(WorkflowGraphExecution):
    ask_result: AskWorkflowResult


def invoke_ask_graph(
    request: WorkflowInvokeRequest,
    *,
    settings: Settings,
    thread_id: str,
    run_id: str,
    trace_hook: TraceHook | None = None,
) -> AskGraphExecution:
    initial_state = build_initial_ask_state(
        request=request,
        thread_id=thread_id,
        run_id=run_id,
    )
    runtime_trace_hook = build_workflow_runtime_trace_hook(settings, trace_hook)
    execution = invoke_checkpointed_linear_graph(
        graph_name="ask_graph",
        steps=_build_ask_steps(settings=settings, trace_hook=runtime_trace_hook),
        initial_state=initial_state,
        checkpoint_db_path=settings.index_db_path,
        resume_from_checkpoint=request.resume_from_checkpoint,
        trace_hook=runtime_trace_hook,
        required_terminal_fields=("ask_result",),
    )
    final_state = execution.state

    ask_result = final_state.get("ask_result")
    if ask_result is None:
        raise RuntimeError("ask_graph completed without producing ask_result.")

    shared_execution = build_workflow_graph_execution(
        graph_name="ask_graph",
        action_type=request.action_type,
        final_state=final_state,
        checkpoint_run=execution,
    )
    return AskGraphExecution(
        graph_name=shared_execution.graph_name,
        action_type=shared_execution.action_type,
        thread_id=shared_execution.thread_id,
        run_id=shared_execution.run_id,
        state=shared_execution.state,
        trace_events=shared_execution.trace_events,
        used_langgraph=shared_execution.used_langgraph,
        checkpoint_used=shared_execution.checkpoint_used,
        resumed_from_node=shared_execution.resumed_from_node,
        ask_result=ask_result,
    )


def build_initial_ask_state(
    *,
    request: WorkflowInvokeRequest,
    thread_id: str,
    run_id: str,
) -> StewardState:
    return {
        **build_base_workflow_state(
            request,
            thread_id=thread_id,
            run_id=run_id,
        ),
        "retrieved_chunks": [],
    }


def build_ask_graph(
    *,
    settings: Settings,
    trace_hook: TraceHook | None = None,
):
    workflow = StateGraph(StewardState)
    steps = _build_ask_steps(settings=settings, trace_hook=trace_hook)
    for current_step in steps:
        workflow.add_node(current_step.name, current_step.node)
    workflow.add_edge(START, steps[0].name)
    for current_step, next_step in zip(steps, steps[1:]):
        workflow.add_edge(current_step.name, next_step.name)
    workflow.add_edge(steps[-1].name, END)
    return workflow.compile()


def _build_ask_steps(
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> list[GraphStep]:
    return [
        GraphStep(
            name="prepare_ask",
            node=lambda state: _prepare_ask_node(state, trace_hook=trace_hook),
        ),
        GraphStep(
            name="execute_ask",
            node=lambda state: _execute_ask_node(state, settings=settings, trace_hook=trace_hook),
        ),
        GraphStep(
            name="finalize_ask",
            node=lambda state: _finalize_ask_node(state, trace_hook=trace_hook),
        ),
    ]


def _prepare_ask_node(
    state: StewardState,
    *,
    trace_hook: TraceHook | None,
) -> StewardState:
    retrieval_filter = state.get("retrieval_filter", RetrievalMetadataFilter())
    trace_events = append_trace_event(
        state,
        graph_name="ask_graph",
        node_name="prepare_ask",
        event_type="entered",
        details={
            # 这里故意不把原始 query 全量写入 trace，避免在还没做脱敏策略前
            # 就把用户输入原文复制到观测数据里。
            "query_length": len((state.get("user_query") or "").strip()),
            "provider_preference": state.get("provider_preference") or "",
            "filter_summary": retrieval_filter.model_dump(
                exclude_defaults=True,
                exclude_none=True,
            ),
        },
        trace_hook=trace_hook,
    )
    return {
        "approval_required": False,
        "trace_events": trace_events,
        "transient_prompt_context": {
            "graph_name": "ask_graph",
            "thread_id": state["thread_id"],
            "run_id": state["run_id"],
        },
    }


def _execute_ask_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    ask_result = run_minimal_ask(
        WorkflowInvokeRequest(
            thread_id=state["thread_id"],
            action_type=state["action_type"],
            user_query=state.get("user_query"),
            note_path=state.get("note_path"),
            note_paths=list(state.get("note_paths", [])),
            require_approval=False,
            provider_preference=state.get("provider_preference"),
            retrieval_filter=state.get("retrieval_filter", RetrievalMetadataFilter()),
            metadata=dict(state.get("request_metadata", {})),
        ),
        settings=settings,
    )
    trace_events = append_trace_event(
        state,
        graph_name="ask_graph",
        node_name="execute_ask",
        event_type="completed",
        details={
            "result_mode": ask_result.mode.value,
            "candidate_count": len(ask_result.retrieved_candidates),
            "retrieval_fallback_used": ask_result.retrieval_fallback_used,
            "model_fallback_used": ask_result.model_fallback_used,
        },
        trace_hook=trace_hook,
    )
    return {
        "ask_result": ask_result,
        "retrieved_chunks": [
            candidate.model_dump(mode="json")
            for candidate in ask_result.retrieved_candidates
        ],
        "trace_events": trace_events,
    }


def _finalize_ask_node(
    state: StewardState,
    *,
    trace_hook: TraceHook | None,
) -> StewardState:
    ask_result = state.get("ask_result")
    trace_events = append_trace_event(
        state,
        graph_name="ask_graph",
        node_name="finalize_ask",
        event_type="completed",
        details={
            "result_mode": ask_result.mode.value if ask_result is not None else "missing",
            "trace_event_count_before_finalize": len(state.get("trace_events", [])),
        },
        trace_hook=trace_hook,
    )
    return {
        "trace_events": trace_events,
    }
