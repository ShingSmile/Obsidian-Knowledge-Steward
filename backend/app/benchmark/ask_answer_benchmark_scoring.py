from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from statistics import median
import re
from typing import Sequence

from app.benchmark.ask_dataset import AskBenchmarkCase
from app.contracts.workflow import AskResultMode, AskWorkflowResult


_VERDICT_POINTS: dict[str, float] = {
    "correct": 1.0,
    "partial": 0.5,
    "incorrect": 0.0,
}


@dataclass(frozen=True, slots=True)
class AskAnswerBenchmarkCaseScore:
    case_id: str
    variant_id: str
    verdict: str
    correctness_points: float
    unsupported_claim: bool
    matched_expected_facts: list[str]
    missed_expected_facts: list[str]
    forbidden_claim_hits: list[str]
    latency_ms: int
    answer_mode: str
    tool_call_attempted: bool
    tool_call_used: str | None
    allow_tool: bool
    expected_tool_names: list[str]


@dataclass(frozen=True, slots=True)
class AskAnswerBenchmarkVariantAggregate:
    variant_id: str
    case_count: int
    answer_correctness: float
    unsupported_claim_rate: float
    generated_answer_rate: float
    retrieval_only_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    tool_trigger_rate: float
    expected_tool_hit_rate: float
    tool_case_answer_correctness: float


def score_answer_benchmark_case(
    *,
    case: AskBenchmarkCase,
    ask_result: AskWorkflowResult,
    latency_ms: int,
    variant_id: str = "unknown",
) -> AskAnswerBenchmarkCaseScore:
    answer_text = ask_result.answer or ""
    matched_expected_facts = [
        expected_fact
        for expected_fact in case.expected_facts
        if _contains_normalized_phrase(answer_text, expected_fact)
    ]
    missed_expected_facts = [
        expected_fact
        for expected_fact in case.expected_facts
        if expected_fact not in matched_expected_facts
    ]
    forbidden_claim_hits = [
        forbidden_claim
        for forbidden_claim in case.forbidden_claims
        if _contains_normalized_phrase(answer_text, forbidden_claim)
    ]

    unsupported_claim = bool(forbidden_claim_hits)
    if unsupported_claim:
        verdict = "incorrect"
    elif ask_result.mode is AskResultMode.GENERATED_ANSWER:
        if len(matched_expected_facts) == len(case.expected_facts):
            verdict = "correct"
        elif matched_expected_facts:
            verdict = "partial"
        else:
            verdict = "incorrect"
    elif ask_result.mode in (AskResultMode.RETRIEVAL_ONLY, AskResultMode.NO_HITS):
        if case.allow_retrieval_only and not case.should_generate_answer:
            verdict = "partial"
        else:
            verdict = "incorrect"
    else:
        verdict = "incorrect"

    return AskAnswerBenchmarkCaseScore(
        case_id=case.case_id,
        variant_id=variant_id,
        verdict=verdict,
        correctness_points=_VERDICT_POINTS[verdict],
        unsupported_claim=unsupported_claim,
        matched_expected_facts=matched_expected_facts,
        missed_expected_facts=missed_expected_facts,
        forbidden_claim_hits=forbidden_claim_hits,
        latency_ms=latency_ms,
        answer_mode=ask_result.mode.value,
        tool_call_attempted=ask_result.tool_call_attempted,
        tool_call_used=ask_result.tool_call_used,
        allow_tool=case.allow_tool,
        expected_tool_names=list(case.expected_tool_names),
    )


def aggregate_answer_benchmark_variant_scores(
    *,
    variant_id: str,
    case_scores: Sequence[AskAnswerBenchmarkCaseScore],
) -> AskAnswerBenchmarkVariantAggregate:
    scores = list(case_scores)
    case_count = len(scores)
    if case_count == 0:
        return AskAnswerBenchmarkVariantAggregate(
            variant_id=variant_id,
            case_count=0,
            answer_correctness=0.0,
            unsupported_claim_rate=0.0,
            generated_answer_rate=0.0,
            retrieval_only_rate=0.0,
            p50_latency_ms=0.0,
            p95_latency_ms=0.0,
            tool_trigger_rate=0.0,
            expected_tool_hit_rate=0.0,
            tool_case_answer_correctness=0.0,
        )

    answer_correctness = _rounded_ratio(
        sum(score.correctness_points for score in scores),
        case_count,
    )
    unsupported_claim_rate = _rounded_ratio(
        sum(1 for score in scores if score.unsupported_claim),
        case_count,
    )
    generated_answer_rate = _rounded_ratio(
        sum(1 for score in scores if score.answer_mode == AskResultMode.GENERATED_ANSWER.value),
        case_count,
    )
    retrieval_only_rate = _rounded_ratio(
        sum(1 for score in scores if score.answer_mode == AskResultMode.RETRIEVAL_ONLY.value),
        case_count,
    )

    latencies = sorted(score.latency_ms for score in scores)
    p50_latency_ms = float(median(latencies))
    p95_latency_ms = float(_nearest_rank_percentile(latencies, percentile=0.95))

    tool_scores = [score for score in scores if score.allow_tool]
    tool_trigger_rate, expected_tool_hit_rate, tool_case_answer_correctness = _aggregate_tool_subset_metrics(
        tool_scores
    )

    return AskAnswerBenchmarkVariantAggregate(
        variant_id=variant_id,
        case_count=case_count,
        answer_correctness=answer_correctness,
        unsupported_claim_rate=unsupported_claim_rate,
        generated_answer_rate=generated_answer_rate,
        retrieval_only_rate=retrieval_only_rate,
        p50_latency_ms=p50_latency_ms,
        p95_latency_ms=p95_latency_ms,
        tool_trigger_rate=tool_trigger_rate,
        expected_tool_hit_rate=expected_tool_hit_rate,
        tool_case_answer_correctness=tool_case_answer_correctness,
    )


def _aggregate_tool_subset_metrics(
    tool_scores: Sequence[AskAnswerBenchmarkCaseScore],
) -> tuple[float, float, float]:
    tool_case_count = len(tool_scores)
    if tool_case_count == 0:
        return 0.0, 0.0, 0.0

    tool_trigger_rate = _rounded_ratio(
        sum(1 for score in tool_scores if score.tool_call_attempted),
        tool_case_count,
    )
    expected_tool_hit_rate = _rounded_ratio(
        sum(
            1
            for score in tool_scores
            if score.tool_call_used is not None and score.tool_call_used in score.expected_tool_names
        ),
        tool_case_count,
    )
    tool_case_answer_correctness = _rounded_ratio(
        sum(score.correctness_points for score in tool_scores),
        tool_case_count,
    )
    return tool_trigger_rate, expected_tool_hit_rate, tool_case_answer_correctness


def _contains_normalized_phrase(text: str, phrase: str) -> bool:
    normalized_text = _normalize_text(text)
    normalized_phrase = _normalize_text(phrase)
    return bool(normalized_phrase) and normalized_phrase in normalized_text


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold().strip()


def _nearest_rank_percentile(values: Sequence[int], *, percentile: float) -> int:
    if not values:
        return 0
    rank = ceil(percentile * len(values))
    index = max(0, min(rank - 1, len(values) - 1))
    return values[index]


def _rounded_ratio(numerator: float, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
