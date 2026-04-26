from __future__ import annotations

import json
import inspect
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime
from unittest.mock import Mock, patch

from app.benchmark.ask_answer_benchmark_judge import (
    JUDGE_PROMPT_VERSION,
    JudgeInput,
    JudgeProviderConfig,
    JudgeScore,
)
from app.benchmark.ask_answer_benchmark_variants import (
    ANSWER_BENCHMARK_VARIANTS,
    AskAnswerBenchmarkVariant,
    build_answer_benchmark_metadata,
    load_answer_benchmark_smoke_case_ids,
    resolve_answer_benchmark_prompt_version,
)
from app.benchmark.ask_dataset import load_ask_benchmark_dataset
from app.config import get_settings
from app.contracts.workflow import AskCitation, AskResultMode, GuardrailAction, RuntimeFaithfulnessSignal

from app.benchmark.ask_answer_benchmark import run_ask_answer_benchmark


def _fake_execution(
    *,
    provider_name: str = "openai-compatible",
    model_name: str = "qwen3.6-flash-2026-04-16",
    ask_result_mode: AskResultMode = AskResultMode.GENERATED_ANSWER,
    answer: str = "answer text",
    citations: list[AskCitation] | None = None,
    runtime_faithfulness: RuntimeFaithfulnessSignal | None = None,
) -> Mock:
    ask_result = Mock(
        mode=ask_result_mode,
        answer=answer,
        citations=citations or [],
        retrieved_candidates=[],
        retrieval_fallback_used=False,
        retrieval_fallback_reason=None,
        model_fallback_used=False,
        model_fallback_reason=None,
        provider_name=provider_name,
        model_name=model_name,
        tool_call_attempted=False,
        tool_call_rounds=0,
        tool_call_used=None,
        guardrail_action=GuardrailAction.ALLOW,
        runtime_faithfulness=runtime_faithfulness or RuntimeFaithfulnessSignal(),
    )
    return Mock(ask_result=ask_result)


def _judge_config() -> JudgeProviderConfig:
    return JudgeProviderConfig(
        provider_name="judge-provider",
        base_url="https://judge.example",
        api_key="judge-key",
        model_name="judge-model",
    )


def _scored_judge_score() -> JudgeScore:
    return JudgeScore(
        judge_status="scored",
        verdict="mostly_correct",
        correctness_points=0.75,
        matched_facts=["matched fact"],
        missed_facts=["missed fact"],
        unsupported_claims=[],
        reason="The answer is mostly correct.",
    )


def _non_scored_judge_score() -> JudgeScore:
    return JudgeScore(
        judge_status="parse_error",
        verdict=None,
        correctness_points=None,
        matched_facts=[],
        missed_facts=[],
        unsupported_claims=[],
        reason=None,
        error_reason="invalid_json",
        raw_response_excerpt="{not json",
    )


def _call_matrix(call_args_list: list[tuple[object, dict[str, object]]]) -> list[tuple[str, str]]:
    return [
        (
            call.args[0].metadata["case_id"],
            call.args[0].metadata["variant_id"],
        )
        for call in call_args_list
    ]


def _thread_ids(call_args_list: list[tuple[object, dict[str, object]]]) -> list[str]:
    return [call.kwargs["thread_id"] for call in call_args_list]


