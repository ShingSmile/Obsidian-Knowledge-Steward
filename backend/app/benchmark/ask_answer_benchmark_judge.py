from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Sequence
from urllib import error as urllib_error
from urllib import request as urllib_request


DEFAULT_JUDGE_MODEL = "qwen3.6-max-preview"
JUDGE_PROMPT_VERSION = "2026-04-25-answer-judge-v1"
JUDGE_TIMEOUT_SECONDS = 30
JUDGE_VERDICT_POINTS = {
    "correct": 1.0,
    "mostly_correct": 0.75,
    "partial": 0.5,
    "mostly_incorrect": 0.25,
    "incorrect": 0.0,
}


@dataclass(frozen=True)
class JudgeConfigOverrides:
    provider_name: str = ""
    base_url: str = ""
    api_key: str = ""
    model: str = ""


@dataclass(frozen=True)
class JudgeProviderConfig:
    provider_name: str
    base_url: str
    api_key: str
    model_name: str


@dataclass(frozen=True)
class JudgeCitation:
    citation_id: str
    source_path: str
    snippet: str


@dataclass(frozen=True)
class JudgeInput:
    case_id: str
    variant_id: str
    user_query: str
    expected_facts: list[str]
    forbidden_claims: list[str]
    answer_text: str
    citations: list[JudgeCitation]
    ask_result_mode: str
    runtime_faithfulness: object | None


@dataclass(frozen=True)
class JudgeScore:
    judge_status: str
    verdict: str | None
    correctness_points: float | None
    matched_facts: list[str]
    missed_facts: list[str]
    unsupported_claims: list[str]
    reason: str | None
    error_reason: str | None = None
    raw_response_excerpt: str | None = None


def judge_score_to_payload(score: JudgeScore) -> dict[str, object]:
    return {
        "judge_status": score.judge_status,
        "verdict": score.verdict,
        "correctness_points": score.correctness_points,
        "matched_facts": list(score.matched_facts),
        "missed_facts": list(score.missed_facts),
        "unsupported_claims": list(score.unsupported_claims),
        "reason": score.reason,
        "error_reason": score.error_reason,
        "raw_response_excerpt": score.raw_response_excerpt,
    }


def aggregate_judge_scores(scores: Sequence[JudgeScore]) -> dict[str, object]:
    judge_case_count = len(scores)
    if judge_case_count == 0:
        return {
            "judge_case_count": 0,
            "judge_scored_count": 0,
            "judge_failed_count": 0,
            "judge_answer_correctness": 0.0,
            "judge_unsupported_claim_rate": 0.0,
            "judge_scored_rate": 0.0,
            "judge_failed_rate": 0.0,
        }

    scored = [score for score in scores if _has_numeric_correctness_points(score)]
    judge_scored_count = len(scored)
    judge_failed_count = judge_case_count - judge_scored_count

    if judge_scored_count == 0:
        judge_answer_correctness = 0.0
        judge_unsupported_claim_rate = 0.0
    else:
        judge_answer_correctness = round(
            sum(score.correctness_points or 0.0 for score in scored) / judge_scored_count,
            4,
        )
        judge_unsupported_claim_rate = round(
            sum(1 for score in scored if score.unsupported_claims) / judge_scored_count,
            4,
        )

    return {
        "judge_case_count": judge_case_count,
        "judge_scored_count": judge_scored_count,
        "judge_failed_count": judge_failed_count,
        "judge_answer_correctness": judge_answer_correctness,
        "judge_unsupported_claim_rate": judge_unsupported_claim_rate,
        "judge_scored_rate": round(judge_scored_count / judge_case_count, 4),
        "judge_failed_rate": round(judge_failed_count / judge_case_count, 4),
    }


def resolve_judge_provider_config(settings: object, overrides: JudgeConfigOverrides) -> JudgeProviderConfig:
    provider_name = (
        overrides.provider_name
        or getattr(settings, "judge_provider_name", "")
        or getattr(settings, "cloud_provider_name", "")
    )
    base_url = overrides.base_url or getattr(settings, "judge_base_url", "") or getattr(settings, "cloud_base_url", "")
    api_key = overrides.api_key or getattr(settings, "judge_api_key", "") or getattr(settings, "cloud_api_key", "")
    model = overrides.model or getattr(settings, "judge_model", "") or DEFAULT_JUDGE_MODEL
    return JudgeProviderConfig(
        provider_name=provider_name,
        base_url=base_url,
        api_key=api_key,
        model_name=model,
    )


def _has_numeric_correctness_points(score: JudgeScore) -> bool:
    return (
        score.judge_status == "scored"
        and isinstance(score.correctness_points, (int, float))
        and not isinstance(score.correctness_points, bool)
    )


