from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.config import Settings
from app.context.assembly import build_ask_context_bundle
from app.context.safety import detect_safety_flags
from app.context.render import render_grounded_answer_prompt, render_tool_selection_prompt
from app.contracts.workflow import (
    AskCitation,
    AskResultMode,
    AskWorkflowResult,
    ContextBundle,
    ContextEvidenceItem,
    GuardrailAction,
    GuardrailOutcome,
    RetrievedChunkCandidate,
    RuntimeFaithfulnessSignal,
    ToolCallDecision,
    ToolExecutionResult,
    WorkflowAction,
    WorkflowInvokeRequest,
)
from app.guardrails.ask import (
    evaluate_final_ask_response,
    evaluate_runtime_ask_faithfulness,
    evaluate_tool_call_outcome,
)
from app.quality.faithfulness import build_runtime_ask_faithfulness_signal
from app.retrieval.hybrid import search_hybrid_chunks_in_db
from app.tools.registry import (
    build_chat_completion_tools_for_workflow,
    execute_tool_call,
    get_allowed_tools_for_workflow,
)


ASK_RETRIEVAL_LIMIT = 4
ASK_CONTEXT_TOKEN_BUDGET = 2400
ASK_TOOL_RESULT_CHAR_BUDGET = 1200
MODEL_TIMEOUT_SECONDS = 20
CITATION_PATTERN = re.compile(r"\[(\d+)\]")
PROMPT_VISIBLE_TOOL_NAMES = {
    "load_note_excerpt",
    "get_note_outline",
}


@dataclass(frozen=True)
class ChatProviderTarget:
    provider_key: str
    provider_name: str
    base_url: str
    model_name: str
    api_key: str | None = None


class ChatProviderError(RuntimeError):
    """Raised when a configured chat provider cannot return a usable answer."""


@dataclass(frozen=True)
class AskTurnContext:
    query: str
    candidates: list[RetrievedChunkCandidate]
    bundle: ContextBundle
    prompt_candidates: list[RetrievedChunkCandidate]
    citations: list[AskCitation]
    retrieval_fallback_used: bool
    retrieval_fallback_reason: str | None
    allowed_tool_names: list[str]
    raw_tool_results: list[ToolExecutionResult]
    prompt_tool_results: list[ToolExecutionResult]


@dataclass(frozen=True)
class AskBenchmarkRuntimeConfig:
    context_assembly_enabled: bool = True
    runtime_faithfulness_gate_enabled: bool = True


def build_initial_ask_turn(
    request: WorkflowInvokeRequest,
    *,
    settings: Settings,
) -> AskTurnContext | AskWorkflowResult:
    query = _normalize_ask_query(request.user_query)
    allowed_tool_names = _get_allowed_tool_names(request.action_type)

    retrieval_response = search_hybrid_chunks_in_db(
        settings.index_db_path,
        query,
        settings=settings,
        limit=ASK_RETRIEVAL_LIMIT,
        metadata_filter=request.retrieval_filter,
        provider_preference=request.provider_preference,
    )
    candidates = retrieval_response.candidates

    if not candidates:
        return AskWorkflowResult(
            mode=AskResultMode.NO_HITS,
            query=query,
            answer="未找到可支撑回答的笔记片段，当前无法返回带引用的答案。",
            citations=[],
            retrieved_candidates=[],
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
            tool_call_rounds=0,
        )

    benchmark_runtime_config = _resolve_ask_benchmark_runtime_config(request.metadata)
    return _build_ask_turn_context(
        query=query,
        workflow_action=request.action_type,
        candidates=candidates,
        raw_tool_results=[],
        prompt_tool_results=[],
        retrieval_fallback_used=retrieval_response.fallback_used,
        retrieval_fallback_reason=retrieval_response.fallback_reason,
        allowed_tool_names=allowed_tool_names,
        benchmark_runtime_config=benchmark_runtime_config,
    )


def decide_ask_tool_call(
    turn: AskTurnContext,
    *,
    settings: Settings,
    provider_preference: str | None,
    workflow_action: WorkflowAction,
) -> tuple[ToolCallDecision, GuardrailOutcome]:
    tool_decision = _request_tool_call_decision(
        query=turn.query,
        bundle=turn.bundle,
        settings=settings,
        provider_preference=provider_preference,
    )
    return tool_decision, evaluate_tool_call_outcome(
        tool_decision,
        workflow_action=workflow_action,
    )


