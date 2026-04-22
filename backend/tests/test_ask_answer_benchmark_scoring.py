from __future__ import annotations

import unittest

from app.benchmark.ask_answer_benchmark_scoring import (
    aggregate_answer_benchmark_variant_scores,
    score_answer_benchmark_case,
)
from app.benchmark.ask_dataset import AskBenchmarkCase, AskBenchmarkLocator
from app.contracts.workflow import AskResultMode, AskWorkflowResult


def _locator() -> AskBenchmarkLocator:
    return AskBenchmarkLocator(
        note_path="Notes/Alpha.md",
        heading_path="Summary",
        excerpt_anchor="alpha evidence",
    )


def _case(
    *,
    case_id: str,
    expected_facts: list[str],
    forbidden_claims: list[str] | None = None,
    allow_retrieval_only: bool = False,
    should_generate_answer: bool = True,
    allow_tool: bool = False,
    expected_tool_names: list[str] | None = None,
) -> AskBenchmarkCase:
    return AskBenchmarkCase(
        case_id=case_id,
        bucket="single_hop",
        user_query=f"query for {case_id}",
        source_origin="fixture",
        expected_relevant_paths=["Notes/Alpha.md"],
        expected_relevant_locators=[_locator()],
        expected_facts=expected_facts,
        forbidden_claims=forbidden_claims or [],
        allow_tool=allow_tool,
        expected_tool_names=expected_tool_names or [],
        allow_retrieval_only=allow_retrieval_only,
        should_generate_answer=should_generate_answer,
        review_status="approved",
        review_notes="ready",
    )


def _ask_result(
    *,
    mode: AskResultMode,
    answer: str,
    tool_call_attempted: bool = False,
    tool_call_used: str | None = None,
) -> AskWorkflowResult:
    return AskWorkflowResult(
        mode=mode,
        query="query",
        answer=answer,
        tool_call_attempted=tool_call_attempted,
        tool_call_used=tool_call_used,
    )


