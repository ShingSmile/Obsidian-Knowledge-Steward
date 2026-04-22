from __future__ import annotations

import json
import inspect
import tempfile
import unittest
from pathlib import Path

from app.benchmark.ask_answer_benchmark_variants import (
    ANSWER_BENCHMARK_VARIANTS,
    AskAnswerBenchmarkVariant,
    build_answer_benchmark_metadata,
    load_answer_benchmark_smoke_case_ids,
    resolve_answer_benchmark_prompt_version,
)


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