def apply_ask_tool_turn(
    turn: AskTurnContext,
    *,
    decision: ToolCallDecision,
    workflow_action: WorkflowAction,
    settings: Settings,
    request_metadata: dict[str, object] | None = None,
) -> AskTurnContext | AskWorkflowResult:
    if not decision.requested:
        return turn

    tool_result = execute_tool_call(
        decision,
        workflow_action=workflow_action,
        settings=settings,
    )
    next_raw_tool_results = [*turn.raw_tool_results, tool_result]
    if not tool_result.ok:
        return _build_retrieval_only_result(
            query=turn.query,
            citations=turn.citations,
            candidates=turn.prompt_candidates,
            retrieval_fallback_used=turn.retrieval_fallback_used,
            retrieval_fallback_reason=turn.retrieval_fallback_reason,
            tool_call_attempted=True,
            tool_call_rounds=len(next_raw_tool_results),
            tool_call_used=decision.tool_name,
            guardrail_outcome=GuardrailOutcome(
                action=GuardrailAction.TOOL_RESULT_INSUFFICIENT,
                applied=True,
                reasons=[tool_result.error or "tool_failed"],
            ),
        )

    if _tool_results_have_safety_flags([tool_result]):
        return _build_retrieval_only_result(
            query=turn.query,
            citations=turn.citations,
            candidates=turn.prompt_candidates,
            retrieval_fallback_used=turn.retrieval_fallback_used,
            retrieval_fallback_reason=turn.retrieval_fallback_reason,
            tool_call_attempted=True,
            tool_call_rounds=len(next_raw_tool_results),
            tool_call_used=decision.tool_name,
            guardrail_outcome=GuardrailOutcome(
                action=GuardrailAction.POSSIBLE_INJECTION_DETECTED,
                applied=True,
                reasons=["tool_result_flagged"],
            ),
        )

    next_prompt_tool_results = [
        *turn.prompt_tool_results,
        *_select_prompt_tool_results(
            [tool_result],
            prompt_candidates=turn.prompt_candidates,
        ),
    ]
    if not tool_result.allow_context_reentry and len(next_prompt_tool_results) == len(turn.prompt_tool_results):
        return _build_retrieval_only_result(
            query=turn.query,
            citations=turn.citations,
            candidates=turn.prompt_candidates,
            retrieval_fallback_used=turn.retrieval_fallback_used,
            retrieval_fallback_reason=turn.retrieval_fallback_reason,
            tool_call_attempted=True,
            tool_call_rounds=len(next_raw_tool_results),
            tool_call_used=decision.tool_name,
            guardrail_outcome=GuardrailOutcome(
                action=GuardrailAction.TOOL_RESULT_INSUFFICIENT,
                applied=True,
                reasons=["tool_result_not_prompt_safe"],
            ),
        )

    return _build_ask_turn_context(
        query=turn.query,
        workflow_action=workflow_action,
        candidates=turn.candidates,
        raw_tool_results=next_raw_tool_results,
        prompt_tool_results=next_prompt_tool_results,
        retrieval_fallback_used=turn.retrieval_fallback_used,
        retrieval_fallback_reason=turn.retrieval_fallback_reason,
        allowed_tool_names=turn.allowed_tool_names,
        benchmark_runtime_config=_resolve_ask_benchmark_runtime_config(request_metadata),
    )


