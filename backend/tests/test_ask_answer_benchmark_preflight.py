from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from app.benchmark.ask_answer_benchmark_judge import (
    DEFAULT_JUDGE_MODEL,
    JudgeConfigOverrides,
    JudgeProviderConfig,
    resolve_judge_provider_config,
)
from app.benchmark.ask_answer_benchmark_preflight import run_answer_benchmark_preflight
from app.config import get_settings


def _write_readable_benchmark_files(temp_root: Path) -> tuple[Path, Path]:
    dataset_path = temp_root / "ask_benchmark.json"
    dataset_path.write_text('{"schema_version": 1, "cases": []}', encoding="utf-8")
    smoke_subset_path = temp_root / "ask_answer_benchmark_smoke_cases.json"
    smoke_subset_path.write_text(
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
                    "ask_case_010",
                ],
            }
        ),
        encoding="utf-8",
    )
    return dataset_path, smoke_subset_path


def _answer_benchmark_settings(**overrides: object):
    defaults = {
        "cloud_provider_name": "openai-compatible",
        "cloud_base_url": "https://answer.example",
        "cloud_api_key": "answer-key",
        "cloud_chat_model": "qwen3.6-flash-2026-04-16",
    }
    defaults.update(overrides)
    return replace(get_settings(), **defaults)


class AskAnswerBenchmarkPreflightTests(unittest.TestCase):
    def test_reports_missing_cloud_provider_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark.json"
            dataset_path.write_text('{"schema_version": 1, "cases": []}', encoding="utf-8")
            smoke_subset_path = temp_root / "ask_answer_benchmark_smoke_cases.json"
            smoke_subset_path.write_text("{}", encoding="utf-8")

            settings = replace(
                get_settings(),
                cloud_base_url="",
                cloud_chat_model="",
            )
            result = run_answer_benchmark_preflight(
                settings=settings,
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
            )

        self.assertEqual(result.status, "provider_not_configured")
        self.assertIn("KS_CLOUD_BASE_URL", result.message)

    def test_reports_canonical_model_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark.json"
            dataset_path.write_text('{"schema_version": 1, "cases": []}', encoding="utf-8")
            smoke_subset_path = temp_root / "ask_answer_benchmark_smoke_cases.json"
            smoke_subset_path.write_text("{}", encoding="utf-8")

            settings = replace(
                get_settings(),
                cloud_base_url="https://example.com",
                cloud_chat_model="gpt-test",
            )
            result = run_answer_benchmark_preflight(
                settings=settings,
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
            )

        self.assertEqual(result.status, "canonical_model_mismatch")
        self.assertIn("qwen3.6-flash-2026-04-16", result.message)

    def test_reports_missing_smoke_subset_file_in_smoke_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark.json"
            dataset_path.write_text('{"schema_version": 1, "cases": []}', encoding="utf-8")
            smoke_subset_path = temp_root / "missing_smoke_subset.json"

            settings = replace(
                get_settings(),
                cloud_base_url="https://example.com",
                cloud_chat_model="qwen3.6-flash-2026-04-16",
            )
            result = run_answer_benchmark_preflight(
                settings=settings,
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
            )

        self.assertEqual(result.status, "smoke_subset_not_found")
        self.assertIn("smoke subset", result.message)

    def test_disabled_judge_does_not_require_judge_config_but_still_requires_answer_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path, smoke_subset_path = _write_readable_benchmark_files(Path(temp_dir))

            result = run_answer_benchmark_preflight(
                settings=_answer_benchmark_settings(),
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
                judge_enabled=False,
                judge_provider_config=None,
            )
            missing_answer_result = run_answer_benchmark_preflight(
                settings=_answer_benchmark_settings(cloud_base_url="", cloud_chat_model=""),
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
                judge_enabled=False,
                judge_provider_config=None,
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(missing_answer_result.status, "provider_not_configured")

    def test_enabled_judge_fails_startup_when_judge_base_url_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path, smoke_subset_path = _write_readable_benchmark_files(Path(temp_dir))

            result = run_answer_benchmark_preflight(
                settings=_answer_benchmark_settings(),
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
                judge_enabled=True,
                judge_provider_config=JudgeProviderConfig(
                    provider_name="judge-provider",
                    base_url="",
                    api_key="judge-key",
                    model_name="judge-model",
                ),
            )

        self.assertEqual(result.status, "judge_provider_not_configured")
        self.assertIn("judge", result.message.lower())

    def test_enabled_judge_uses_default_model_when_no_judge_model_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path, smoke_subset_path = _write_readable_benchmark_files(Path(temp_dir))
            settings = _answer_benchmark_settings(
                judge_provider_name="judge-provider",
                judge_base_url="https://judge.example",
                judge_api_key="judge-key",
                judge_model="",
            )
            judge_config = resolve_judge_provider_config(settings, JudgeConfigOverrides())

            result = run_answer_benchmark_preflight(
                settings=settings,
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
                judge_enabled=True,
                judge_provider_config=judge_config,
            )

        self.assertEqual(judge_config.model_name, DEFAULT_JUDGE_MODEL)
        self.assertEqual(result.status, "ok")

    def test_missing_judge_api_key_is_not_startup_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path, smoke_subset_path = _write_readable_benchmark_files(Path(temp_dir))

            result = run_answer_benchmark_preflight(
                settings=_answer_benchmark_settings(),
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
                judge_enabled=True,
                judge_provider_config=JudgeProviderConfig(
                    provider_name="judge-provider",
                    base_url="https://judge.example",
                    api_key="",
                    model_name="judge-model",
                ),
            )

        self.assertEqual(result.status, "ok")


if __name__ == "__main__":
    unittest.main()
