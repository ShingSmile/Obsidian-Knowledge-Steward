from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings
from app.contracts.workflow import (
    AskCitation,
    AskWorkflowResult,
    ContextBundle,
    RetrievalMetadataFilter,
    RetrievedChunkCandidate,
    ToolCallDecision,
    ToolExecutionResult,
    WorkflowInvokeRequest,
)
from app.graphs.runtime import (
    END,
    START,
    StateGraph,
    TraceHook,
    append_trace_event,
    build_base_workflow_state,
    build_workflow_graph_execution,
    build_workflow_runtime_trace_hook,
    invoke_checkpointed_compiled_graph,
    open_sqlite_checkpointer,
    save_business_checkpoint_safely,
    WorkflowGraphExecution,
)
from app.graphs.checkpoint import WorkflowCheckpointStatus
from app.graphs.state import StewardState
from app.services.ask import (
    AskTurnContext,
    apply_ask_tool_turn,
    build_retrieval_only_ask_result,
    build_initial_ask_turn,
    decide_ask_tool_call,
    generate_ask_result,
)


DEFAULT_ASK_MAX_TOOL_ROUNDS = 3


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
    with open_sqlite_checkpointer(settings.index_db_path) as checkpointer:
        graph = build_ask_graph(
            settings=settings,
            trace_hook=runtime_trace_hook,
            checkpointer=checkpointer,
        )
        execution = invoke_checkpointed_compiled_graph(
            graph_name="ask_graph",
            graph=graph,
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

    if not (
        execution.checkpoint_used
        and execution.resumed_from_status == WorkflowCheckpointStatus.COMPLETED
    ):
        save_business_checkpoint_safely(
            db_path=settings.index_db_path,
            graph_name="ask_graph",
            checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
            last_completed_node=_resolve_last_completed_node(final_state),
            next_node_name=None,
            state=final_state,
        )

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
    configured_max_rounds = request.metadata.get("max_tool_rounds", DEFAULT_ASK_MAX_TOOL_ROUNDS)
    if not isinstance(configured_max_rounds, int) or configured_max_rounds < 0:
        configured_max_rounds = DEFAULT_ASK_MAX_TOOL_ROUNDS
    return {
        **build_base_workflow_state(
            request,
            thread_id=thread_id,
            run_id=run_id,
        ),
        "retrieved_chunks": [],
        "ask_query": "",
        "ask_candidates": [],
        "ask_bundle": {},
        "ask_tool_decision": None,
        "ask_tool_results": [],
        "ask_prompt_candidates": [],
        "ask_citations": [],
        "ask_tool_call_rounds": 0,
        "ask_max_tool_rounds": configured_max_rounds,
        "ask_should_finalize": False,
        "ask_prompt_tool_results": [],
        "ask_retrieval_fallback_used": False,
        "ask_retrieval_fallback_reason": None,
        "ask_tool_call_attempted": False,
        "ask_tool_call_used": None,
    }


def build_ask_graph(
    *,
    settings: Settings,
    trace_hook: TraceHook | None = None,
    checkpointer: Any | None = None,
):
    workflow = StateGraph(StewardState)
    workflow.add_node("prepare_ask", lambda state: _prepare_ask_node(state, settings=settings, trace_hook=trace_hook))
    workflow.add_node("llm_call", lambda state: _llm_call_node(state, settings=settings, trace_hook=trace_hook))
    workflow.add_node("tool_node", lambda state: _tool_node(state, settings=settings, trace_hook=trace_hook))
    workflow.add_node("finalize_ask", lambda state: _finalize_ask_node(state, settings=settings, trace_hook=trace_hook))
    workflow.add_edge(START, "prepare_ask")
    workflow.add_edge("prepare_ask", "llm_call")
    workflow.add_conditional_edges(
        "llm_call",
        _route_after_llm_call,
        {
            "tool_node": "tool_node",
            "finalize_ask": "finalize_ask",
        },
    )
    workflow.add_edge("tool_node", "llm_call")
    workflow.add_edge("finalize_ask", END)
    return workflow.compile(checkpointer=checkpointer)


def _resolve_last_completed_node(state: StewardState) -> str | None:
    trace_events = state.get("trace_events", [])
    if not trace_events:
        return None
    return trace_events[-1]["node_name"]


def _prepare_ask_node(
    state: StewardState,
    *,
    settings: Settings,
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
    initial_turn = build_initial_ask_turn(
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
    updates: StewardState = {
        "approval_required": False,
        "trace_events": trace_events,
        "transient_prompt_context": {
            "graph_name": "ask_graph",
            "thread_id": state["thread_id"],
            "run_id": state["run_id"],
        },
    }
    if isinstance(initial_turn, AskWorkflowResult):
        updates["ask_result"] = initial_turn
        updates["ask_query"] = initial_turn.query
        updates["ask_should_finalize"] = True
        updates["retrieved_chunks"] = [
            candidate.model_dump(mode="json")
            for candidate in initial_turn.retrieved_candidates
        ]
        updates["ask_prompt_candidates"] = [
            candidate.model_dump(mode="json")
            for candidate in initial_turn.retrieved_candidates
        ]
        updates["ask_citations"] = [
            citation.model_dump(mode="json")
            for citation in initial_turn.citations
        ]
        updates["ask_retrieval_fallback_used"] = initial_turn.retrieval_fallback_used
        updates["ask_retrieval_fallback_reason"] = initial_turn.retrieval_fallback_reason
        updates["ask_tool_call_attempted"] = initial_turn.tool_call_attempted
        updates["ask_tool_call_used"] = initial_turn.tool_call_used
        updates["ask_tool_call_rounds"] = initial_turn.tool_call_rounds
        return updates

    updates.update(_turn_context_to_state_updates(initial_turn))
    updates["ask_should_finalize"] = False
    return updates


def _llm_call_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    if state.get("ask_result") is not None:
        ask_result = state["ask_result"]
        trace_events = append_trace_event(
            state,
            graph_name="ask_graph",
            node_name="llm_call",
            event_type="completed",
            details={
                "result_mode": ask_result.mode.value if ask_result is not None else "",
                "tool_call_attempted": state.get("ask_tool_call_attempted", False),
                "tool_call_used": state.get("ask_tool_call_used") or "",
                "guardrail_action": (
                    ask_result.guardrail_action.value
                    if ask_result is not None and ask_result.guardrail_action
                    else ""
                ),
                "tool_call_rounds": state.get("ask_tool_call_rounds", 0),
                "requested_tool_call": False,
                "route": "finalize_ask",
            },
            trace_hook=trace_hook,
        )
        return {
            "trace_events": trace_events,
            "ask_should_finalize": True,
        }

    turn = _turn_context_from_state(state)
    decision, guardrail = decide_ask_tool_call(
        turn,
        settings=settings,
        provider_preference=state.get("provider_preference"),
        workflow_action=state["action_type"],
    )
    tool_call_attempted = state.get("ask_tool_call_attempted", False) or decision.requested
    tool_call_used = decision.tool_name if decision.requested else state.get("ask_tool_call_used")
    route = "finalize_ask"
    forced_finalize_reason = ""
    updates: StewardState = {
        "ask_tool_decision": decision.model_dump(mode="json"),
        "ask_tool_call_attempted": tool_call_attempted,
        "ask_tool_call_used": tool_call_used,
    }
    if guardrail.applied:
        updates["ask_result"] = _build_guardrailed_result(
            state=state,
            turn=turn,
            decision=decision,
            guardrail=guardrail,
        )
        updates["ask_should_finalize"] = True
    elif decision.requested and state.get("ask_tool_call_rounds", 0) < state.get("ask_max_tool_rounds", DEFAULT_ASK_MAX_TOOL_ROUNDS):
        route = "tool_node"
        updates["ask_should_finalize"] = False
    else:
        updates["ask_should_finalize"] = True
        if decision.requested:
            forced_finalize_reason = "max_tool_rounds"

    trace_events = append_trace_event(
        state,
        graph_name="ask_graph",
        node_name="llm_call",
        event_type="completed",
        details={
            "result_mode": (
                updates["ask_result"].mode.value
                if updates.get("ask_result") is not None
                else ""
            ),
            "tool_call_attempted": tool_call_attempted,
            "tool_call_used": tool_call_used or "",
            "guardrail_action": guardrail.action.value if guardrail.applied else "",
            "tool_call_rounds": state.get("ask_tool_call_rounds", 0),
            "requested_tool_call": decision.requested,
            "route": route,
            "forced_finalize_reason": forced_finalize_reason,
        },
        trace_hook=trace_hook,
    )
    updates["trace_events"] = trace_events
    return updates


def _route_after_llm_call(state: StewardState) -> str:
    if state.get("ask_should_finalize", False):
        return "finalize_ask"
    decision = state.get("ask_tool_decision")
    if isinstance(decision, dict) and decision.get("requested") is True:
        return "tool_node"
    return "finalize_ask"


def _tool_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    turn = _turn_context_from_state(state)
    decision = _tool_decision_from_state(state)
    next_turn = apply_ask_tool_turn(
        turn,
        decision=decision,
        workflow_action=state["action_type"],
        settings=settings,
    )
    updates: StewardState = {
        "ask_tool_call_rounds": state.get("ask_tool_call_rounds", 0) + 1,
    }
    if isinstance(next_turn, AskWorkflowResult):
        updates["ask_result"] = next_turn
        updates["ask_should_finalize"] = True
        updates["retrieved_chunks"] = [
            candidate.model_dump(mode="json")
            for candidate in next_turn.retrieved_candidates
        ]
        updates["ask_prompt_candidates"] = [
            candidate.model_dump(mode="json")
            for candidate in next_turn.retrieved_candidates
        ]
        updates["ask_citations"] = [
            citation.model_dump(mode="json")
            for citation in next_turn.citations
        ]
    else:
        updates.update(_turn_context_to_state_updates(next_turn))
        updates["ask_should_finalize"] = False

    trace_events = append_trace_event(
        state,
        graph_name="ask_graph",
        node_name="tool_node",
        event_type="completed",
        details={
            "result_mode": (
                next_turn.mode.value
                if isinstance(next_turn, AskWorkflowResult)
                else ""
            ),
            "tool_call_used": decision.tool_name or "",
            "tool_call_rounds": updates["ask_tool_call_rounds"],
            "guardrail_action": (
                next_turn.guardrail_action.value
                if isinstance(next_turn, AskWorkflowResult) and next_turn.guardrail_action
                else ""
            ),
        },
        trace_hook=trace_hook,
    )
    updates["trace_events"] = trace_events
    return updates


def _finalize_ask_node(
    state: StewardState,
    *,
    settings: Settings,
    trace_hook: TraceHook | None,
) -> StewardState:
    ask_result = state.get("ask_result")
    if ask_result is None:
        turn = _turn_context_from_state(state)
        ask_result = generate_ask_result(
            turn,
            settings=settings,
            provider_preference=state.get("provider_preference"),
            tool_call_attempted=state.get("ask_tool_call_attempted", False),
            tool_call_used=state.get("ask_tool_call_used"),
            tool_call_rounds=state.get("ask_tool_call_rounds", 0),
        )
    trace_events = append_trace_event(
        state,
        graph_name="ask_graph",
        node_name="finalize_ask",
        event_type="completed",
        details={
            "result_mode": ask_result.mode.value if ask_result is not None else "missing",
            "trace_event_count_before_finalize": len(state.get("trace_events", [])),
            "tool_call_rounds": ask_result.tool_call_rounds if ask_result is not None else 0,
        },
        trace_hook=trace_hook,
    )
    return {
        "ask_result": ask_result,
        "retrieved_chunks": [
            candidate.model_dump(mode="json")
            for candidate in ask_result.retrieved_candidates
        ] if ask_result is not None else [],
        "ask_prompt_candidates": [
            candidate.model_dump(mode="json")
            for candidate in ask_result.retrieved_candidates
        ] if ask_result is not None else [],
        "ask_citations": [
            citation.model_dump(mode="json")
            for citation in ask_result.citations
        ] if ask_result is not None else [],
        "trace_events": trace_events,
    }


def _turn_context_to_state_updates(turn: AskTurnContext) -> StewardState:
    return {
        "ask_query": turn.query,
        "ask_candidates": [
            candidate.model_dump(mode="json")
            for candidate in turn.candidates
        ],
        "ask_bundle": turn.bundle.model_dump(mode="json"),
        "ask_prompt_candidates": [
            candidate.model_dump(mode="json")
            for candidate in turn.prompt_candidates
        ],
        "ask_citations": [
            citation.model_dump(mode="json")
            for citation in turn.citations
        ],
        "ask_tool_results": [
            result.model_dump(mode="json")
            for result in turn.raw_tool_results
        ],
        "ask_prompt_tool_results": [
            result.model_dump(mode="json")
            for result in turn.prompt_tool_results
        ],
        "ask_retrieval_fallback_used": turn.retrieval_fallback_used,
        "ask_retrieval_fallback_reason": turn.retrieval_fallback_reason,
        "retrieved_chunks": [
            candidate.model_dump(mode="json")
            for candidate in turn.prompt_candidates
        ],
    }


def _turn_context_from_state(state: StewardState) -> AskTurnContext:
    return AskTurnContext(
        query=state.get("ask_query", ""),
        candidates=[
            RetrievedChunkCandidate.model_validate(candidate)
            for candidate in state.get("ask_candidates", [])
        ],
        bundle=ContextBundle.model_validate(state.get("ask_bundle", {})),
        prompt_candidates=[
            RetrievedChunkCandidate.model_validate(candidate)
            for candidate in state.get("ask_prompt_candidates", [])
        ],
        citations=[
            AskCitation.model_validate(citation)
            for citation in state.get("ask_citations", [])
        ],
        retrieval_fallback_used=state.get("ask_retrieval_fallback_used", False),
        retrieval_fallback_reason=state.get("ask_retrieval_fallback_reason"),
        allowed_tool_names=ContextBundle.model_validate(state.get("ask_bundle", {})).allowed_tool_names,
        raw_tool_results=[
            ToolExecutionResult.model_validate(result)
            for result in state.get("ask_tool_results", [])
        ],
        prompt_tool_results=[
            ToolExecutionResult.model_validate(result)
            for result in state.get("ask_prompt_tool_results", [])
        ],
    )


def _tool_decision_from_state(state: StewardState) -> ToolCallDecision:
    decision = state.get("ask_tool_decision")
    if isinstance(decision, dict):
        return ToolCallDecision.model_validate(decision)
    return ToolCallDecision(requested=False)


def _build_guardrailed_result(
    *,
    state: StewardState,
    turn: AskTurnContext,
    decision: ToolCallDecision,
    guardrail,
) -> AskWorkflowResult:
    return build_retrieval_only_ask_result(
        query=turn.query,
        citations=turn.citations,
        candidates=turn.prompt_candidates,
        retrieval_fallback_used=turn.retrieval_fallback_used,
        retrieval_fallback_reason=turn.retrieval_fallback_reason,
        tool_call_attempted=state.get("ask_tool_call_attempted", False) or decision.requested,
        tool_call_rounds=state.get("ask_tool_call_rounds", 0),
        tool_call_used=decision.tool_name,
        guardrail_outcome=guardrail,
    )