class AskAnswerBenchmarkScoringTest(unittest.TestCase):
    def test_score_case_marks_complete_fact_coverage_as_correct(self) -> None:
        case = _case(
            case_id="case-correct",
            expected_facts=["Alpha 已完成", "Beta 已同步"],
        )
        ask_result = _ask_result(
            mode=AskResultMode.GENERATED_ANSWER,
            answer="Alpha 已完成，并且 Beta 已同步。",
        )

        score = score_answer_benchmark_case(case=case, ask_result=ask_result, latency_ms=420)

        self.assertEqual(score.verdict, "correct")
        self.assertEqual(score.correctness_points, 1.0)
        self.assertFalse(score.unsupported_claim)
        self.assertEqual(score.matched_expected_facts, ["Alpha 已完成", "Beta 已同步"])
        self.assertEqual(score.missed_expected_facts, [])
        self.assertEqual(score.forbidden_claim_hits, [])

    def test_score_case_marks_partial_fact_coverage_as_partial(self) -> None:
        case = _case(
            case_id="case-partial",
            expected_facts=["Alpha 已完成", "Beta 已同步"],
        )
        ask_result = _ask_result(
            mode=AskResultMode.GENERATED_ANSWER,
            answer="Alpha 已完成。",
        )

        score = score_answer_benchmark_case(case=case, ask_result=ask_result, latency_ms=240)

        self.assertEqual(score.verdict, "partial")
        self.assertEqual(score.correctness_points, 0.5)
        self.assertFalse(score.unsupported_claim)
        self.assertEqual(score.matched_expected_facts, ["Alpha 已完成"])
        self.assertEqual(score.missed_expected_facts, ["Beta 已同步"])
        self.assertEqual(score.forbidden_claim_hits, [])

    def test_score_case_marks_forbidden_claim_as_unsupported(self) -> None:
        case = _case(
            case_id="case-forbidden",
            expected_facts=["Alpha 已完成"],
            forbidden_claims=["Beta 已部署"],
        )
        ask_result = _ask_result(
            mode=AskResultMode.GENERATED_ANSWER,
            answer="Alpha 已完成，但 Beta 已部署。",
        )

        score = score_answer_benchmark_case(case=case, ask_result=ask_result, latency_ms=420)

        self.assertEqual(score.verdict, "incorrect")
        self.assertEqual(score.correctness_points, 0.0)
        self.assertTrue(score.unsupported_claim)
        self.assertEqual(score.matched_expected_facts, ["Alpha 已完成"])
        self.assertEqual(score.missed_expected_facts, [])
        self.assertEqual(score.forbidden_claim_hits, ["Beta 已部署"])

    def test_score_case_treats_retrieval_only_as_compliant_fallback_when_allowed(self) -> None:
        case = _case(
            case_id="case-fallback",
            expected_facts=["Alpha 已完成"],
            allow_retrieval_only=True,
            should_generate_answer=False,
        )
        ask_result = _ask_result(
            mode=AskResultMode.RETRIEVAL_ONLY,
            answer="",
        )

        score = score_answer_benchmark_case(case=case, ask_result=ask_result, latency_ms=180)

        self.assertEqual(score.verdict, "partial")
        self.assertEqual(score.correctness_points, 0.5)
        self.assertFalse(score.unsupported_claim)
        self.assertEqual(score.matched_expected_facts, [])
        self.assertEqual(score.missed_expected_facts, ["Alpha 已完成"])
        self.assertEqual(score.forbidden_claim_hits, [])

    def test_aggregate_variant_scores_computes_core_and_tool_metrics(self) -> None:
        scores = [
            score_answer_benchmark_case(
                case=_case(case_id="case-1", expected_facts=["Alpha 已完成"]),
                ask_result=_ask_result(
                    mode=AskResultMode.GENERATED_ANSWER,
                    answer="Alpha 已完成。",
                ),
                latency_ms=100,
            ),
            score_answer_benchmark_case(
                case=_case(case_id="case-2", expected_facts=["Alpha 已完成", "Beta 已同步"]),
                ask_result=_ask_result(
                    mode=AskResultMode.GENERATED_ANSWER,
                    answer="Alpha 已完成。",
                ),
                latency_ms=200,
            ),
            score_answer_benchmark_case(
                case=_case(
                    case_id="case-3",
                    expected_facts=["Alpha 已完成"],
                    allow_retrieval_only=True,
                    should_generate_answer=False,
                ),
                ask_result=_ask_result(
                    mode=AskResultMode.RETRIEVAL_ONLY,
                    answer="",
                ),
                latency_ms=300,
            ),
            score_answer_benchmark_case(
                case=_case(
                    case_id="case-4",
                    expected_facts=["Alpha 已完成"],
                    allow_tool=True,
                    expected_tool_names=["tool.alpha"],
                ),
                ask_result=_ask_result(
                    mode=AskResultMode.GENERATED_ANSWER,
                    answer="Alpha 已完成。",
                    tool_call_attempted=True,
                    tool_call_used="tool.alpha",
                ),
                latency_ms=400,
            ),
        ]

        aggregate = aggregate_answer_benchmark_variant_scores(variant_id="hybrid", case_scores=scores)

        self.assertEqual(aggregate.variant_id, "hybrid")
        self.assertEqual(aggregate.case_count, 4)
        self.assertEqual(aggregate.answer_correctness, 0.75)
        self.assertEqual(aggregate.unsupported_claim_rate, 0.0)
        self.assertEqual(aggregate.generated_answer_rate, 0.75)
        self.assertEqual(aggregate.retrieval_only_rate, 0.25)
        self.assertEqual(aggregate.p50_latency_ms, 250.0)
        self.assertEqual(aggregate.p95_latency_ms, 400.0)
        self.assertEqual(aggregate.tool_trigger_rate, 1.0)
        self.assertEqual(aggregate.expected_tool_hit_rate, 1.0)
        self.assertEqual(aggregate.tool_case_answer_correctness, 1.0)


if __name__ == "__main__":
    unittest.main()