def generate_ask_result(
    turn: AskTurnContext,
    *,
    settings: Settings,
    provider_preference: str | None,
    tool_call_attempted: bool,
    tool_call_used: str | None,
    tool_call_rounds: int,
    request_metadata: dict[str, object] | None = None,
) -> AskWorkflowResult:
    benchmark_runtime_config = _resolve_ask_benchmark_runtime_config(request_metadata)
    generated_answer, provider_target, model_fallback_reason = _try_generate_grounded_answer(
        query=turn.query,
        bundle=turn.bundle,
        settings=settings,
        provider_preference=provider_preference,
    )
    if generated_answer is None or provider_target is None:
        return _build_retrieval_only_result(
            query=turn.query,
            citations=turn.citations,
            candidates=turn.prompt_candidates,
            retrieval_fallback_used=turn.retrieval_fallback_used,
            retrieval_fallback_reason=turn.retrieval_fallback_reason,
            model_fallback_used=True,
            model_fallback_reason=model_fallback_reason,
            tool_call_attempted=tool_call_attempted,
            tool_call_rounds=tool_call_rounds,
            tool_call_used=tool_call_used,
        )

    citation_alignment_error = _validate_generated_answer_citations(
        answer=generated_answer,
        candidate_count=len(turn.citations),
    )
    if citation_alignment_error is not None:
        return _build_retrieval_only_result(
            query=turn.query,
            citations=turn.citations,
            candidates=turn.prompt_candidates,
            retrieval_fallback_used=turn.retrieval_fallback_used,
            retrieval_fallback_reason=turn.retrieval_fallback_reason,
            model_fallback_used=True,
            model_fallback_reason=citation_alignment_error,
            tool_call_attempted=tool_call_attempted,
            tool_call_rounds=tool_call_rounds,
            tool_call_used=tool_call_used,
        )

    final_guardrail = evaluate_final_ask_response(
        answer_text=generated_answer,
        citations=turn.citations,
        bundle=turn.bundle,
        tool_results=turn.raw_tool_results,
    )
    if final_guardrail.applied:
        return _build_retrieval_only_result(
            query=turn.query,
            citations=turn.citations,
            candidates=turn.prompt_candidates,
            retrieval_fallback_used=turn.retrieval_fallback_used,
            retrieval_fallback_reason=turn.retrieval_fallback_reason,
            tool_call_attempted=tool_call_attempted,
            tool_call_rounds=tool_call_rounds,
            tool_call_used=tool_call_used,
            guardrail_outcome=final_guardrail,
        )

    generated_result = AskWorkflowResult(
        mode=AskResultMode.GENERATED_ANSWER,
        query=turn.query,
        answer=generated_answer,
        citations=turn.citations,
        retrieved_candidates=turn.prompt_candidates,
        retrieval_fallback_used=turn.retrieval_fallback_used,
        retrieval_fallback_reason=turn.retrieval_fallback_reason,
        provider_name=provider_target.provider_name,
        model_name=provider_target.model_name,
        tool_call_attempted=tool_call_attempted,
        tool_call_rounds=tool_call_rounds,
        tool_call_used=tool_call_used,
        guardrail_action=final_guardrail.action,
    )
    runtime_faithfulness = build_runtime_ask_faithfulness_signal(
        generated_result,
        settings=settings,
        provider_preference=provider_preference,
    )
    generated_result = generated_result.model_copy(
        update={"runtime_faithfulness": runtime_faithfulness}
    )
    if not benchmark_runtime_config.runtime_faithfulness_gate_enabled:
        return generated_result

    faithfulness_guardrail = evaluate_runtime_ask_faithfulness(runtime_faithfulness)
    if faithfulness_guardrail.applied:
        return _build_retrieval_only_result(
            query=turn.query,
            citations=turn.citations,
            candidates=turn.prompt_candidates,
            retrieval_fallback_used=turn.retrieval_fallback_used,
            retrieval_fallback_reason=turn.retrieval_fallback_reason,
            tool_call_attempted=tool_call_attempted,
            tool_call_rounds=tool_call_rounds,
            tool_call_used=tool_call_used,
            guardrail_outcome=faithfulness_guardrail,
            runtime_faithfulness=runtime_faithfulness,
        )
    return generated_result


def _normalize_ask_query(user_query: str | None) -> str:
    query = (user_query or "").strip()
    if not query:
        raise ValueError("ask_qa requests must include a non-empty user_query.")
    return query


def _get_allowed_tool_names(workflow_action: WorkflowAction) -> list[str]:
    return [spec.name for spec in get_allowed_tools_for_workflow(workflow_action)]


