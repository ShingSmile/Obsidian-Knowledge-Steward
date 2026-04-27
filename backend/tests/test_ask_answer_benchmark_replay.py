from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from app.benchmark.ask_answer_benchmark_judge import (
    JUDGE_PROMPT_VERSION,
    JudgeInput,
    JudgeProviderConfig,
    JudgeScore,
)
from app.benchmark.ask_answer_benchmark_replay import (
    judge_answer_benchmark_artifact,
    load_answer_benchmark_artifact,
)


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
        verdict="correct",
        correctness_points=1.0,
        matched_facts=["Alpha shipped the new indexer."],
        missed_facts=[],
        unsupported_claims=[],
        reason="The answer matches the expected fact.",
    )


def _dataset_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "cases": [
            {
                "case_id": "ask_case_001",
                "bucket": "single_hop",
                "user_query": "What changed in Alpha?",
                "source_origin": "fixture",
                "expected_relevant_paths": ["Notes/Alpha.md"],
                "expected_relevant_locators": [],
                "expected_facts": ["Alpha shipped the new indexer."],
                "forbidden_claims": ["Beta was deleted."],
                "allow_tool": False,
                "expected_tool_names": [],
                "allow_retrieval_only": False,
                "should_generate_answer": True,
                "review_status": "approved",
                "review_notes": "",
            }
        ],
    }


