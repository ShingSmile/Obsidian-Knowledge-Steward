from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.benchmark.ask_answer_benchmark_judge import JudgeConfigOverrides, JudgeProviderConfig


ROOT_DIR = Path(__file__).resolve().parents[2]
CLI_PATH = ROOT_DIR / "eval" / "benchmark" / "judge_answer_benchmark_artifact.py"


def load_cli_module() -> object:
    spec = importlib.util.spec_from_file_location("judge_answer_benchmark_artifact_cli", CLI_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load CLI module from {CLI_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _judge_config(
    *,
    base_url: str = "https://judge.example",
    model_name: str = "judge-model",
) -> JudgeProviderConfig:
    return JudgeProviderConfig(
        provider_name="judge-provider",
        base_url=base_url,
        api_key="judge-key",
        model_name=model_name,
    )


class AskAnswerBenchmarkJudgeCliTests(unittest.TestCase):
    def test_missing_input_returns_exit_code_1(self) -> None:
        module = load_cli_module()

        stderr_buffer = io.StringIO()
        with contextlib.redirect_stderr(stderr_buffer):
            exit_code = module.main(["--output", "/tmp/out.json"])

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR:", stderr_buffer.getvalue())

    def test_wrong_artifact_kind_returns_exit_code_1(self) -> None:
        module = load_cli_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "artifact.json"
            input_path.write_text('{"benchmark_kind": "retrieval"}', encoding="utf-8")
            output_path = temp_path / "out.json"

            with patch.object(module, "get_settings", return_value=Mock()):
                with patch.object(module, "resolve_judge_provider_config", return_value=_judge_config()):
                    stderr_buffer = io.StringIO()
                    with contextlib.redirect_stderr(stderr_buffer):
                        exit_code = module.main(["--input", str(input_path), "--output", str(output_path)])

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR:", stderr_buffer.getvalue())

    def test_missing_judge_base_url_returns_1_and_skips_service(self) -> None:
        module = load_cli_module()

        with patch.object(module, "get_settings", return_value=Mock()):
            with patch.object(
                module,
                "resolve_judge_provider_config",
                return_value=_judge_config(base_url="  "),
            ):
                with patch.object(module, "judge_answer_benchmark_artifact") as mocked_service:
                    stderr_buffer = io.StringIO()
                    with contextlib.redirect_stderr(stderr_buffer):
                        exit_code = module.main(["--input", "/tmp/in.json", "--output", "/tmp/out.json"])

        self.assertEqual(exit_code, 1)
        mocked_service.assert_not_called()
        self.assertIn("base URL", stderr_buffer.getvalue())

    def test_missing_resolved_judge_model_returns_1_and_skips_service(self) -> None:
        module = load_cli_module()

        with patch.object(module, "get_settings", return_value=Mock()):
            with patch.object(
                module,
                "resolve_judge_provider_config",
                return_value=_judge_config(model_name=""),
            ):
                with patch.object(module, "judge_answer_benchmark_artifact") as mocked_service:
                    stderr_buffer = io.StringIO()
                    with contextlib.redirect_stderr(stderr_buffer):
                        exit_code = module.main(["--input", "/tmp/in.json", "--output", "/tmp/out.json"])

        self.assertEqual(exit_code, 1)
        mocked_service.assert_not_called()
        self.assertIn("model", stderr_buffer.getvalue())

    def test_judge_model_preview_value_is_accepted_and_forwarded_as_override(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        judge_config = _judge_config(model_name="qwen3.6-max-preview")

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "resolve_judge_provider_config",
                return_value=judge_config,
            ) as mocked_resolve:
                with patch.object(module, "judge_answer_benchmark_artifact", return_value={}) as mocked_service:
                    exit_code = module.main(
                        [
                            "--input",
                            "/tmp/in.json",
                            "--output",
                            "/tmp/out.json",
                            "--judge-model",
                            "qwen3.6-max-preview",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        mocked_resolve.assert_called_once_with(
            mocked_settings,
            JudgeConfigOverrides(model="qwen3.6-max-preview"),
        )
        _, kwargs = mocked_service.call_args
        self.assertIs(kwargs["judge_provider_config"], judge_config)

    def test_valid_input_forwards_paths_settings_and_resolved_judge_config(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        judge_config = _judge_config()

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(module, "resolve_judge_provider_config", return_value=judge_config):
                with patch.object(module, "judge_answer_benchmark_artifact", return_value={}) as mocked_service:
                    exit_code = module.main(
                        [
                            "--input",
                            "/tmp/in.json",
                            "--output",
                            "/tmp/out.json",
                            "--dataset",
                            "/tmp/dataset.json",
                        ]
                    )

        self.assertEqual(exit_code, 0)
        mocked_service.assert_called_once()
        _, kwargs = mocked_service.call_args
        self.assertEqual(kwargs["input_path"], Path("/tmp/in.json"))
        self.assertEqual(kwargs["output_path"], Path("/tmp/out.json"))
        self.assertEqual(kwargs["dataset_path"], Path("/tmp/dataset.json"))
        self.assertIs(kwargs["settings"], mocked_settings)
        self.assertIs(kwargs["judge_provider_config"], judge_config)


if __name__ == "__main__":
    unittest.main()