def _build_ask_turn_context(
    *,
    query: str,
    workflow_action: WorkflowAction,
    candidates: list[RetrievedChunkCandidate],
    raw_tool_results: list[ToolExecutionResult],
    prompt_tool_results: list[ToolExecutionResult],
    retrieval_fallback_used: bool,
    retrieval_fallback_reason: str | None,
    allowed_tool_names: list[str],
    benchmark_runtime_config: AskBenchmarkRuntimeConfig,
) -> AskTurnContext | AskWorkflowResult:
    if benchmark_runtime_config.context_assembly_enabled:
        bundle = build_ask_context_bundle(
            user_query=query,
            candidates=candidates,
            tool_results=prompt_tool_results,
            token_budget=ASK_CONTEXT_TOKEN_BUDGET,
            allowed_tool_names=allowed_tool_names,
        )
    else:
        bundle = _build_raw_ask_context_bundle(
            user_query=query,
            workflow_action=workflow_action,
            candidates=candidates,
            tool_results=prompt_tool_results,
            token_budget=ASK_CONTEXT_TOKEN_BUDGET,
            allowed_tool_names=allowed_tool_names,
        )
    prompt_candidates = _select_prompt_candidates(candidates=candidates, bundle=bundle)
    citations = _build_citations(prompt_candidates)
    if bundle.safety_flags and not prompt_candidates:
        return _build_retrieval_only_result(
            query=query,
            citations=[],
            candidates=[],
            retrieval_fallback_used=retrieval_fallback_used,
            retrieval_fallback_reason=retrieval_fallback_reason,
            tool_call_attempted=bool(raw_tool_results),
            tool_call_rounds=len(raw_tool_results),
            tool_call_used=raw_tool_results[-1].tool_name if raw_tool_results else None,
            guardrail_outcome=GuardrailOutcome(
                action=GuardrailAction.POSSIBLE_INJECTION_DETECTED,
                applied=True,
                reasons=["all_visible_context_flagged"],
            ),
        )
    return AskTurnContext(
        query=query,
        candidates=candidates,
        bundle=bundle,
        prompt_candidates=prompt_candidates,
        citations=citations,
        retrieval_fallback_used=retrieval_fallback_used,
        retrieval_fallback_reason=retrieval_fallback_reason,
        allowed_tool_names=allowed_tool_names,
        raw_tool_results=raw_tool_results,
        prompt_tool_results=prompt_tool_results,
    )


def _resolve_ask_benchmark_runtime_config(
    metadata: dict[str, object] | None,
) -> AskBenchmarkRuntimeConfig:
    if not isinstance(metadata, dict):
        return AskBenchmarkRuntimeConfig()

    variant_metadata = metadata.get("answer_benchmark_variant")
    config_source: dict[str, object] | None = None
    if isinstance(variant_metadata, dict):
        config_source = variant_metadata
    elif metadata.get("benchmark_kind") == "ask_answer":
        config_source = metadata

    if config_source is None:
        return AskBenchmarkRuntimeConfig()

    return AskBenchmarkRuntimeConfig(
        context_assembly_enabled=_coerce_benchmark_toggle(
            config_source.get("context_assembly_enabled"),
            default=True,
        ),
        runtime_faithfulness_gate_enabled=_coerce_benchmark_toggle(
            config_source.get("runtime_faithfulness_gate_enabled"),
            default=True,
        ),
    )