def _legacy_artifact() -> dict[str, object]:
    return {
        "schema_version": 1,
        "benchmark_kind": "ask_answer",
        "benchmark_mode": "smoke",
        "dataset_version": 1,
        "run_timestamp": "2026-04-25T10:00:00",
        "provider_name": "answer-provider",
        "model_name": "answer-model",
        "custom_top_level": {"preserve": True},
        "case_variant_records": [
            {
                "case_id": "ask_case_001",
                "variant_id": "hybrid",
                "ask_result_mode": "generated_answer",
                "answer_text": "Alpha shipped the new indexer. [1]",
                "citations": [
                    {
                        "chunk_id": "chunk-alpha",
                        "path": "Notes/Alpha.md",
                        "snippet": "Alpha shipped the new indexer.",
                    }
                ],
                "runtime_faithfulness": {"outcome": "allow"},
                "record_metadata": {"preserve": True},
            }
        ],
        "variant_aggregates": {
            "hybrid": {
                "case_count": 1,
                "answer_correctness": 0.5,
                "unsupported_claim_rate": 0.25,
            }
        },
        "run_status": "passed",
    }


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class AskAnswerBenchmarkReplayTests(unittest.TestCase):
    def test_rejects_non_answer_benchmark_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = _write_json(Path(temp_dir) / "artifact.json", {"benchmark_kind": "retrieval"})

            with self.assertRaisesRegex(ValueError, "ask_answer"):
                load_answer_benchmark_artifact(input_path)

    def test_adds_judge_score_to_valid_legacy_records_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", _legacy_artifact())
            output_path = temp_path / "judged-artifact.json"

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ) as mocked_judge:
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=output_path,
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )
            self.assertTrue(output_path.exists())
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(written, result)
        record = result["case_variant_records"][0]
        self.assertEqual(record["record_metadata"], {"preserve": True})
        self.assertEqual(record["judge_score"]["judge_status"], "scored")
        self.assertEqual(record["judge_score"]["correctness_points"], 1.0)
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_case_count"], 1)
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_scored_count"], 1)

        mocked_judge.assert_called_once()
        judge_input = mocked_judge.call_args.args[0]
        self.assertIsInstance(judge_input, JudgeInput)
        self.assertEqual(judge_input.case_id, "ask_case_001")
        self.assertEqual(judge_input.variant_id, "hybrid")
        self.assertEqual(judge_input.user_query, "What changed in Alpha?")
        self.assertEqual(judge_input.expected_facts, ["Alpha shipped the new indexer."])
        self.assertEqual(judge_input.forbidden_claims, ["Beta was deleted."])
        self.assertEqual(judge_input.answer_text, "Alpha shipped the new indexer. [1]")
        self.assertEqual(judge_input.ask_result_mode, "generated_answer")
        self.assertEqual(judge_input.runtime_faithfulness, {"outcome": "allow"})
        self.assertEqual(judge_input.citations[0].citation_id, "chunk-alpha")
        self.assertEqual(judge_input.citations[0].source_path, "Notes/Alpha.md")
        self.assertEqual(judge_input.citations[0].snippet, "Alpha shipped the new indexer.")
        self.assertEqual(mocked_judge.call_args.args[1], _judge_config())

    def test_preserves_original_top_level_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", _legacy_artifact())

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ):
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        self.assertEqual(result["run_timestamp"], "2026-04-25T10:00:00")
        self.assertEqual(result["provider_name"], "answer-provider")
        self.assertEqual(result["model_name"], "answer-model")
        self.assertEqual(result["custom_top_level"], {"preserve": True})
        self.assertEqual(result["run_status"], "passed")

    def test_adds_full_judge_run_metadata_with_empty_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", _legacy_artifact())

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ):
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        metadata = result["judge_run_metadata"]
        self.assertEqual(metadata["judge_enabled"], True)
        self.assertEqual(metadata["judge_provider_name"], "judge-provider")
        self.assertEqual(metadata["judge_model_name"], "judge-model")
        self.assertEqual(metadata["judge_prompt_version"], JUDGE_PROMPT_VERSION)
        self.assertEqual(metadata["source_artifact_path"], str(input_path))
        self.assertEqual(metadata["warnings"], [])
        self.assertIsInstance(datetime.fromisoformat(metadata["judge_run_timestamp"]), datetime)

    def test_records_dataset_version_mismatch_warning(self) -> None:
        artifact = _legacy_artifact()
        artifact["dataset_version"] = 0

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", artifact)

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ):
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        self.assertEqual(
            result["judge_run_metadata"]["warnings"],
            [
                {
                    "code": "dataset_version_mismatch",
                    "artifact_dataset_version": 0,
                    "current_dataset_version": 1,
                }
            ],
        )

    def test_backfills_legacy_rule_aggregate_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", _legacy_artifact())

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ):
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        aggregate = result["variant_aggregates"]["hybrid"]
        self.assertEqual(aggregate["rule_answer_correctness"], 0.5)
        self.assertEqual(aggregate["rule_unsupported_claim_rate"], 0.25)

    def test_skips_records_missing_required_fields_without_calling_provider(self) -> None:
        artifact = _legacy_artifact()
        artifact["case_variant_records"] = [
            {"variant_id": "hybrid", "answer_text": "answer", "citations": []},
            {"case_id": "ask_case_001", "answer_text": "answer", "citations": []},
            {"case_id": "ask_case_001", "variant_id": "hybrid", "citations": []},
            {"case_id": "ask_case_001", "variant_id": "hybrid", "answer_text": "answer"},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", artifact)

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ) as mocked_judge:
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        mocked_judge.assert_not_called()
        for record in result["case_variant_records"]:
            self.assertEqual(record["judge_score"]["judge_status"], "skipped_missing_record_fields")
            self.assertIsNone(record["judge_score"]["verdict"])
            self.assertIsNone(record["judge_score"]["correctness_points"])
            self.assertEqual(record["judge_score"]["matched_facts"], [])
            self.assertEqual(record["judge_score"]["missed_facts"], [])
            self.assertEqual(record["judge_score"]["unsupported_claims"], [])
            self.assertIsNone(record["judge_score"]["reason"])
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_case_count"], 3)
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_failed_count"], 3)

    def test_skips_records_with_invalid_required_values_without_calling_provider(self) -> None:
        artifact = _legacy_artifact()
        artifact["case_variant_records"] = [
            {"case_id": "ask_case_001", "variant_id": None, "answer_text": "answer", "citations": []},
            {"case_id": "ask_case_001", "variant_id": "   ", "answer_text": "answer", "citations": []},
            {"case_id": "ask_case_001", "variant_id": "hybrid", "answer_text": None, "citations": []},
            {"case_id": "   ", "variant_id": "hybrid", "answer_text": "answer", "citations": []},
            {
                "case_id": "ask_case_001",
                "variant_id": "hybrid",
                "answer_text": "answer",
                "citations": {"chunk_id": "not-a-list"},
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", artifact)

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ) as mocked_judge:
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        mocked_judge.assert_not_called()
        for record in result["case_variant_records"]:
            self.assertEqual(
                record["judge_score"],
                {
                    "judge_status": "skipped_missing_record_fields",
                    "verdict": None,
                    "correctness_points": None,
                    "matched_facts": [],
                    "missed_facts": [],
                    "unsupported_claims": [],
                    "reason": None,
                    "error_reason": "missing_record_fields",
                    "raw_response_excerpt": None,
                },
            )
        self.assertNotIn("None", result["variant_aggregates"])
        self.assertNotIn("", result["variant_aggregates"])
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_case_count"], 3)
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_failed_count"], 3)

    def test_valid_record_uses_normalized_case_and_variant_ids_for_judging_and_aggregation(self) -> None:
        artifact = _legacy_artifact()
        artifact["case_variant_records"][0]["case_id"] = " ask_case_001 "
        artifact["case_variant_records"][0]["variant_id"] = " hybrid "

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", artifact)

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
                return_value=_scored_judge_score(),
            ) as mocked_judge:
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        mocked_judge.assert_called_once()
        judge_input = mocked_judge.call_args.args[0]
        self.assertEqual(judge_input.case_id, "ask_case_001")
        self.assertEqual(judge_input.variant_id, "hybrid")
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_case_count"], 1)
        self.assertNotIn(" hybrid ", result["variant_aggregates"])

    def test_skips_missing_dataset_case_without_calling_provider(self) -> None:
        artifact = _legacy_artifact()
        artifact["case_variant_records"][0]["case_id"] = "missing_case"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset_path = _write_json(temp_path / "dataset.json", _dataset_payload())
            input_path = _write_json(temp_path / "artifact.json", artifact)

            with patch(
                "app.benchmark.ask_answer_benchmark_replay.score_answer_with_judge",
            ) as mocked_judge:
                result = judge_answer_benchmark_artifact(
                    input_path=input_path,
                    output_path=temp_path / "out.json",
                    settings=Mock(),
                    dataset_path=dataset_path,
                    judge_provider_config=_judge_config(),
                )

        mocked_judge.assert_not_called()
        record = result["case_variant_records"][0]
        self.assertEqual(record["judge_score"]["judge_status"], "skipped_missing_dataset_case")
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_case_count"], 1)
        self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_failed_count"], 1)


if __name__ == "__main__":
    unittest.main()
