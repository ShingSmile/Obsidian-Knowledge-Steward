from __future__ import annotations

import json
import inspect
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime
from unittest.mock import Mock, patch

from app.benchmark.ask_answer_benchmark_variants import (
    ANSWER_BENCHMARK_VARIANTS,
    AskAnswerBenchmarkVariant,
    build_answer_benchmark_metadata,
    load_answer_benchmark_smoke_case_ids,
    resolve_answer_benchmark_prompt_version,
)
from app.benchmark.ask_dataset import load_ask_benchmark_dataset
from app.config import get_settings
from app.contracts.workflow import AskResultMode, GuardrailAction, RuntimeFaithfulnessSignal

from app.benchmark.ask_answer_benchmark import run_ask_answer_benchmark


def _fake_execution(
    *,
    provider_name: str = "openai-compatible",
    model_name: str = "qwen-max",
    ask_result_mode: AskResultMode = AskResultMode.GENERATED_ANSWER,
) -> Mock:
    ask_result = Mock(
        mode=ask_result_mode,
        answer="answer text",
        citations=[],
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
        runtime_faithfulness=RuntimeFaithfulnessSignal(),
    )
    return Mock(ask_result=ask_result)


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
            ),
            {
                "benchmark_kind": "ask_answer",
                "case_id": "ask_case_001",
                "variant_id": "hybrid_assembly_gate",
                "context_assembly_enabled": True,
                "runtime_faithfulness_gate_enabled": True,
                "smoke_subset": False,
                "prompt_version": "tool:2026-04-22-tool-v1|answer:2026-04-22-grounded-v1",
            },
        )

    def test_build_answer_benchmark_metadata_requires_explicit_smoke_subset(self) -> None:
        self.assertIs(
            inspect.signature(build_answer_benchmark_metadata).parameters["smoke_subset"].default,
            inspect._empty,
        )


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
            first_request = mocked_invoke.call_args_list[0].args[0]
            self.assertEqual(first_request.provider_preference, "cloud")
            self.assertTrue(output_path.exists())
            self.assertEqual(result["provider_name"], "openai-compatible")
            self.assertEqual(result["model_name"], "qwen-max")
            self.assertEqual(result["prompt_version"], resolve_answer_benchmark_prompt_version())
            self.assertEqual(result["git_commit"], "abc1234")
            self.assertFalse(result["worktree_dirty"])
            self.assertEqual(result["benchmark_kind"], "ask_answer")
            self.assertEqual(result["schema_version"], 1)
            self.assertEqual(len(result["case_variant_records"]), 30)
            self.assertEqual(result["smoke_subset_version"], 1)
            self.assertNotIn("tool_allowed", result["variant_aggregates"]["hybrid"])
            self.assertEqual(
                set(result["artifact_metadata"]),
                {
                    "schema_version",
                    "benchmark_kind",
                    "benchmark_mode",
                    "dataset_version",
                    "provider_name",
                    "model_name",
                    "run_timestamp",
                    "git_commit",
                    "prompt_version",
                    "worktree_dirty",
                    "selected_case_count",
                    "selected_case_ids",
                    "smoke_subset_version",
                },
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
            first_request = mocked_invoke.call_args_list[0].args[0]
            self.assertEqual(first_request.provider_preference, "cloud")
            self.assertEqual(result["provider_name"], "openai-compatible")
            self.assertEqual(result["model_name"], "qwen-max")
            self.assertEqual(result["git_commit"], "abc1234")
            self.assertTrue(result["worktree_dirty"])
            self.assertEqual(len(result["case_variant_records"]), 150)
            self.assertIn("tool_allowed", result["variant_aggregates"]["hybrid"])
            self.assertEqual(
                set(result["artifact_metadata"]),
                {
                    "schema_version",
                    "benchmark_kind",
                    "benchmark_mode",
                    "dataset_version",
                    "provider_name",
                    "model_name",
                    "run_timestamp",
                    "git_commit",
                    "prompt_version",
                    "worktree_dirty",
                    "selected_case_count",
                    "selected_case_ids",
                },
            )