def _coerce_benchmark_toggle(value: object, *, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _build_raw_ask_context_bundle(
    *,
    user_query: str,
    workflow_action: WorkflowAction,
    candidates: list[RetrievedChunkCandidate],
    tool_results: list[ToolExecutionResult],
    token_budget: int,
    allowed_tool_names: list[str],
) -> ContextBundle:
    evidence_items = _build_raw_retrieval_evidence_items(candidates)
    return ContextBundle(
        user_intent=user_query,
        workflow_action=workflow_action,
        evidence_items=evidence_items,
        tool_results=tool_results,
        allowed_tool_names=allowed_tool_names,
        token_budget=token_budget,
        safety_flags=_collect_raw_bundle_safety_flags(candidates, tool_results),
        assembly_notes=["benchmark_variant:raw_retrieval_candidates"],
    )


def _build_raw_retrieval_evidence_items(
    candidates: list[RetrievedChunkCandidate],
) -> list[ContextEvidenceItem]:
    total_by_path: dict[str, int] = {}
    for candidate in candidates:
        total_by_path[candidate.path] = total_by_path.get(candidate.path, 0) + 1

    seen_by_path: dict[str, int] = {}
    evidence_items: list[ContextEvidenceItem] = []
    for candidate in candidates:
        seen_by_path[candidate.path] = seen_by_path.get(candidate.path, 0) + 1
        evidence_items.append(
            ContextEvidenceItem(
                source_path=candidate.path,
                chunk_id=candidate.chunk_id,
                source_note_title=candidate.title,
                heading_path=candidate.heading_path,
                position_hint=(
                    f"第 {seen_by_path[candidate.path]} 条 / "
                    f"共 {total_by_path[candidate.path]} 条"
                ),
                text=candidate.text,
                score=candidate.score,
                source_kind="retrieval",
            )
        )
    return evidence_items


def _collect_raw_bundle_safety_flags(
    candidates: list[RetrievedChunkCandidate],
    tool_results: list[ToolExecutionResult],
) -> list[str]:
    flags: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        for flag in detect_safety_flags(candidate.text):
            if flag in seen:
                continue
            seen.add(flag)
            flags.append(flag)

    for result in tool_results:
        if not result.ok or not result.allow_context_reentry or not result.data:
            continue
        payload = json.dumps(result.data, ensure_ascii=False, sort_keys=True)
        for flag in detect_safety_flags(payload):
            if flag in seen:
                continue
            seen.add(flag)
            flags.append(flag)

    return flags


def _build_citations(candidates: list[RetrievedChunkCandidate]) -> list[AskCitation]:
    return [
        AskCitation(
            chunk_id=candidate.chunk_id,
            path=candidate.path,
            title=candidate.title,
            heading_path=candidate.heading_path,
            start_line=candidate.start_line,
            end_line=candidate.end_line,
            score=candidate.score,
            snippet=candidate.snippet,
            retrieval_source=candidate.retrieval_source,
        )
        for candidate in candidates
    ]


def _select_prompt_candidates(
    candidates: list[RetrievedChunkCandidate],
    bundle: ContextBundle,
) -> list[RetrievedChunkCandidate]:
    # Prompt-visible citations always follow the assembled bundle order, not the raw
    # retrieval order. That keeps citation numbering aligned with what the user can
    # actually see in the rendered prompt.
    retrieval_chunk_ids = [
        item.chunk_id
        for item in bundle.evidence_items
        if item.source_kind == "retrieval" and item.chunk_id is not None
    ]
    candidate_by_chunk_id = {candidate.chunk_id: candidate for candidate in candidates}
    return [
        candidate_by_chunk_id[chunk_id]
        for chunk_id in retrieval_chunk_ids
        if chunk_id in candidate_by_chunk_id
    ]


def _tool_results_have_safety_flags(tool_results: list[ToolExecutionResult]) -> bool:
    return any(
        detect_safety_flags(json.dumps(result.data, ensure_ascii=False, sort_keys=True))
        for result in tool_results
        if result.ok and result.data
    )


def _select_prompt_tool_results(
    tool_results: list[ToolExecutionResult],
    *,
    prompt_candidates: list[RetrievedChunkCandidate],
) -> list[ToolExecutionResult]:
    selected: list[ToolExecutionResult] = []
    for result in tool_results:
        if not result.ok or not result.data:
            continue
        if result.tool_name not in PROMPT_VISIBLE_TOOL_NAMES:
            continue
        trimmed_data = dict(result.data)
        if result.tool_name == "load_note_excerpt":
            note_path = trimmed_data.get("note_path")
            excerpt = trimmed_data.get("excerpt")
            if not isinstance(note_path, str) or not isinstance(excerpt, str):
                continue
            if not _has_unique_prompt_candidate_path(note_path, prompt_candidates):
                continue
            trimmed_data["excerpt"] = excerpt[:ASK_TOOL_RESULT_CHAR_BUDGET]
        elif result.tool_name == "get_note_outline":
            note_path = trimmed_data.get("note_path")
            if not isinstance(note_path, str) or not _has_unique_prompt_candidate_path(note_path, prompt_candidates):
                continue
            if _serialized_tool_payload_chars(trimmed_data) > ASK_TOOL_RESULT_CHAR_BUDGET:
                continue
        selected.append(
            ToolExecutionResult(
                tool_name=result.tool_name,
                ok=result.ok,
                data=trimmed_data,
                error=result.error,
                allow_context_reentry=True,
            )
    )
    return selected


def _serialized_tool_payload_chars(data: dict[str, object]) -> int:
    return len(json.dumps(data, ensure_ascii=False, sort_keys=True))


def _has_unique_prompt_candidate_path(
    note_path: str,
    prompt_candidates: list[RetrievedChunkCandidate],
) -> bool:
    normalized_note_parts = _normalize_path_parts(note_path)
    if not normalized_note_parts:
        return False
    matching_candidate_paths: set[tuple[str, ...]] = set()
    for candidate in prompt_candidates:
        candidate_parts = _normalize_path_parts(candidate.path)
        if len(candidate_parts) < len(normalized_note_parts):
            continue
        if candidate_parts[-len(normalized_note_parts):] == normalized_note_parts:
            matching_candidate_paths.add(candidate_parts)
            if len(matching_candidate_paths) > 1:
                return False
    return len(matching_candidate_paths) == 1


def _normalize_path_parts(path_value: str) -> tuple[str, ...]:
    return tuple(part for part in Path(path_value.replace("\\", "/")).parts if part not in {"", "."})


def _build_retrieval_only_answer(
    *,
    query: str,
    citations: list[AskCitation],
    retrieval_fallback_used: bool,
) -> str:
    lines = [
        f"当前未使用模型生成答案，先返回与问题“{query}”最相关的检索证据。",
    ]
    if retrieval_fallback_used:
        # 这里单独提示 retrieval fallback，是为了防止上游把“放宽过滤后的候选”
        # 误当成严格条件下的强命中，导致用户高估答案可信度。
        lines.append("注意：结构化过滤条件过严，检索已退回纯 FTS 结果。")

    for index, citation in enumerate(citations, start=1):
        location = citation.heading_path or citation.title
        lines.append(
            f"[{index}] {Path(citation.path).name} / {location} "
            f"(lines {citation.start_line}-{citation.end_line}): {citation.snippet}"
        )
    return "\n".join(lines)


def _build_retrieval_only_result(
    *,
    query: str,
    citations: list[AskCitation],
    candidates: list[RetrievedChunkCandidate],
    retrieval_fallback_used: bool,
    retrieval_fallback_reason: str | None,
    model_fallback_used: bool = False,
    model_fallback_reason: str | None = None,
    tool_call_attempted: bool = False,
    tool_call_rounds: int = 0,
    tool_call_used: str | None = None,
    guardrail_outcome: GuardrailOutcome | None = None,
    runtime_faithfulness: RuntimeFaithfulnessSignal | None = None,
) -> AskWorkflowResult:
    return AskWorkflowResult(
        mode=AskResultMode.RETRIEVAL_ONLY,
        query=query,
        answer=_build_retrieval_only_answer(
            query=query,
            citations=citations,
            retrieval_fallback_used=retrieval_fallback_used,
        ),
        citations=citations,
        retrieved_candidates=candidates,
        retrieval_fallback_used=retrieval_fallback_used,
        retrieval_fallback_reason=retrieval_fallback_reason,
        model_fallback_used=model_fallback_used,
        model_fallback_reason=model_fallback_reason,
        tool_call_attempted=tool_call_attempted,
        tool_call_rounds=tool_call_rounds,
        tool_call_used=tool_call_used,
        guardrail_action=guardrail_outcome.action if guardrail_outcome is not None else None,
        runtime_faithfulness=runtime_faithfulness,
    )


def build_retrieval_only_ask_result(**kwargs: object) -> AskWorkflowResult:
    return _build_retrieval_only_result(**kwargs)


def _request_tool_call_decision(
    *,
    query: str,
    bundle: ContextBundle,
    settings: Settings,
    provider_preference: str | None,
) -> ToolCallDecision:
    provider_targets = _resolve_chat_provider_targets(
        settings=settings,
        provider_preference=provider_preference,
    )
    if not provider_targets:
        return ToolCallDecision(requested=False)

    for provider_target in provider_targets:
        structured_decision = _request_structured_tool_call_decision(
            provider_target=provider_target,
            query=query,
            bundle=bundle,
        )
        if structured_decision is not None:
            return structured_decision

        prompt_decision = _request_prompt_tool_call_decision(
            provider_target=provider_target,
            query=query,
            bundle=bundle,
        )
        if prompt_decision is not None:
            return prompt_decision

    return ToolCallDecision(requested=False)


def _build_tool_selection_messages(
    *,
    query: str,
    bundle: ContextBundle,
) -> list[dict[str, str]]:
    _ = query
    return [
        {
            "role": "system",
            "content": (
                "You decide whether exactly one read-only tool call is needed before answering. "
                "Return strict JSON only with keys requested, tool_name, arguments, rationale. "
                "If no tool is needed, return "
                "{\"requested\": false, \"tool_name\": null, \"arguments\": {}, \"rationale\": \"\"}."
            ),
        },
        {
            "role": "user",
            "content": render_tool_selection_prompt(bundle),
        },
    ]


def _build_structured_tool_selection_messages(
    *,
    query: str,
    bundle: ContextBundle,
) -> list[dict[str, str]]:
    _ = query
    return [
        {
            "role": "system",
            "content": (
                "You decide whether exactly one read-only tool call is needed before answering. "
                "Use at most one tool. If no tool is needed, respond without calling a tool."
            ),
        },
        {
            "role": "user",
            "content": render_tool_selection_prompt(bundle),
        },
    ]


def _parse_tool_call_decision(raw_text: str) -> ToolCallDecision:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return ToolCallDecision(requested=False)

    if not isinstance(payload, dict):
        return ToolCallDecision(requested=False)

    requested = payload.get("requested")
    if not isinstance(requested, bool) or not requested:
        return ToolCallDecision(requested=False)

    tool_name = payload.get("tool_name")
    arguments = payload.get("arguments")
    rationale = payload.get("rationale")
    return ToolCallDecision(
        requested=True,
        tool_name=tool_name if isinstance(tool_name, str) else None,
        arguments=arguments if isinstance(arguments, dict) else {},
        rationale=rationale if isinstance(rationale, str) else None,
    )


def _parse_structured_tool_call_decision(
    response_payload: dict[str, object],
) -> ToolCallDecision | None:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return None

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return None

    tool_calls = message.get("tool_calls")
    if tool_calls is None:
        return ToolCallDecision(requested=False)
    if not isinstance(tool_calls, list):
        return None
    if not tool_calls:
        return ToolCallDecision(requested=False)

    first_tool_call = tool_calls[0]
    if not isinstance(first_tool_call, dict):
        return None
    if first_tool_call.get("type") != "function":
        return None

    function_payload = first_tool_call.get("function")
    if not isinstance(function_payload, dict):
        return None

    tool_name = function_payload.get("name")
    if not isinstance(tool_name, str) or not tool_name.strip():
        return None

    raw_arguments = function_payload.get("arguments")
    if raw_arguments in (None, ""):
        arguments: dict[str, object] = {}
    elif isinstance(raw_arguments, str):
        try:
            parsed_arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed_arguments, dict):
            return None
        arguments = parsed_arguments
    else:
        return None

    return ToolCallDecision(
        requested=True,
        tool_name=tool_name,
        arguments=arguments,
    )


