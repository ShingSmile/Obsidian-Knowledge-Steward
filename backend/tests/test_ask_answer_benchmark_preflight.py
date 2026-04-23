from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from app.benchmark.ask_answer_benchmark_preflight import run_answer_benchmark_preflight
from app.config import get_settings


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
        self.assertIn("qwen3.6-max-preview", result.message)

    def test_reports_missing_smoke_subset_file_in_smoke_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark.json"
            dataset_path.write_text('{"schema_version": 1, "cases": []}', encoding="utf-8")
            smoke_subset_path = temp_root / "missing_smoke_subset.json"

            settings = replace(
                get_settings(),
                cloud_base_url="https://example.com",
                cloud_chat_model="qwen3.6-max-preview",
            )
            result = run_answer_benchmark_preflight(
                settings=settings,
                mode="smoke",
                dataset_path=dataset_path,
                smoke_subset_path=smoke_subset_path,
            )

        self.assertEqual(result.status, "smoke_subset_not_found")
        self.assertIn("smoke subset", result.message)


if __name__ == "__main__":
    unittest.main()
