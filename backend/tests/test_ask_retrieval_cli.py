from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.benchmark.ask_retrieval_preflight import AskRetrievalPreflightResult


ROOT_DIR = Path(__file__).resolve().parents[2]
CLI_PATH = ROOT_DIR / "eval" / "benchmark" / "run_retrieval_benchmark.py"


def load_cli_module() -> object:
    spec = importlib.util.spec_from_file_location("run_retrieval_benchmark_cli", CLI_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load CLI module from {CLI_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AskRetrievalCliTests(unittest.TestCase):
    def test_main_returns_non_zero_and_skips_benchmark_when_preflight_fails(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        mocked_settings.sample_vault_dir = Path("/tmp/sample-vault")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "retrieval-benchmark.json"
            with patch.object(module, "get_settings", return_value=mocked_settings):
                with patch.object(
                    module,
                    "run_local_retrieval_preflight",
                    return_value=AskRetrievalPreflightResult(
                        status="provider_not_configured",
                        provider_key=None,
                        provider_name=None,
                        model_name=None,
                        message="Local embedding provider is not configured.",
                    ),
                ):
                    with patch.object(module, "run_ask_retrieval_benchmark") as mocked_run_benchmark:
                        stderr_buffer = io.StringIO()
                        with contextlib.redirect_stderr(stderr_buffer):
                            exit_code = module.main(
                                ["--output", str(output_path)]
                            )

            self.assertFalse(output_path.exists())

        self.assertEqual(exit_code, 1)
        mocked_run_benchmark.assert_not_called()
        self.assertIn(
            "Local embedding provider is not configured.",
            stderr_buffer.getvalue(),
        )

    def test_main_returns_zero_and_forwards_output_and_dataset(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        mocked_settings.sample_vault_dir = Path("/tmp/sample-vault")

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "run_local_retrieval_preflight",
                return_value=AskRetrievalPreflightResult(
                    status="ok",
                    provider_key="local",
                    provider_name="ollama",
                    model_name="nomic-embed-text",
                    message="Local embedding preflight passed.",
                ),
            ):
                with patch.object(
                    module,
                    "run_ask_retrieval_benchmark",
                    return_value={"run_status": "passed"},
                ) as mocked_run_benchmark:
                    exit_code = module.main(
                        [
                            "--output",
                            "/tmp/retrieval-benchmark.json",
                            "--dataset",
                            "/tmp/ask-benchmark.json",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        mocked_run_benchmark.assert_called_once()
        _, kwargs = mocked_run_benchmark.call_args
        self.assertEqual(kwargs["output_path"], Path("/tmp/retrieval-benchmark.json"))
        self.assertEqual(kwargs["dataset_path"], Path("/tmp/ask-benchmark.json"))

    def test_main_uses_default_output_path_when_output_is_omitted(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        mocked_settings.sample_vault_dir = Path("/tmp/sample-vault")

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "run_local_retrieval_preflight",
                return_value=AskRetrievalPreflightResult(
                    status="ok",
                    provider_key="local",
                    provider_name="ollama",
                    model_name="nomic-embed-text",
                    message="Local embedding preflight passed.",
                ),
            ):
                with patch.object(
                    module,
                    "run_ask_retrieval_benchmark",
                    return_value={"run_status": "passed"},
                ) as mocked_run_benchmark:
                    exit_code = module.main([])

        self.assertEqual(exit_code, 0)
        mocked_run_benchmark.assert_called_once()
        _, kwargs = mocked_run_benchmark.call_args
        self.assertIsNone(kwargs["output_path"])
        self.assertIsNone(kwargs["dataset_path"])

    def test_main_returns_non_zero_when_benchmark_fails(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        mocked_settings.sample_vault_dir = Path("/tmp/sample-vault")

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "run_local_retrieval_preflight",
                return_value=AskRetrievalPreflightResult(
                    status="ok",
                    provider_key="local",
                    provider_name="ollama",
                    model_name="nomic-embed-text",
                    message="Local embedding preflight passed.",
                ),
            ):
                with patch.object(
                    module,
                    "run_ask_retrieval_benchmark",
                    return_value={"run_status": "failed"},
                ):
                    exit_code = module.main(["--output", "/tmp/retrieval-benchmark.json"])

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