def _request_structured_tool_call_decision(
    *,
    provider_target: ChatProviderTarget,
    query: str,
    bundle: ContextBundle,
) -> ToolCallDecision | None:
    payload = {
        "model": provider_target.model_name,
        "temperature": 0,
        "messages": _build_structured_tool_selection_messages(query=query, bundle=bundle),
        "tools": build_chat_completion_tools_for_workflow(bundle.workflow_action),
        "tool_choice": "auto",
    }
    try:
        response_payload = _request_chat_completion_payload(
            provider_target=provider_target,
            payload=payload,
        )
    except ChatProviderError:
        return None
    return _parse_structured_tool_call_decision(response_payload)


def _request_prompt_tool_call_decision(
    *,
    provider_target: ChatProviderTarget,
    query: str,
    bundle: ContextBundle,
) -> ToolCallDecision | None:
    payload = {
        "model": provider_target.model_name,
        "temperature": 0,
        "messages": _build_tool_selection_messages(query=query, bundle=bundle),
    }
    try:
        response_payload = _request_chat_completion_payload(
            provider_target=provider_target,
            payload=payload,
        )
    except ChatProviderError:
        return None

    raw_text = _extract_chat_completion_text(response_payload)
    if not raw_text:
        return None
    return _parse_tool_call_decision(raw_text)


