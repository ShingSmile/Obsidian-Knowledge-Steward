from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from urllib import error as urllib_error

from app.benchmark.ask_answer_benchmark_judge import (
    DEFAULT_JUDGE_MODEL,
    JUDGE_TIMEOUT_SECONDS,
    JUDGE_VERDICT_POINTS,
    JudgeCitation,
    JudgeConfigOverrides,
    JudgeInput,
    JudgeProviderConfig,
    build_judge_messages,
    parse_judge_response_payload,
    resolve_judge_provider_config,
    score_answer_with_judge,
)
from app.config import Settings


def _settings(**overrides: object) -> Settings:
    defaults = {
        "cloud_provider_name": "cloud-provider",
        "cloud_base_url": "https://cloud.example",
        "cloud_api_key": "cloud-key",
        "cloud_chat_model": "cloud-chat-model",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _judge_input() -> JudgeInput:
    return JudgeInput(
        case_id="ask_case_001",
        variant_id="hybrid_assembly_gate",
        user_query="What changed in Alpha?",
        expected_facts=["Alpha shipped the new indexer.", "Beta remains disabled."],
        forbidden_claims=["Gamma was deleted."],
        answer_text="Alpha shipped the new indexer. Beta remains disabled. [1]",
        citations=[
            JudgeCitation(
                citation_id="1",
                source_path="Notes/Alpha.md",
                snippet="Alpha shipped the new indexer in April.",
            ),
            JudgeCitation(
                citation_id="2",
                source_path="Notes/Beta.md",
                snippet="Beta remains disabled pending review.",
            ),
        ],
        ask_result_mode="generated_answer",
        runtime_faithfulness={
            "outcome": "allow",
            "score": 0.91,
            "backend": "runtime",
        },
    )


def _provider_payload(content: object) -> bytes:
    return json.dumps(
        {"choices": [{"message": {"content": content}}]},
        ensure_ascii=False,
    ).encode("utf-8")


class _Response:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


class AskAnswerBenchmarkJudgeTest(unittest.TestCase):
    def test_provider_config_precedence_uses_cli_then_judge_settings_then_cloud_without_cloud_model(self) -> None:
        settings = _settings(
            judge_provider_name="judge-provider",
            judge_base_url="https://judge.example",
            judge_api_key="judge-key",
            judge_model="judge-model",
        )

        cli_config = resolve_judge_provider_config(
            settings,
            JudgeConfigOverrides(
                provider_name="cli-provider",
                base_url="https://cli.example",
                api_key="cli-key",
                model="cli-model",
            ),
        )

        self.assertEqual(
            cli_config,
            JudgeProviderConfig(
                provider_name="cli-provider",
                base_url="https://cli.example",
                api_key="cli-key",
                model_name="cli-model",
            ),
        )
        self.assertEqual(cli_config.model_name, "cli-model")

        settings_config = resolve_judge_provider_config(settings, JudgeConfigOverrides())

        self.assertEqual(
            settings_config,
            JudgeProviderConfig(
                provider_name="judge-provider",
                base_url="https://judge.example",
                api_key="judge-key",
                model_name="judge-model",
            ),
        )
        self.assertEqual(settings_config.model_name, "judge-model")

        fallback_config = resolve_judge_provider_config(
            _settings(
                judge_provider_name="",
                judge_base_url="",
                judge_api_key="",
                judge_model="",
                cloud_chat_model="must-not-be-used",
            ),
            JudgeConfigOverrides(),
        )

        self.assertEqual(
            fallback_config,
            JudgeProviderConfig(
                provider_name="cloud-provider",
                base_url="https://cloud.example",
                api_key="cloud-key",
                model_name=DEFAULT_JUDGE_MODEL,
            ),
        )
        self.assertEqual(fallback_config.model_name, DEFAULT_JUDGE_MODEL)
        self.assertNotEqual(fallback_config.model_name, "must-not-be-used")

    def test_prompt_message_construction_includes_case_data_and_citation_snippets(self) -> None:
        messages = build_judge_messages(_judge_input())

        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        user_payload = json.loads(messages[1]["content"])
        self.assertEqual(user_payload["case_id"], "ask_case_001")
        self.assertEqual(user_payload["variant_id"], "hybrid_assembly_gate")
        self.assertEqual(user_payload["ask_result_mode"], "generated_answer")
        self.assertEqual(
            user_payload["runtime_faithfulness"],
            {
                "outcome": "allow",
                "score": 0.91,
                "backend": "runtime",
            },
        )
        rendered = "\n".join(message["content"] for message in messages)
        self.assertIn("What changed in Alpha?", rendered)
        self.assertIn("Alpha shipped the new indexer.", rendered)
        self.assertIn("Beta remains disabled.", rendered)
        self.assertIn("Gamma was deleted.", rendered)
        self.assertIn("Alpha shipped the new indexer. Beta remains disabled. [1]", rendered)
        self.assertIn("Notes/Alpha.md", rendered)
        self.assertIn("Alpha shipped the new indexer in April.", rendered)
        self.assertIn("Notes/Beta.md", rendered)
        self.assertIn("Beta remains disabled pending review.", rendered)

    def test_all_verdicts_parse_with_expected_points(self) -> None:
        for verdict, expected_points in JUDGE_VERDICT_POINTS.items():
            with self.subTest(verdict=verdict):
                score = parse_judge_response_payload(
                    json.dumps(
                        {
                            "verdict": verdict,
                            "matched_facts": ["fact-a"],
                            "missed_facts": ["fact-b"],
                            "unsupported_claims": ["claim-c"],
                            "reason": "The answer was evaluated.",
                        },
                        ensure_ascii=False,
                    )
                )

                self.assertEqual(score.judge_status, "scored")
                self.assertEqual(score.verdict, verdict)
                self.assertEqual(score.correctness_points, expected_points)
                self.assertEqual(score.matched_facts, ["fact-a"])
                self.assertEqual(score.missed_facts, ["fact-b"])
                self.assertEqual(score.unsupported_claims, ["claim-c"])
                self.assertEqual(score.reason, "The answer was evaluated.")

    def test_invalid_json_returns_parse_error_score(self) -> None:
        score = parse_judge_response_payload("{not json")

        self.assertEqual(score.judge_status, "parse_error")
        self.assertIsNone(score.verdict)
        self.assertIsNone(score.correctness_points)
        self.assertEqual(score.matched_facts, [])
        self.assertEqual(score.missed_facts, [])
        self.assertEqual(score.unsupported_claims, [])
        self.assertIsNone(score.reason)
        self.assertEqual(score.error_reason, "invalid_json")
        self.assertEqual(score.raw_response_excerpt, "{not json")

    def test_missing_required_fields_returns_invalid_schema_score(self) -> None:
        invalid_payloads = [
            {"matched_facts": [], "missed_facts": [], "unsupported_claims": [], "reason": "missing verdict"},
            {"verdict": "correct", "matched_facts": "fact", "missed_facts": [], "unsupported_claims": [], "reason": "bad matched"},
            {"verdict": "correct", "matched_facts": [], "missed_facts": "fact", "unsupported_claims": [], "reason": "bad missed"},
            {"verdict": "correct", "matched_facts": [], "missed_facts": [], "unsupported_claims": "claim", "reason": "bad unsupported"},
            {"verdict": "correct", "matched_facts": [], "missed_facts": [], "unsupported_claims": [], "reason": ""},
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                score = parse_judge_response_payload(json.dumps(payload, ensure_ascii=False))

                self.assertEqual(score.judge_status, "invalid_schema")
                self.assertIsNone(score.verdict)
                self.assertIsNone(score.correctness_points)

    def test_non_string_list_elements_return_invalid_schema_score(self) -> None:
        invalid_payloads = [
            {
                "verdict": "correct",
                "matched_facts": [{"text": "not a string"}],
                "missed_facts": [],
                "unsupported_claims": [],
                "reason": "bad matched element",
            },
            {
                "verdict": "correct",
                "matched_facts": [],
                "missed_facts": [7],
                "unsupported_claims": [],
                "reason": "bad missed element",
            },
            {
                "verdict": "correct",
                "matched_facts": [],
                "missed_facts": [],
                "unsupported_claims": [None],
                "reason": "bad unsupported element",
            },
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                score = parse_judge_response_payload(json.dumps(payload, ensure_ascii=False))

                self.assertEqual(score.judge_status, "invalid_schema")
                self.assertIsNone(score.verdict)
                self.assertIsNone(score.correctness_points)
                self.assertEqual(score.matched_facts, [])
                self.assertEqual(score.missed_facts, [])
                self.assertEqual(score.unsupported_claims, [])

    def test_openai_compatible_provider_sends_expected_payload_and_extracts_content(self) -> None:
        response_text = json.dumps(
            {
                "verdict": "mostly_correct",
                "matched_facts": ["Alpha shipped the new indexer."],
                "missed_facts": ["Beta remains disabled."],
                "unsupported_claims": [],
                "reason": "The answer covers the main fact.",
            },
            ensure_ascii=False,
        )
        provider_config = JudgeProviderConfig(
            provider_name="openai-compatible",
            base_url="https://judge.example/v1",
            api_key="secret-key",
            model_name="judge-model",
        )

        with patch(
            "app.benchmark.ask_answer_benchmark_judge.urllib_request.urlopen",
            return_value=_Response(_provider_payload(response_text)),
        ) as urlopen:
            score = score_answer_with_judge(_judge_input(), provider_config)

        self.assertEqual(score.judge_status, "scored")
        self.assertEqual(score.verdict, "mostly_correct")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://judge.example/v1/chat/completions")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], JUDGE_TIMEOUT_SECONDS)
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-key")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "judge-model")
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["messages"], build_judge_messages(_judge_input()))

    def test_provider_extracts_content_from_openai_text_parts(self) -> None:
        response_text = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "text", "text": "{\"verdict\":\"partial\","},
                            {"type": "image_url", "image_url": {"url": "ignored"}},
                            {
                                "type": "text",
                                "text": "\"matched_facts\":[],\"missed_facts\":[],\"unsupported_claims\":[],\"reason\":\"ok\"}",
                            },
                        ]
                    }
                }
            ]
        }
        provider_config = JudgeProviderConfig(
            provider_name="openai-compatible",
            base_url="https://judge.example/chat/completions",
            api_key="",
            model_name="judge-model",
        )

        with patch(
            "app.benchmark.ask_answer_benchmark_judge.urllib_request.urlopen",
            return_value=_Response(json.dumps(response_text).encode("utf-8")),
        ) as urlopen:
            score = score_answer_with_judge(_judge_input(), provider_config)

        self.assertEqual(score.judge_status, "scored")
        self.assertEqual(score.verdict, "partial")
        self.assertEqual(urlopen.call_args.args[0].full_url, "https://judge.example/chat/completions")
        self.assertIsNone(urlopen.call_args.args[0].get_header("Authorization"))

    def test_provider_connection_failures_and_invalid_payload_map_to_provider_unavailable(self) -> None:
        failures = [
            urllib_error.URLError("connection refused"),
            OSError("network unavailable"),
            ValueError("bad url"),
            _Response(b"{not json"),
            _Response(b"\xff\xfe\xfa"),
            _Response(json.dumps({"choices": []}).encode("utf-8")),
        ]
        provider_config = JudgeProviderConfig(
            provider_name="openai-compatible",
            base_url="https://judge.example",
            api_key="",
            model_name="judge-model",
        )

        for failure in failures:
            with self.subTest(failure=failure):
                patch_kwargs = {"side_effect": failure}
                if isinstance(failure, _Response):
                    patch_kwargs = {"return_value": failure}
                with patch(
                    "app.benchmark.ask_answer_benchmark_judge.urllib_request.urlopen",
                    **patch_kwargs,
                ):
                    score = score_answer_with_judge(_judge_input(), provider_config)

                self.assertEqual(score.judge_status, "provider_unavailable")
                self.assertIsNone(score.verdict)
                self.assertIsNone(score.correctness_points)

    def test_missing_base_url_maps_to_provider_unavailable_without_urlopen(self) -> None:
        provider_config = JudgeProviderConfig(
            provider_name="openai-compatible",
            base_url="",
            api_key="",
            model_name="judge-model",
        )

        with patch("app.benchmark.ask_answer_benchmark_judge.urllib_request.urlopen") as urlopen:
            score = score_answer_with_judge(_judge_input(), provider_config)

        self.assertEqual(score.judge_status, "provider_unavailable")
        self.assertEqual(score.error_reason, "missing_judge_base_url")
        self.assertIsNone(score.verdict)
        self.assertIsNone(score.correctness_points)
        urlopen.assert_not_called()

    def test_provider_timeout_maps_to_timeout(self) -> None:
        provider_config = JudgeProviderConfig(
            provider_name="openai-compatible",
            base_url="https://judge.example",
            api_key="",
            model_name="judge-model",
        )

        with patch(
            "app.benchmark.ask_answer_benchmark_judge.urllib_request.urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            score = score_answer_with_judge(_judge_input(), provider_config)

        self.assertEqual(score.judge_status, "timeout")
        self.assertIsNone(score.verdict)
        self.assertIsNone(score.correctness_points)


if __name__ == "__main__":
    unittest.main()
