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
    ContextBundle,
    AskResultMode,
    AskWorkflowResult,
    GuardrailAction,
    GuardrailOutcome,
    RetrievedChunkCandidate,
    ToolCallDecision,
    ToolExecutionResult,
    WorkflowInvokeRequest,
)
from app.guardrails.ask import evaluate_final_ask_response, evaluate_tool_call_outcome
from app.retrieval.hybrid import search_hybrid_chunks_in_db
from app.tools.registry import execute_tool_call, get_allowed_tools_for_workflow


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


def run_minimal_ask(
    request: WorkflowInvokeRequest,
    *,
    settings: Settings,
) -> AskWorkflowResult:
    query = (request.user_query or "").strip()
    if not query:
        raise ValueError("ask_qa requests must include a non-empty user_query.")

    retrieval_response = search_hybrid_chunks_in_db(
        settings.index_db_path,
        query,
        settings=settings,
        limit=ASK_RETRIEVAL_LIMIT,
        metadata_filter=request.retrieval_filter,
        provider_preference=request.provider_preference,
    )
    candidates = retrieval_response.candidates
    allowed_tool_names = [
        spec.name for spec in get_allowed_tools_for_workflow(request.action_type)
    ]

    if not candidates:
        return AskWorkflowResult(
            mode=AskResultMode.NO_HITS,
            query=query,
            answer="未找到可支撑回答的笔记片段，当前无法返回带引用的答案。",
            citations=[],
            retrieved_candidates=[],
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
        )

    bundle = build_ask_context_bundle(
        user_query=query,
        candidates=candidates,
        tool_results=[],
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
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
            guardrail_outcome=GuardrailOutcome(
                action=GuardrailAction.POSSIBLE_INJECTION_DETECTED,
                applied=True,
                reasons=["all_visible_context_flagged"],
            ),
        )
    tool_decision = _request_tool_call_decision(
        query=query,
        bundle=bundle,
        settings=settings,
        provider_preference=request.provider_preference,
    )
    tool_guardrail = evaluate_tool_call_outcome(
        tool_decision,
        workflow_action=request.action_type,
    )
    tool_results: list[ToolExecutionResult] = []
    if tool_guardrail.applied:
        return _build_retrieval_only_result(
            query=query,
            citations=citations,
            candidates=prompt_candidates,
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
            tool_decision=tool_decision,
            guardrail_outcome=tool_guardrail,
        )

    if tool_decision.requested:
        tool_result = execute_tool_call(
            tool_decision,
            workflow_action=request.action_type,
            settings=settings,
        )
        if not tool_result.ok:
            return _build_retrieval_only_result(
                query=query,
                citations=citations,
                candidates=prompt_candidates,
                retrieval_fallback_used=retrieval_response.fallback_used,
                retrieval_fallback_reason=retrieval_response.fallback_reason,
                tool_decision=tool_decision,
                guardrail_outcome=GuardrailOutcome(
                    action=GuardrailAction.TOOL_RESULT_INSUFFICIENT,
                    applied=True,
                    reasons=[tool_result.error or "tool_failed"],
                ),
            )
        tool_results.append(tool_result)
        if _tool_results_have_safety_flags(tool_results):
            return _build_retrieval_only_result(
                query=query,
                citations=citations,
                candidates=prompt_candidates,
                retrieval_fallback_used=retrieval_response.fallback_used,
                retrieval_fallback_reason=retrieval_response.fallback_reason,
                tool_decision=tool_decision,
                guardrail_outcome=GuardrailOutcome(
                    action=GuardrailAction.POSSIBLE_INJECTION_DETECTED,
                    applied=True,
                    reasons=["tool_result_flagged"],
                ),
            )
        prompt_tool_results = _select_prompt_tool_results(
            tool_results,
            prompt_candidates=prompt_candidates,
        )
        if any(not result.allow_context_reentry for result in tool_results) and not prompt_tool_results:
            return _build_retrieval_only_result(
                query=query,
                citations=citations,
                candidates=prompt_candidates,
                retrieval_fallback_used=retrieval_response.fallback_used,
                retrieval_fallback_reason=retrieval_response.fallback_reason,
                tool_decision=tool_decision,
                guardrail_outcome=GuardrailOutcome(
                    action=GuardrailAction.TOOL_RESULT_INSUFFICIENT,
                    applied=True,
                    reasons=["tool_result_not_prompt_safe"],
                ),
            )
        bundle = build_ask_context_bundle(
            user_query=query,
            candidates=candidates,
            tool_results=prompt_tool_results,
            token_budget=ASK_CONTEXT_TOKEN_BUDGET,
            allowed_tool_names=allowed_tool_names,
        )
        prompt_candidates = _select_prompt_candidates(candidates=candidates, bundle=bundle)
        citations = _build_citations(prompt_candidates)

    generated_answer, provider_target, model_fallback_reason = _try_generate_grounded_answer(
        query=query,
        bundle=bundle,
        settings=settings,
        provider_preference=request.provider_preference,
    )
    if generated_answer is None or provider_target is None:
        return _build_retrieval_only_result(
            query=query,
            citations=citations,
            candidates=prompt_candidates,
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
            model_fallback_used=True,
            model_fallback_reason=model_fallback_reason,
            tool_decision=tool_decision,
        )

    citation_alignment_error = _validate_generated_answer_citations(
        answer=generated_answer,
        candidate_count=len(citations),
    )
    # 这里在 service 层做程序级编号校验，是为了把“模型返回了文本、但引用已经缺失或漂移”
    # 的 bad case 截停在响应落地之前。当前任务只做编号对齐，不假装已经完成语义级 groundedness。
    if citation_alignment_error is not None:
        return _build_retrieval_only_result(
            query=query,
            citations=citations,
            candidates=prompt_candidates,
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
            model_fallback_used=True,
            model_fallback_reason=citation_alignment_error,
            tool_decision=tool_decision,
        )

    final_guardrail = evaluate_final_ask_response(
        answer_text=generated_answer,
        citations=citations,
        bundle=bundle,
        tool_results=tool_results,
    )
    if final_guardrail.applied:
        return _build_retrieval_only_result(
            query=query,
            citations=citations,
            candidates=prompt_candidates,
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
            tool_decision=tool_decision,
            guardrail_outcome=final_guardrail,
        )

    return AskWorkflowResult(
        mode=AskResultMode.GENERATED_ANSWER,
        query=query,
        answer=generated_answer,
        citations=citations,
        retrieved_candidates=prompt_candidates,
        retrieval_fallback_used=retrieval_response.fallback_used,
        retrieval_fallback_reason=retrieval_response.fallback_reason,
        provider_name=provider_target.provider_name,
        model_name=provider_target.model_name,
        tool_call_attempted=tool_decision.requested,
        tool_call_used=tool_decision.tool_name,
        guardrail_action=final_guardrail.action,
    )


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
    tool_decision: ToolCallDecision | None = None,
    guardrail_outcome: GuardrailOutcome | None = None,
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
        tool_call_attempted=tool_decision.requested if tool_decision is not None else False,
        tool_call_used=tool_decision.tool_name if tool_decision is not None else None,
        guardrail_action=guardrail_outcome.action if guardrail_outcome is not None else None,
    )


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
        try:
            payload = {
                "model": provider_target.model_name,
                "temperature": 0,
                "messages": _build_tool_selection_messages(query=query, bundle=bundle),
            }
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
            with urllib_request.urlopen(request, timeout=MODEL_TIMEOUT_SECONDS) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (
            urllib_error.HTTPError,
            urllib_error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ):
            continue

        raw_text = _extract_chat_completion_text(response_payload)
        if not raw_text:
            continue
        return _parse_tool_call_decision(raw_text)

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
    except (urllib_error.HTTPError, urllib_error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ChatProviderError(str(exc)) from exc

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