def _validate_generated_answer_citations(
    *,
    answer: str,
    candidate_count: int,
) -> str | None:
    normalized_answer = answer.strip()
    if not normalized_answer:
        return "citation_alignment_empty_answer"

    citation_numbers = [int(match.group(1)) for match in CITATION_PATTERN.finditer(normalized_answer)]
    if not citation_numbers:
        return "citation_alignment_missing_reference"

    # 只要模型引用了当前候选范围外的编号，就说明 answer 和当前证据集合已经脱钩。
    # 这里宁可保守降级，也不把“看起来像有引用”的坏答案继续往下游传。
    invalid_numbers = [
        citation_number
        for citation_number in citation_numbers
        if citation_number < 1 or citation_number > candidate_count
    ]
    if invalid_numbers:
        return "citation_alignment_out_of_range"

    return None


def _try_generate_grounded_answer(
    *,
    query: str,
    bundle: ContextBundle,
    settings: Settings,
    provider_preference: str | None,
) -> tuple[str | None, ChatProviderTarget | None, str | None]:
    provider_targets = _resolve_chat_provider_targets(
        settings=settings,
        provider_preference=provider_preference,
    )
    if not provider_targets:
        return None, None, "no_available_chat_provider"

    last_error: ChatProviderError | None = None
    for provider_target in provider_targets:
        try:
            answer = _request_grounded_answer(
                provider_target=provider_target,
                query=query,
                bundle=bundle,
            )
        except ChatProviderError as exc:
            last_error = exc
            continue
        return answer, provider_target, None

    if last_error is not None:
        return None, None, "all_chat_providers_failed"
    return None, None, "no_available_chat_provider"


