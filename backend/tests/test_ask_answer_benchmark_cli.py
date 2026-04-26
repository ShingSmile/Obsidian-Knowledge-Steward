from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import Mock, patch

from app.benchmark.ask_answer_benchmark_judge import JudgeConfigOverrides, JudgeProviderConfig
from app.benchmark.ask_answer_benchmark_preflight import AskAnswerBenchmarkPreflightResult
from app.config import get_settings


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
                    model_name="qwen3.6-flash-2026-04-16",
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

    def test_default_judge_is_disabled_and_does_not_require_judge_flags(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        judge_config = JudgeProviderConfig(
            provider_name="judge-provider",
            base_url="https://judge.example",
            api_key="judge-key",
            model_name="judge-model",
        )

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "resolve_judge_provider_config",
                return_value=judge_config,
            ) as mocked_resolve:
                with patch.object(
                    module,
                    "run_answer_benchmark_preflight",
                    return_value=AskAnswerBenchmarkPreflightResult(
                        status="ok",
                        provider_name="openai-compatible",
                        model_name="qwen3.6-flash-2026-04-16",
                        message="Answer benchmark preflight passed.",
                    ),
                ) as mocked_preflight:
                    with patch.object(
                        module,
                        "run_ask_answer_benchmark",
                        return_value={"run_status": "passed"},
                    ) as mocked_run_benchmark:
                        exit_code = module.main(["--mode", "smoke", "--output", "/tmp/answer-benchmark.json"])

        self.assertEqual(exit_code, 0)
        mocked_resolve.assert_called_once_with(mocked_settings, JudgeConfigOverrides())
        _, preflight_kwargs = mocked_preflight.call_args
        self.assertFalse(preflight_kwargs["judge_enabled"])
        self.assertIs(preflight_kwargs["judge_provider_config"], judge_config)
        _, runner_kwargs = mocked_run_benchmark.call_args
        self.assertFalse(runner_kwargs["judge_enabled"])
        self.assertIs(runner_kwargs["judge_provider_config"], judge_config)

    def test_judge_enabled_resolves_config_and_passes_it_to_preflight_and_runner(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        judge_config = JudgeProviderConfig(
            provider_name="judge-provider",
            base_url="https://judge.example",
            api_key="judge-key",
            model_name="judge-model",
        )

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "resolve_judge_provider_config",
                return_value=judge_config,
            ) as mocked_resolve:
                with patch.object(
                    module,
                    "run_answer_benchmark_preflight",
                    return_value=AskAnswerBenchmarkPreflightResult(
                        status="ok",
                        provider_name="openai-compatible",
                        model_name="qwen3.6-flash-2026-04-16",
                        message="Answer benchmark preflight passed.",
                    ),
                ) as mocked_preflight:
                    with patch.object(
                        module,
                        "run_ask_answer_benchmark",
                        return_value={"run_status": "passed"},
                    ) as mocked_run_benchmark:
                        exit_code = module.main(
                            [
                                "--mode",
                                "smoke",
                                "--output",
                                "/tmp/answer-benchmark.json",
                                "--judge",
                                "enabled",
                            ]
                        )

        self.assertEqual(exit_code, 0)
        mocked_resolve.assert_called_once_with(mocked_settings, JudgeConfigOverrides())
        _, preflight_kwargs = mocked_preflight.call_args
        self.assertTrue(preflight_kwargs["judge_enabled"])
        self.assertIs(preflight_kwargs["judge_provider_config"], judge_config)
        _, runner_kwargs = mocked_run_benchmark.call_args
        self.assertTrue(runner_kwargs["judge_enabled"])
        self.assertIs(runner_kwargs["judge_provider_config"], judge_config)

    def test_judge_cli_flags_override_settings_derived_config(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        judge_config = JudgeProviderConfig(
            provider_name="cli-provider",
            base_url="https://cli-judge.example",
            api_key="cli-key",
            model_name="cli-model",
        )

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "resolve_judge_provider_config",
                return_value=judge_config,
            ) as mocked_resolve:
                with patch.object(
                    module,
                    "run_answer_benchmark_preflight",
                    return_value=AskAnswerBenchmarkPreflightResult(
                        status="ok",
                        provider_name="openai-compatible",
                        model_name="qwen3.6-flash-2026-04-16",
                        message="Answer benchmark preflight passed.",
                    ),
                ) as mocked_preflight:
                    with patch.object(
                        module,
                        "run_ask_answer_benchmark",
                        return_value={"run_status": "passed"},
                    ) as mocked_run_benchmark:
                        exit_code = module.main(
                            [
                                "--mode",
                                "smoke",
                                "--output",
                                "/tmp/answer-benchmark.json",
                                "--judge",
                                "enabled",
                                "--judge-provider-name",
                                "cli-provider",
                                "--judge-base-url",
                                "https://cli-judge.example",
                                "--judge-api-key",
                                "cli-key",
                                "--judge-model",
                                "cli-model",
                            ]
                        )

        self.assertEqual(exit_code, 0)
        mocked_resolve.assert_called_once_with(
            mocked_settings,
            JudgeConfigOverrides(
                provider_name="cli-provider",
                base_url="https://cli-judge.example",
                api_key="cli-key",
                model="cli-model",
            ),
        )
        _, preflight_kwargs = mocked_preflight.call_args
        self.assertIs(preflight_kwargs["judge_provider_config"], judge_config)
        _, runner_kwargs = mocked_run_benchmark.call_args
        self.assertIs(runner_kwargs["judge_provider_config"], judge_config)

    def test_judge_model_default_preview_value_is_accepted_and_forwarded(self) -> None:
        module = load_cli_module()
        mocked_settings = Mock()
        judge_config = JudgeProviderConfig(
            provider_name="judge-provider",
            base_url="https://judge.example",
            api_key="judge-key",
            model_name="qwen3.6-max-preview",
        )

        with patch.object(module, "get_settings", return_value=mocked_settings):
            with patch.object(
                module,
                "resolve_judge_provider_config",
                return_value=judge_config,
            ) as mocked_resolve:
                with patch.object(
                    module,
                    "run_answer_benchmark_preflight",
                    return_value=AskAnswerBenchmarkPreflightResult(
                        status="ok",
                        provider_name="openai-compatible",
                        model_name="qwen3.6-flash-2026-04-16",
                        message="Answer benchmark preflight passed.",
                    ),
                ) as mocked_preflight:
                    with patch.object(
                        module,
                        "run_ask_answer_benchmark",
                        return_value={"run_status": "passed"},
                    ) as mocked_run_benchmark:
                        exit_code = module.main(
                            [
                                "--mode",
                                "smoke",
                                "--output",
                                "/tmp/answer-benchmark.json",
                                "--judge",
                                "enabled",
                                "--judge-model",
                                "qwen3.6-max-preview",
                            ]
                        )

        self.assertEqual(exit_code, 0)
        mocked_resolve.assert_called_once_with(
            mocked_settings,
            JudgeConfigOverrides(model="qwen3.6-max-preview"),
        )
        _, preflight_kwargs = mocked_preflight.call_args
        self.assertIs(preflight_kwargs["judge_provider_config"], judge_config)
        _, runner_kwargs = mocked_run_benchmark.call_args
        self.assertIs(runner_kwargs["judge_provider_config"], judge_config)

    def test_judge_enabled_blank_base_url_fails_real_preflight_before_runner(self) -> None:
        module = load_cli_module()
        settings = replace(
            get_settings(),
            cloud_provider_name="openai-compatible",
            cloud_base_url="https://answer.example",
            cloud_api_key="answer-key",
            cloud_chat_model="qwen3.6-flash-2026-04-16",
            judge_provider_name="judge-provider",
            judge_base_url="https://judge.example",
            judge_api_key="judge-key",
            judge_model="judge-model",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            dataset_path = Path(temp_dir) / "ask_benchmark.json"
            dataset_path.write_text('{"schema_version": 1, "cases": []}', encoding="utf-8")

            with patch.object(module, "get_settings", return_value=settings):
                with patch.object(module, "run_ask_answer_benchmark") as mocked_run_benchmark:
                    stderr_buffer = io.StringIO()
                    with contextlib.redirect_stderr(stderr_buffer):
                        exit_code = module.main(
                            [
                                "--mode",
                                "smoke",
                                "--dataset",
                                str(dataset_path),
                                "--judge",
                                "enabled",
                                "--judge-base-url",
                                "   ",
                            ]
                        )

        self.assertEqual(exit_code, 1)
        mocked_run_benchmark.assert_not_called()
        stderr = stderr_buffer.getvalue().lower()
        self.assertIn("judge provider", stderr)
        self.assertIn("--judge-base-url", stderr)


if __name__ == "__main__":
    unittest.main()
