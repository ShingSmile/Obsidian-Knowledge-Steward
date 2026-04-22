from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.benchmark.ask_answer_benchmark_preflight import AskAnswerBenchmarkPreflightResult


ROOT_DIR = Path(__file__).resolve().parents[2]
CLI_PATH = ROOT_DIR / "eval" / "benchmark" / "run_answer_benchmark.py"


def load_cli_module() -> object:
    spec = importlib.util.spec_from_file_location("run_answer_benchmark_cli", CLI_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load CLI module from {CLI_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AskAnswerBenchmarkCliTests(unittest.TestCase):
    def test_main_returns_non_zero_and_skips_benchmark_when_preflight_fails(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "answer-benchmark.json"
            with patch.object(module, "get_settings", return_value=mocked_settings):
                with patch.object(
                    module,
                    "run_answer_benchmark_preflight",
                    return_value=AskAnswerBenchmarkPreflightResult(
                        status="provider_not_configured",
                        provider_name=None,
                        model_name=None,
                        message="Cloud provider is not configured.",
                    ),
                ):
                    with patch.object(module, "run_ask_answer_benchmark") as mocked_run_benchmark:
                        stderr_buffer = io.StringIO()
                        with contextlib.redirect_stderr(stderr_buffer):
                            exit_code = module.main(["--mode", "smoke", "--output", str(output_path)])

            self.assertFalse(output_path.exists())

        self.assertEqual(exit_code, 1)
        mocked_run_benchmark.assert_not_called()
        self.assertIn("Cloud provider is not configured.", stderr_buffer.getvalue())

    def test_main_forwards_mode_output_and_dataset(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "run_answer_benchmark_preflight",
                return_value=AskAnswerBenchmarkPreflightResult(
                    status="ok",
                    provider_name="openai-compatible",
                    model_name="qwen-max",
                    message="Answer benchmark preflight passed.",
                ),
            ):
                with patch.object(
                    module,
                    "run_ask_answer_benchmark",
                    return_value={"run_status": "passed"},
                ) as mocked_run_benchmark:
                    exit_code = module.main(
                        [
                            "--mode",
                            "full",
                            "--output",
                            "/tmp/answer-benchmark.json",
                            "--dataset",
                            "/tmp/ask-benchmark.json",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        mocked_run_benchmark.assert_called_once()
        _, kwargs = mocked_run_benchmark.call_args
        self.assertEqual(kwargs["mode"], "full")
        self.assertEqual(kwargs["output_path"], Path("/tmp/answer-benchmark.json"))
        self.assertEqual(kwargs["dataset_path"], Path("/tmp/ask-benchmark.json"))


if __name__ == "__main__":
    unittest.main()