def _resolve_chat_provider_targets(
    *,
    settings: Settings,
    provider_preference: str | None,
) -> list[ChatProviderTarget]:
    normalized_preference = (provider_preference or settings.default_model_provider).strip().casefold()
    cloud_target = _build_provider_target(
        provider_key="cloud",
        provider_name=settings.cloud_provider_name,
        base_url=settings.cloud_base_url,
        model_name=settings.cloud_chat_model,
        api_key=settings.cloud_api_key or None,
    )
    local_target = _build_provider_target(
        provider_key="local",
        provider_name=settings.local_provider_name,
        base_url=settings.local_base_url,
        model_name=settings.local_chat_model,
        api_key=None,
    )

    available_targets = [target for target in (cloud_target, local_target) if target is not None]
    if not available_targets:
        return []

    if normalized_preference in {"local", settings.local_provider_name.casefold()}:
        preferred_order = ["local", "cloud"]
    else:
        preferred_order = ["cloud", "local"]

    # 这里保留“首选 provider 失败后尝试下一条”的顺序，是为了让 ask 链路先把
    # 云优先、本地兼容的降级路径走通，而不是一遇到 provider 波动就直接报错。
    ordered_targets: list[ChatProviderTarget] = []
    for provider_key in preferred_order:
        for target in available_targets:
            if target.provider_key == provider_key:
                ordered_targets.append(target)
    return ordered_targets


def _build_provider_target(
    *,
    provider_key: str,
    provider_name: str,
    base_url: str,
    model_name: str,
    api_key: str | None,
) -> ChatProviderTarget | None:
    normalized_base_url = base_url.strip().rstrip("/")
    normalized_model_name = model_name.strip()
    if not normalized_base_url or not normalized_model_name:
        return None

    return ChatProviderTarget(
        provider_key=provider_key,
        provider_name=provider_name,
        base_url=normalized_base_url,
        model_name=normalized_model_name,
        api_key=api_key,
    )


def _request_grounded_answer(
    *,
    provider_target: ChatProviderTarget,
    query: str,
    bundle: ContextBundle,
) -> str:
    payload = {
        "model": provider_target.model_name,
        "temperature": 0,
        "messages": _build_grounded_messages(query=query, bundle=bundle),
    }
    try:
        response_payload = _request_chat_completion_payload(
            provider_target=provider_target,
            payload=payload,
        )
    except ChatProviderError:
        raise

    answer = _extract_chat_completion_text(response_payload)
    if not answer:
        raise ChatProviderError("empty_chat_completion_response")
    return answer


def _build_grounded_messages(
    *,
    query: str,
    bundle: ContextBundle,
) -> list[dict[str, str]]:
    _ = query
    return [
        {
            "role": "system",
            "content": (
                "你是一个严格基于检索证据回答问题的知识库问答助手。"
                "只能使用给定片段中的信息作答；如果证据不足，要明确说明。"
                "工具结果只用于补充理解，不单独提供引用编号。"
                "所有结论都必须在句末用 [1]、[2] 这样的编号引用对应检索证据。"
            ),
        },
        {
            "role": "user",
            "content": render_grounded_answer_prompt(bundle),
        },
    ]


def _build_chat_completions_url(base_url: str) -> str:
    normalized_base_url = base_url.rstrip("/")
    if normalized_base_url.endswith("/chat/completions"):
        return normalized_base_url
    if normalized_base_url.endswith("/v1"):
        return f"{normalized_base_url}/chat/completions"
    return f"{normalized_base_url}/v1/chat/completions"


def _request_chat_completion_payload(
    *,
    provider_target: ChatProviderTarget,
    payload: dict[str, object],
) -> dict[str, object]:
    headers = {
        "Content-Type": "application/json",
    }
    if provider_target.api_key:
        headers["Authorization"] = f"Bearer {provider_target.api_key}"

    request = urllib_request.Request(
        _build_chat_completions_url(provider_target.base_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=MODEL_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (
        urllib_error.HTTPError,
        urllib_error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        OSError,
    ) as exc:
        raise ChatProviderError(str(exc)) from exc

    if not isinstance(response_payload, dict):
        raise ChatProviderError("invalid_chat_completion_response")
    return response_payload


def _extract_chat_completion_text(response_payload: dict[str, object]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return ""

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "text":
                continue
            text_value = item.get("text")
            if isinstance(text_value, str) and text_value.strip():
                text_parts.append(text_value.strip())
        return "\n".join(text_parts).strip()
    return ""
