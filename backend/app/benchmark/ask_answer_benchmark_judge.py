from __future__ import annotations

from dataclasses import dataclass
import json
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
    model: str


@dataclass(frozen=True)
class JudgeCitation:
    citation_id: str
    source_path: str
    snippet: str


@dataclass(frozen=True)
class JudgeInput:
    user_query: str
    expected_facts: list[str]
    forbidden_claims: list[str]
    answer_text: str
    citations: list[JudgeCitation]


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
        model=model,
    )


def build_judge_messages(judge_input: JudgeInput) -> list[dict[str, str]]:
    case_payload = {
        "prompt_version": JUDGE_PROMPT_VERSION,
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
    payload = {
        "model": provider_config.model,
        "temperature": 0,
        "messages": build_judge_messages(judge_input),
    }
    request = urllib_request.Request(
        _build_chat_completions_url(provider_config.base_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=_build_headers(provider_config.api_key),
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=JUDGE_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        return build_non_scored_judge_score("timeout", str(exc) or "timeout")
    except (
        urllib_error.HTTPError,
        urllib_error.URLError,
        OSError,
        json.JSONDecodeError,
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
