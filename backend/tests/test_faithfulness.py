from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch

from app.config import get_settings
from app.contracts.workflow import (
    AskCitation,
    AskResultMode,
    AskWorkflowResult,
    RetrievedChunkCandidate,
    RuntimeFaithfulnessOutcome,
)
from app.quality.faithfulness import (
    build_claim_faithfulness_report,
    build_runtime_ask_faithfulness_signal,
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

    def test_split_atomic_claims_skips_lead_in_lines_for_chinese_list_answers(
        self,
    ) -> None:
        claims = split_atomic_claims(
            "根据2023-06-12的今日进程记录，结算重构功能主要总结了以下四个模块：\n"
            "1. 批次结算页面：涵盖状态变化、基础信息、销售详情、结算历史与未结金额等展示内容。\n"
            "2. 结算操作界面：包含结算均价设置、时间筛选、新增结算单备注等功能，并明确默认全部勾选与费用项不可更改等注意点。"
        )

        self.assertEqual(
            claims,
            [
                "批次结算页面：涵盖状态变化、基础信息、销售详情、结算历史与未结金额等展示内容",
                "结算操作界面：包含结算均价设置、时间筛选、新增结算单备注等功能，并明确默认全部勾选与费用项不可更改等注意点",
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

    def test_build_claim_faithfulness_report_does_not_treat_incidental_negation_as_contradiction(
        self,
    ) -> None:
        report = build_claim_faithfulness_report(
            "批次结算页面。",
            evidence_texts=["批次结算页面：销售详情（已结清不支持代卖费用设置与添加费用）。"],
        )

        self.assertEqual(report["backend"], "lexical_semantic")
        self.assertEqual(report["score"], 1.0)
        self.assertEqual(report["claims"][0]["verdict"], "entailed")

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

    def test_build_claim_faithfulness_report_supports_chinese_multiline_list_summary(
        self,
    ) -> None:
        report = build_claim_faithfulness_report(
            "根据2023-06-12的今日进程记录，结算重构功能主要总结了以下四个模块：\n"
            "1. 批次结算页面：涵盖状态变化、基础信息、销售详情、结算历史与未结金额等展示内容。\n"
            "2. 结算操作界面：包含结算均价设置、时间筛选、新增结算单备注等功能，并明确默认全部勾选与费用项不可更改等注意点。\n"
            "3. 结算详情：重点配置结算均价设置以展示原始均价、原始货款及优惠信息。\n"
            "4. 货主管理详情页面：包含付款记录、买家赊欠、结算金额/未付款/已付款跳转结算单页面及结算单详情等内容。",
            evidence_texts=[
                "\n".join(
                    [
                        "结算重构功能总结：",
                        "1. 批次结算页面：",
                        "（1）状态变化：在售、售罄、结清",
                        "（2）页面展示：",
                        "基础信息",
                        "销售详情",
                        "结算历史",
                        "未结金额",
                        "2. 结算操作界面：",
                        "功能点：结算均价设置、时间筛选、新增结算单备注",
                        "注意点：默认全部勾选、费用项不可更改",
                        "3. 结算详情：",
                        "注意点：配置结算均价设置展示原始均价、原始货款、优惠",
                        "4. 货主管理详情页面：",
                        "付款记录",
                        "买家赊欠",
                        "结算金额、未付款、已付款-跳转结算单页面",
                        "结算单详情",
                    ]
                )
            ],
        )

        self.assertEqual(report["backend"], "lexical_semantic")
        self.assertEqual(report["score"], 1.0)
        self.assertEqual(
            report["verdict_breakdown"],
            {"entailed": 4, "contradicted": 0, "neutral": 0},
        )

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

    def test_build_runtime_ask_faithfulness_signal_uses_all_prompt_candidates(
        self,
    ) -> None:
        ask_result = AskWorkflowResult(
            mode=AskResultMode.GENERATED_ANSWER,
            query="2023-06-12 的今日进程总结了哪些结算重构功能模块？",
            answer=(
                "1. 批次结算页面[1]\n"
                "2. 结算操作界面[1]\n"
                "3. 结算详情[1]\n"
                "4. 货主管理详情页面[1]"
            ),
            citations=[
                AskCitation(
                    chunk_id="chunk-1",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    start_line=17,
                    end_line=22,
                    score=1.0,
                    snippet="批次结算页面",
                ),
                AskCitation(
                    chunk_id="chunk-2",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    start_line=23,
                    end_line=27,
                    score=0.9,
                    snippet="结算操作界面",
                ),
                AskCitation(
                    chunk_id="chunk-3",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    start_line=28,
                    end_line=31,
                    score=0.8,
                    snippet="结算详情",
                ),
                AskCitation(
                    chunk_id="chunk-4",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    start_line=32,
                    end_line=40,
                    score=0.7,
                    snippet="货主管理详情页面",
                ),
            ],
            retrieved_candidates=[
                RetrievedChunkCandidate(
                    chunk_id="chunk-1",
                    note_id="note-1",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    note_type="daily_note",
                    template_family="plain",
                    daily_note_date="2023-06-12",
                    source_mtime_ns=1,
                    start_line=17,
                    end_line=22,
                    score=1.0,
                    snippet="批次结算页面",
                    text="批次结算页面",
                ),
                RetrievedChunkCandidate(
                    chunk_id="chunk-2",
                    note_id="note-1",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    note_type="daily_note",
                    template_family="plain",
                    daily_note_date="2023-06-12",
                    source_mtime_ns=1,
                    start_line=23,
                    end_line=27,
                    score=0.9,
                    snippet="结算操作界面",
                    text="结算操作界面",
                ),
                RetrievedChunkCandidate(
                    chunk_id="chunk-3",
                    note_id="note-1",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    note_type="daily_note",
                    template_family="plain",
                    daily_note_date="2023-06-12",
                    source_mtime_ns=1,
                    start_line=28,
                    end_line=31,
                    score=0.8,
                    snippet="结算详情",
                    text="结算详情",
                ),
                RetrievedChunkCandidate(
                    chunk_id="chunk-4",
                    note_id="note-1",
                    path="日常/2023-06/2023-06-12_星期一.md",
                    title="三、今日进程",
                    heading_path="三、今日进程",
                    note_type="daily_note",
                    template_family="plain",
                    daily_note_date="2023-06-12",
                    source_mtime_ns=1,
                    start_line=32,
                    end_line=40,
                    score=0.7,
                    snippet="货主管理详情页面",
                    text="货主管理详情页面",
                ),
            ],
        )

        signal = build_runtime_ask_faithfulness_signal(ask_result)

        self.assertEqual(signal.outcome, RuntimeFaithfulnessOutcome.ALLOW)
        self.assertEqual(signal.score, 1.0)
        self.assertEqual(signal.unsupported_claim_count, 0)


if __name__ == "__main__":
    unittest.main()