class AskAnswerBenchmarkContractTests(unittest.TestCase):
    def test_load_smoke_case_ids_returns_fixed_unique_ten_case_subset(self) -> None:
        case_ids = load_answer_benchmark_smoke_case_ids()
        self.assertEqual(
            case_ids,
            (
                "ask_case_001",
                "ask_case_002",
                "ask_case_003",
                "ask_case_004",
                "ask_case_005",
                "ask_case_006",
                "ask_case_007",
                "ask_case_008",
                "ask_case_009",
                "ask_case_010",
            ),
        )

    def test_variant_matrix_matches_task_059_ablation_contract(self) -> None:
        self.assertEqual(
            [
                (
                    variant.variant_id,
                    variant.context_assembly_enabled,
                    variant.runtime_faithfulness_gate_enabled,
                )
                for variant in ANSWER_BENCHMARK_VARIANTS
            ],
            [
                ("hybrid", False, False),
                ("hybrid_assembly", True, False),
                ("hybrid_assembly_gate", True, True),
            ],
        )

    def test_prompt_version_is_non_empty_and_stable(self) -> None:
        prompt_version = resolve_answer_benchmark_prompt_version()
        self.assertEqual(
            prompt_version,
            "tool:2026-04-22-tool-v1|answer:2026-04-22-grounded-v1",
        )

    def test_load_smoke_case_ids_rejects_wrong_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "smoke.json"
            path.write_text(
                json.dumps({"version": 1, "case_ids": ["ask_case_001"]}, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_answer_benchmark_smoke_case_ids(path)

    def test_load_smoke_case_ids_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "smoke.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "case_ids": [
                            "ask_case_001",
                            "ask_case_002",
                            "ask_case_003",
                            "ask_case_004",
                            "ask_case_005",
                            "ask_case_006",
                            "ask_case_007",
                            "ask_case_008",
                            "ask_case_009",
                            "ask_case_009",
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_answer_benchmark_smoke_case_ids(path)

    def test_load_smoke_case_ids_rejects_empty_or_whitespace_only_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "smoke.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "case_ids": [
                            "ask_case_001",
                            "ask_case_002",
                            "ask_case_003",
                            "ask_case_004",
                            "ask_case_005",
                            "ask_case_006",
                            "ask_case_007",
                            "ask_case_008",
                            "ask_case_009",
                            "   ",
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_answer_benchmark_smoke_case_ids(path)

    def test_load_smoke_case_ids_rejects_non_list_or_wrong_version_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            non_list_path = temp_dir_path / "non_list.json"
            non_list_path.write_text(
                json.dumps({"version": 1, "case_ids": "ask_case_001"}, ensure_ascii=False),
                encoding="utf-8",
            )
            wrong_version_path = temp_dir_path / "wrong_version.json"
            wrong_version_path.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "case_ids": [
                            "ask_case_001",
                            "ask_case_002",
                            "ask_case_003",
                            "ask_case_004",
                            "ask_case_005",
                            "ask_case_006",
                            "ask_case_007",
                            "ask_case_008",
                            "ask_case_009",
                            "ask_case_010",
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_answer_benchmark_smoke_case_ids(non_list_path)
            with self.assertRaises(ValueError):
                load_answer_benchmark_smoke_case_ids(wrong_version_path)

    def test_build_answer_benchmark_metadata_returns_expected_shape(self) -> None:
        variant = AskAnswerBenchmarkVariant(
            variant_id="hybrid_assembly_gate",
            context_assembly_enabled=True,
            runtime_faithfulness_gate_enabled=True,
        )

        self.assertEqual(
            build_answer_benchmark_metadata(
                case_id="ask_case_001",
                variant=variant,
                smoke_subset=False,
                allow_tool=False,
            ),
            {
                "benchmark_kind": "ask_answer",
                "case_id": "ask_case_001",
                "variant_id": "hybrid_assembly_gate",
                "context_assembly_enabled": True,
                "runtime_faithfulness_gate_enabled": True,
                "smoke_subset": False,
                "prompt_version": "tool:2026-04-22-tool-v1|answer:2026-04-22-grounded-v1",
                "max_tool_rounds": 0,
            },
        )

    def test_build_answer_benchmark_metadata_requires_explicit_smoke_subset(self) -> None:
        self.assertIs(
            inspect.signature(build_answer_benchmark_metadata).parameters["smoke_subset"].default,
            inspect._empty,
        )

    def test_build_answer_benchmark_metadata_requires_explicit_tool_policy(self) -> None:
        self.assertIs(
            inspect.signature(build_answer_benchmark_metadata).parameters["allow_tool"].default,
            inspect._empty,
        )

    def test_build_answer_benchmark_metadata_does_not_disable_tool_allowed_cases(self) -> None:
        metadata = build_answer_benchmark_metadata(
            case_id="ask_case_tool",
            variant=ANSWER_BENCHMARK_VARIANTS[0],
            smoke_subset=False,
            allow_tool=True,
        )

        self.assertNotIn("max_tool_rounds", metadata)


class AskAnswerBenchmarkOrchestrationTests(unittest.TestCase):
    def test_run_ask_answer_benchmark_smoke_selects_ten_cases_and_writes_artifact(self) -> None:
        settings = get_settings()
        dataset = load_ask_benchmark_dataset()

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "answer-benchmark.json"
            with patch(
                "app.benchmark.ask_answer_benchmark.load_ask_benchmark_dataset",
                return_value=dataset,
            ):
                with patch(
                    "app.benchmark.ask_answer_benchmark.invoke_ask_graph",
                    side_effect=lambda request, **kwargs: _fake_execution(),
                ) as mocked_invoke:
                    with patch(
                        "app.benchmark.ask_answer_benchmark._get_git_commit",
                        return_value="abc1234",
                    ):
                        with patch(
                            "app.benchmark.ask_answer_benchmark._is_worktree_dirty",
                            return_value=False,
                        ):
                            with patch(
                                "app.benchmark.ask_answer_benchmark.datetime",
                            ) as mocked_datetime:
                                mocked_datetime.now.return_value = datetime(2026, 4, 22, 12, 30, 45)
                                result = run_ask_answer_benchmark(
                                    settings=settings,
                                    mode="smoke",
                                    dataset_path=Path(tmp_dir) / "dataset.json",
                                    output_path=output_path,
                                )

            self.assertEqual(result["benchmark_mode"], "smoke")
            self.assertEqual(len(result["selected_case_ids"]), 10)
            self.assertEqual(result["selected_case_ids"], list(load_answer_benchmark_smoke_case_ids()))
            self.assertEqual(mocked_invoke.call_count, 30)
            expected_case_variant_matrix = [
                (case_id, variant.variant_id)
                for case_id in result["selected_case_ids"]
                for variant in ANSWER_BENCHMARK_VARIANTS
            ]
            self.assertEqual(_call_matrix(mocked_invoke.call_args_list), expected_case_variant_matrix)
            thread_ids = _thread_ids(mocked_invoke.call_args_list)
            self.assertEqual(len(thread_ids), len(set(thread_ids)))
            first_request = mocked_invoke.call_args_list[0].args[0]
            first_kwargs = mocked_invoke.call_args_list[0].kwargs
            self.assertEqual(first_request.provider_preference, "cloud")
            self.assertEqual(first_request.metadata["max_tool_rounds"], 0)
            self.assertEqual(first_kwargs["settings"].cloud_chat_model, "qwen3.6-flash-2026-04-16")
            self.assertEqual(first_kwargs["settings"].local_chat_model, "")
            self.assertTrue(
                first_kwargs["thread_id"].startswith("task059_ask_case_001_hybrid_")
            )
            self.assertTrue(output_path.exists())
            self.assertEqual(result["provider_name"], "openai-compatible")
            self.assertEqual(result["model_name"], "qwen3.6-flash-2026-04-16")
            self.assertEqual(result["prompt_version"], resolve_answer_benchmark_prompt_version())
            self.assertEqual(result["git_commit"], "abc1234")
            self.assertFalse(result["worktree_dirty"])
            self.assertEqual(result["benchmark_kind"], "ask_answer")
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(len(result["case_variant_records"]), 30)
            self.assertEqual(result["smoke_subset_version"], 1)
            self.assertNotIn("tool_allowed", result["variant_aggregates"]["hybrid"])
            self.assertEqual(result["artifact_metadata"]["provider_name"], "openai-compatible")
            self.assertEqual(result["artifact_metadata"]["model_name"], "qwen3.6-flash-2026-04-16")
            self.assertEqual(
                result["artifact_metadata"]["prompt_version"],
                resolve_answer_benchmark_prompt_version(),
            )
            self.assertEqual(result["artifact_metadata"]["git_commit"], "abc1234")
            self.assertEqual(result["artifact_metadata"]["benchmark_mode"], "smoke")
            self.assertEqual(result["artifact_metadata"]["selected_case_ids"], result["selected_case_ids"])

    def test_run_ask_answer_benchmark_judge_disabled_keeps_rule_scores_without_judge_payloads(self) -> None:
        settings = get_settings()
        dataset = load_ask_benchmark_dataset()

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "answer-benchmark.json"
            with patch(
                "app.benchmark.ask_answer_benchmark.load_ask_benchmark_dataset",
                return_value=dataset,
            ):
                with patch(
                    "app.benchmark.ask_answer_benchmark.invoke_ask_graph",
                    side_effect=lambda request, **kwargs: _fake_execution(),
                ):
                    with patch(
                        "app.benchmark.ask_answer_benchmark._get_git_commit",
                        return_value="abc1234",
                    ):
                        with patch(
                            "app.benchmark.ask_answer_benchmark._is_worktree_dirty",
                            return_value=False,
                        ):
                            result = run_ask_answer_benchmark(
                                settings=settings,
                                mode="smoke",
                                dataset_path=Path(tmp_dir) / "dataset.json",
                                output_path=output_path,
                                judge_enabled=False,
                            )

        self.assertEqual(result["judge_run_metadata"], {"judge_enabled": False})
        first_record = result["case_variant_records"][0]
        self.assertIn("rule_score", first_record)
        self.assertNotIn("judge_score", first_record)
        self.assertEqual(first_record["rule_score"]["verdict"], first_record["final_verdict"])
        self.assertEqual(
            first_record["rule_score"]["matched_expected_facts"],
            first_record["matched_expected_facts"],
        )
        self.assertIn("missed_expected_facts", first_record)
        self.assertIn("forbidden_claim_hits", first_record)
        self.assertIn("final_verdict", first_record)

        aggregate = result["variant_aggregates"]["hybrid"]
        self.assertIn("answer_correctness", aggregate)
        self.assertIn("unsupported_claim_rate", aggregate)
        self.assertIn("rule_answer_correctness", aggregate)
        self.assertIn("rule_unsupported_claim_rate", aggregate)
        self.assertNotIn("judge_case_count", aggregate)
        self.assertNotIn("judge_scored_count", aggregate)
        self.assertNotIn("judge_answer_correctness", aggregate)
        self.assertNotIn("judge_unsupported_claim_rate", aggregate)
        self.assertNotIn("judge_scored_rate", aggregate)

    def test_run_ask_answer_benchmark_judge_enabled_scores_each_case_variant_record(self) -> None:
        settings = get_settings()
        dataset = load_ask_benchmark_dataset()
        citation = AskCitation(
            chunk_id="chunk-alpha",
            path="Notes/Alpha.md",
            title="Alpha",
            heading_path="Summary",
            start_line=10,
            end_line=12,
            score=0.92,
            snippet="Alpha shipped the new indexer in April.",
        )

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "answer-benchmark.json"
            with patch(
                "app.benchmark.ask_answer_benchmark.load_ask_benchmark_dataset",
                return_value=dataset,
            ):
                with patch(
                    "app.benchmark.ask_answer_benchmark.invoke_ask_graph",
                    side_effect=lambda request, **kwargs: _fake_execution(
                        answer="Alpha shipped the new indexer in April. [1]",
                        citations=[citation],
                    ),
                ):
                    with patch(
                        "app.benchmark.ask_answer_benchmark.score_answer_with_judge",
                        return_value=_scored_judge_score(),
                    ) as mocked_judge:
                        with patch(
                            "app.benchmark.ask_answer_benchmark._get_git_commit",
                            return_value="abc1234",
                        ):
                            with patch(
                                "app.benchmark.ask_answer_benchmark._is_worktree_dirty",
                                return_value=False,
                            ):
                                with patch(
                                    "app.benchmark.ask_answer_benchmark.datetime",
                                ) as mocked_datetime:
                                    mocked_datetime.now.return_value = datetime(2026, 4, 22, 12, 30, 45)
                                    result = run_ask_answer_benchmark(
                                        settings=settings,
                                        mode="smoke",
                                        dataset_path=Path(tmp_dir) / "dataset.json",
                                        output_path=output_path,
                                        judge_enabled=True,
                                        judge_provider_config=_judge_config(),
                                    )

        self.assertEqual(mocked_judge.call_count, 30)
        first_record = result["case_variant_records"][0]
        self.assertIn("rule_score", first_record)
        self.assertEqual(
            first_record["judge_score"],
            {
                "judge_status": "scored",
                "verdict": "mostly_correct",
                "correctness_points": 0.75,
                "matched_facts": ["matched fact"],
                "missed_facts": ["missed fact"],
                "unsupported_claims": [],
                "reason": "The answer is mostly correct.",
                "error_reason": None,
                "raw_response_excerpt": None,
            },
        )
        aggregate = result["variant_aggregates"]["hybrid"]
        self.assertEqual(aggregate["judge_case_count"], 10)
        self.assertEqual(aggregate["judge_scored_count"], 10)
        self.assertEqual(aggregate["judge_answer_correctness"], 0.75)
        self.assertEqual(aggregate["judge_unsupported_claim_rate"], 0.0)
        self.assertEqual(aggregate["judge_scored_rate"], 1.0)

        self.assertEqual(
            result["judge_run_metadata"],
            {
                "judge_enabled": True,
                "judge_provider_name": "judge-provider",
                "judge_model_name": "judge-model",
                "judge_prompt_version": JUDGE_PROMPT_VERSION,
                "judge_run_timestamp": "2026-04-22T12:30:45",
            },
        )

        first_call_input = mocked_judge.call_args_list[0].args[0]
        self.assertIsInstance(first_call_input, JudgeInput)
        self.assertEqual(first_call_input.case_id, "ask_case_001")
        self.assertEqual(first_call_input.variant_id, "hybrid")
        self.assertEqual(first_call_input.user_query, dataset.cases[0].user_query)
        self.assertEqual(first_call_input.expected_facts, dataset.cases[0].expected_facts)
        self.assertEqual(first_call_input.forbidden_claims, dataset.cases[0].forbidden_claims)
        self.assertEqual(first_call_input.answer_text, "Alpha shipped the new indexer in April. [1]")
        self.assertEqual(first_call_input.ask_result_mode, "generated_answer")
        self.assertEqual(
            first_call_input.runtime_faithfulness,
            RuntimeFaithfulnessSignal().model_dump(mode="json", exclude_none=True),
        )
        self.assertEqual(len(first_call_input.citations), 1)
        self.assertEqual(first_call_input.citations[0].citation_id, "chunk-alpha")
        self.assertEqual(first_call_input.citations[0].source_path, "Notes/Alpha.md")
        self.assertEqual(first_call_input.citations[0].snippet, "Alpha shipped the new indexer in April.")
        self.assertEqual(mocked_judge.call_args_list[0].args[1], _judge_config())

    def test_run_ask_answer_benchmark_judge_non_scored_results_do_not_fail_run(self) -> None:
        settings = get_settings()
        dataset = load_ask_benchmark_dataset()

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "answer-benchmark.json"
            with patch(
                "app.benchmark.ask_answer_benchmark.load_ask_benchmark_dataset",
                return_value=dataset,
            ):
                with patch(
                    "app.benchmark.ask_answer_benchmark.invoke_ask_graph",
                    side_effect=lambda request, **kwargs: _fake_execution(),
                ):
                    with patch(
                        "app.benchmark.ask_answer_benchmark.score_answer_with_judge",
                        return_value=_non_scored_judge_score(),
                    ):
                        with patch(
                            "app.benchmark.ask_answer_benchmark._get_git_commit",
                            return_value="abc1234",
                        ):
                            with patch(
                                "app.benchmark.ask_answer_benchmark._is_worktree_dirty",
                                return_value=False,
                            ):
                                result = run_ask_answer_benchmark(
                                    settings=settings,
                                    mode="smoke",
                                    dataset_path=Path(tmp_dir) / "dataset.json",
                                    output_path=output_path,
                                    judge_enabled=True,
                                    judge_provider_config=_judge_config(),
                                )

        self.assertEqual(result["run_status"], "passed")
        first_record = result["case_variant_records"][0]
        self.assertEqual(
            first_record["judge_score"],
            {
                "judge_status": "parse_error",
                "verdict": None,
                "correctness_points": None,
                "matched_facts": [],
                "missed_facts": [],
                "unsupported_claims": [],
                "reason": None,
                "error_reason": "invalid_json",
                "raw_response_excerpt": "{not json",
            },
        )
        aggregate = result["variant_aggregates"]["hybrid"]
        self.assertEqual(aggregate["judge_case_count"], 10)
        self.assertEqual(aggregate["judge_scored_count"], 0)
        self.assertEqual(aggregate["judge_failed_count"], 10)
        self.assertEqual(aggregate["judge_failed_rate"], 1.0)

    def test_run_ask_answer_benchmark_judge_enabled_requires_provider_config(self) -> None:
        settings = get_settings()

        with TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(ValueError, "judge_provider_config is required"):
                run_ask_answer_benchmark(
                    settings=settings,
                    mode="smoke",
                    output_path=Path(tmp_dir) / "answer-benchmark.json",
                    judge_enabled=True,
                )

    def test_run_ask_answer_benchmark_full_selects_fifty_cases_and_includes_tool_aggregate(self) -> None:
        settings = get_settings()
        dataset = load_ask_benchmark_dataset()

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "answer-benchmark.json"
            with patch(
                "app.benchmark.ask_answer_benchmark.load_ask_benchmark_dataset",
                return_value=dataset,
            ):
                with patch(
                    "app.benchmark.ask_answer_benchmark.invoke_ask_graph",
                    side_effect=lambda request, **kwargs: _fake_execution(),
                ) as mocked_invoke:
                    with patch(
                        "app.benchmark.ask_answer_benchmark._get_git_commit",
                        return_value="abc1234",
                    ):
                        with patch(
                            "app.benchmark.ask_answer_benchmark._is_worktree_dirty",
                            return_value=True,
                        ):
                            with patch(
                                "app.benchmark.ask_answer_benchmark.datetime",
                            ) as mocked_datetime:
                                mocked_datetime.now.return_value = datetime(2026, 4, 22, 12, 30, 45)
                                result = run_ask_answer_benchmark(
                                    settings=settings,
                                    mode="full",
                                    dataset_path=Path(tmp_dir) / "dataset.json",
                                    output_path=output_path,
                                )

            self.assertEqual(result["benchmark_mode"], "full")
            self.assertEqual(len(result["selected_case_ids"]), 50)
            self.assertEqual(mocked_invoke.call_count, 150)
            expected_case_variant_matrix = [
                (case.case_id, variant.variant_id)
                for case in dataset.cases
                for variant in ANSWER_BENCHMARK_VARIANTS
            ]
            self.assertEqual(_call_matrix(mocked_invoke.call_args_list), expected_case_variant_matrix)
            thread_ids = _thread_ids(mocked_invoke.call_args_list)
            self.assertEqual(len(thread_ids), len(set(thread_ids)))
            first_request = mocked_invoke.call_args_list[0].args[0]
            first_kwargs = mocked_invoke.call_args_list[0].kwargs
            self.assertEqual(first_request.provider_preference, "cloud")
            self.assertEqual(first_request.metadata["max_tool_rounds"], 0)
            tool_allowed_case_ids = {case.case_id for case in dataset.cases if case.allow_tool}
            tool_allowed_request = next(
                call.args[0]
                for call in mocked_invoke.call_args_list
                if call.args[0].metadata["case_id"] in tool_allowed_case_ids
            )
            self.assertNotIn("max_tool_rounds", tool_allowed_request.metadata)
            self.assertEqual(first_kwargs["settings"].cloud_chat_model, "qwen3.6-flash-2026-04-16")
            self.assertEqual(first_kwargs["settings"].local_chat_model, "")
            self.assertTrue(
                first_kwargs["thread_id"].startswith("task059_ask_case_001_hybrid_")
            )
            self.assertEqual(result["provider_name"], "openai-compatible")
            self.assertEqual(result["model_name"], "qwen3.6-flash-2026-04-16")
            self.assertEqual(result["git_commit"], "abc1234")
            self.assertTrue(result["worktree_dirty"])
            self.assertEqual(len(result["case_variant_records"]), 150)
            self.assertIn("tool_allowed", result["variant_aggregates"]["hybrid"])
            self.assertEqual(result["artifact_metadata"]["provider_name"], "openai-compatible")
            self.assertEqual(result["artifact_metadata"]["model_name"], "qwen3.6-flash-2026-04-16")
            self.assertEqual(
                result["artifact_metadata"]["prompt_version"],
                resolve_answer_benchmark_prompt_version(),
            )
            self.assertEqual(result["artifact_metadata"]["git_commit"], "abc1234")
            self.assertEqual(result["artifact_metadata"]["benchmark_mode"], "full")
            self.assertEqual(result["artifact_metadata"]["selected_case_ids"], result["selected_case_ids"])