def build_judge_messages(judge_input: JudgeInput) -> list[dict[str, str]]:
    case_payload = {
        "prompt_version": JUDGE_PROMPT_VERSION,
        "case_id": judge_input.case_id,
        "variant_id": judge_input.variant_id,
        "user_query": judge_input.user_query,
        "expected_facts": judge_input.expected_facts,
        "forbidden_claims": judge_input.forbidden_claims,
        "answer_text": judge_input.answer_text,
        "citations": [
            {
                "citation_id": citation.citation_id,
                "source_path": citation.source_path,
                "snippet": citation.snippet,
            }
            for citation in judge_input.citations
        ],
        "ask_result_mode": judge_input.ask_result_mode,
        "runtime_faithfulness": _json_compatible(judge_input.runtime_faithfulness),
    }
    return [
        {
            "role": "system",
            "content": (
                "You are a strict answer benchmark judge. Evaluate only the supplied case data. "
                "Return one JSON object with verdict, matched_facts, missed_facts, "
                "unsupported_claims, and reason. The verdict must be one of: "
                f"{', '.join(JUDGE_VERDICT_POINTS)}."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(case_payload, ensure_ascii=False, indent=2),
        },
    ]


def parse_judge_response_payload(payload: str) -> JudgeScore:
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return build_non_scored_judge_score(
            "parse_error",
            "invalid_json",
            raw_response_excerpt=_excerpt(payload),
        )

    if not isinstance(parsed, dict):
        return build_non_scored_judge_score("invalid_schema", "response_not_object")

    verdict = parsed.get("verdict")
    matched_facts = parsed.get("matched_facts")
    missed_facts = parsed.get("missed_facts")
    unsupported_claims = parsed.get("unsupported_claims")
    reason = parsed.get("reason")

    if not isinstance(verdict, str) or verdict not in JUDGE_VERDICT_POINTS:
        return build_non_scored_judge_score("invalid_schema", "invalid_verdict")
    if not isinstance(matched_facts, list):
        return build_non_scored_judge_score("invalid_schema", "invalid_matched_facts")
    if not isinstance(missed_facts, list):
        return build_non_scored_judge_score("invalid_schema", "invalid_missed_facts")
    if not isinstance(unsupported_claims, list):
        return build_non_scored_judge_score("invalid_schema", "invalid_unsupported_claims")
    if not _is_string_list(matched_facts):
        return build_non_scored_judge_score("invalid_schema", "invalid_matched_facts")
    if not _is_string_list(missed_facts):
        return build_non_scored_judge_score("invalid_schema", "invalid_missed_facts")
    if not _is_string_list(unsupported_claims):
        return build_non_scored_judge_score("invalid_schema", "invalid_unsupported_claims")
    if not isinstance(reason, str) or not reason.strip():
        return build_non_scored_judge_score("invalid_schema", "invalid_reason")

    return JudgeScore(
        judge_status="scored",
        verdict=verdict,
        correctness_points=JUDGE_VERDICT_POINTS[verdict],
        matched_facts=matched_facts,
        missed_facts=missed_facts,
        unsupported_claims=unsupported_claims,
        reason=reason.strip(),
    )


def build_non_scored_judge_score(
    status: str,
    error_reason: str,
    raw_response_excerpt: str | None = None,
) -> JudgeScore:
    return JudgeScore(
        judge_status=status,
        verdict=None,
        correctness_points=None,
        matched_facts=[],
        missed_facts=[],
        unsupported_claims=[],
        reason=None,
        error_reason=error_reason,
        raw_response_excerpt=raw_response_excerpt,
    )


def score_answer_with_judge(judge_input: JudgeInput, provider_config: JudgeProviderConfig) -> JudgeScore:
    if not provider_config.base_url.strip():
        return build_non_scored_judge_score("provider_unavailable", "missing_judge_base_url")

    payload = {
        "model": provider_config.model_name,
        "temperature": 0,
        "messages": build_judge_messages(judge_input),
    }

    try:
        request = urllib_request.Request(
            _build_chat_completions_url(provider_config.base_url),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=_build_headers(provider_config.api_key),
            method="POST",
        )
        with urllib_request.urlopen(request, timeout=JUDGE_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        return build_non_scored_judge_score("timeout", str(exc) or "timeout")
    except (
        urllib_error.HTTPError,
        urllib_error.URLError,
        OSError,
        json.JSONDecodeError,
        UnicodeError,
        ValueError,
    ) as exc:
        return build_non_scored_judge_score("provider_unavailable", str(exc) or "provider_error")

    response_text = _extract_chat_completion_text(response_payload)
    if response_text is None:
        return build_non_scored_judge_score("provider_unavailable", "invalid_chat_completion_response")

    return parse_judge_response_payload(response_text)


def _build_headers(api_key: str) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _build_chat_completions_url(base_url: str) -> str:
    normalized_base_url = base_url.rstrip("/")
    if normalized_base_url.endswith("/chat/completions"):
        return normalized_base_url
    if normalized_base_url.endswith("/v1"):
        return f"{normalized_base_url}/chat/completions"
    return f"{normalized_base_url}/v1/chat/completions"


def _extract_chat_completion_text(response_payload: object) -> str | None:
    if not isinstance(response_payload, dict):
        return None
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return None

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return None

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
        if text_parts:
            return "\n".join(text_parts).strip()
    return None


def _excerpt(value: str, limit: int = 500) -> str:
    return value.strip()[:limit]


def _is_string_list(value: list[object]) -> bool:
    return all(isinstance(item, str) for item in value)


def _json_compatible(value: object | None) -> object | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    return value
