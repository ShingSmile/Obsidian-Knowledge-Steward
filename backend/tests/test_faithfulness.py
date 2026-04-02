from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch

from app.config import get_settings
from app.contracts.workflow import RuntimeFaithfulnessOutcome
from app.quality.faithfulness import (
    build_claim_faithfulness_report,
    build_runtime_faithfulness_signal,
    split_atomic_claims,
)
from app.retrieval.embeddings import EmbeddingBatchResult


class ClaimFaithfulnessCoreTests(unittest.TestCase):
    def test_split_atomic_claims_splits_chinese_sentences_and_bullets(self) -> None:
        claims = split_atomic_claims(
            "Alpha 已完成。\n- Beta 未完成\nGamma 需要复盘；Delta 已归档。"
        )

        self.assertEqual(
            claims,
            [
                "Alpha 已完成",
                "Beta 未完成",
                "Gamma 需要复盘",
                "Delta 已归档",
            ],
        )

    def test_build_claim_faithfulness_report_marks_contradicted_claim(self) -> None:
        report = build_claim_faithfulness_report(
            "Alpha 已完成。",
            evidence_texts=["Alpha 尚未完成，当前没有归档。"],
        )

        self.assertEqual(report["backend"], "lexical_semantic")
        self.assertEqual(report["score"], 0.0)
        self.assertEqual(report["claims"][0]["verdict"], "contradicted")

    def test_build_claim_faithfulness_report_marks_neutral_claim(self) -> None:
        report = build_claim_faithfulness_report(
            "Alpha 已完成。",
            evidence_texts=["Beta 正在规划下一阶段。"],
        )

        self.assertEqual(report["backend"], "lexical_semantic")
        self.assertEqual(report["score"], 0.0)
        self.assertEqual(report["claims"][0]["verdict"], "neutral")

    def test_build_claim_faithfulness_report_uses_embedding_backend_when_available(
        self,
    ) -> None:
        settings = replace(
            get_settings(),
            cloud_base_url="https://example.com",
            cloud_embedding_model="text-embedding-test",
            local_embedding_model="",
        )

        def _fake_embed(texts: list[str], **_: object) -> EmbeddingBatchResult:
            embeddings: list[list[float]] = []
            for text in texts:
                normalized = text.casefold()
                if "alpha" in normalized:
                    embeddings.append([1.0, 0.0])
                else:
                    embeddings.append([0.0, 1.0])
            return EmbeddingBatchResult(
                embeddings=embeddings,
                provider_key="cloud",
                provider_name=settings.cloud_provider_name,
                model_name=settings.cloud_embedding_model,
            )

        with patch("app.quality.faithfulness.embed_texts", side_effect=_fake_embed):
            report = build_claim_faithfulness_report(
                "Alpha 已完成。",
                evidence_texts=["Alpha 当前状态为已完成，并已归档。"],
                settings=settings,
            )

        self.assertEqual(report["backend"], "embedding_semantic")
        self.assertEqual(report["score"], 1.0)
        self.assertEqual(report["claims"][0]["verdict"], "entailed")

    def test_build_runtime_faithfulness_signal_flags_low_confidence_when_score_below_threshold(
        self,
    ) -> None:
        signal = build_runtime_faithfulness_signal(
            "Alpha 已完成。",
            evidence_texts=["Beta 正在规划下一阶段。"],
            failure_outcome=RuntimeFaithfulnessOutcome.LOW_CONFIDENCE,
        )

        self.assertEqual(signal.outcome, RuntimeFaithfulnessOutcome.LOW_CONFIDENCE)
        self.assertEqual(signal.unsupported_claim_count, 1)
        self.assertEqual(signal.threshold, 0.67)

    def test_build_runtime_faithfulness_signal_allows_supported_claims(self) -> None:
        signal = build_runtime_faithfulness_signal(
            "Alpha 已完成。",
            evidence_texts=["Alpha 当前状态为已完成，并已归档。"],
            failure_outcome=RuntimeFaithfulnessOutcome.LOW_CONFIDENCE,
        )

        self.assertEqual(signal.outcome, RuntimeFaithfulnessOutcome.ALLOW)
        self.assertEqual(signal.unsupported_claim_count, 0)


if __name__ == "__main__":
    unittest.main()
