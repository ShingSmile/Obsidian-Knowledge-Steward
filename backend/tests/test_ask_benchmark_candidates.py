from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.benchmark.ask_dataset import (
    AskBenchmarkBacklogItem,
    AskBenchmarkCase,
    AskBenchmarkDataset,
    AskBenchmarkLocator,
    AskBenchmarkReviewBacklog,
)
from app.benchmark.ask_dataset_candidates import build_candidate_batch


class AskBenchmarkCandidateTests(unittest.TestCase):
    def _write_note(self, vault_root: Path, relative_path: str, text: str) -> Path:
        note_path = vault_root / relative_path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(text, encoding="utf-8")
        return note_path

    def _make_locator(
        self,
        *,
        note_path: str,
        heading_path: str,
        excerpt_anchor: str,
        line_range: dict[str, int] | None = None,
    ) -> AskBenchmarkLocator:
        payload: dict[str, object] = {
            "note_path": note_path,
            "heading_path": heading_path,
            "excerpt_anchor": excerpt_anchor,
        }
        if line_range is not None:
            payload["line_range"] = line_range
        return AskBenchmarkLocator.model_construct(**payload)

    def _make_case(
        self,
        *,
        case_id: str,
        user_query: str,
        note_path: str,
        heading_path: str,
        excerpt_anchor: str,
        bucket: str = "single_hop",
    ) -> AskBenchmarkCase:
        return AskBenchmarkCase.model_construct(
            case_id=case_id,
            bucket=bucket,
            user_query=user_query,
            source_origin="sample_vault",
            expected_relevant_paths=[note_path],
            expected_relevant_locators=[
                self._make_locator(
                    note_path=note_path,
                    heading_path=heading_path,
                    excerpt_anchor=excerpt_anchor,
                )
            ],
            expected_facts=[excerpt_anchor],
            forbidden_claims=[],
            allow_tool=False,
            expected_tool_names=[],
            allow_retrieval_only=True,
            should_generate_answer=True,
            review_status="approved",
            review_notes="seed",
        )

    def _empty_dataset(self) -> AskBenchmarkDataset:
        return AskBenchmarkDataset.model_construct(schema_version=1, cases=[])

    def _empty_backlog(self) -> AskBenchmarkReviewBacklog:
        return AskBenchmarkReviewBacklog.model_construct(schema_version=1, items=[])

    def test_build_candidate_batch_returns_five_candidates_when_enough_unused_source_material_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(
                vault_root,
                "日常/2024-03-14_星期四.md",
                """# 一、工作任务

- [x] 完成 digest graph
- [ ] 清理 backlog

# 二、今日总结

今天接通了 DAILY_DIGEST。
补充说明：今天先整理再收口。
""",
            )
            self._write_note(
                vault_root,
                "日常/2024-03-15_星期五.md",
                """# Summary

## Highlights

Ship the benchmark.
""",
            )

            batch = build_candidate_batch(
                vault_root=vault_root,
                approved_dataset=self._empty_dataset(),
                backlog=self._empty_backlog(),
                count=5,
            )

            self.assertEqual(len(batch), 5)

    def test_build_candidate_batch_defaults_source_origin_to_sample_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(
                vault_root,
                "日常/2024-03-14_星期四.md",
                """# 一、工作任务

- [x] 完成 digest graph

# 二、今日总结

今天接通了 DAILY_DIGEST。
""",
            )

            batch = build_candidate_batch(
                vault_root=vault_root,
                approved_dataset=self._empty_dataset(),
                backlog=self._empty_backlog(),
                count=5,
            )

            self.assertTrue(batch)
            self.assertTrue(all(item.source_origin == "sample_vault" for item in batch))

    def test_build_candidate_batch_uses_note_path_and_heading_path_locators(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(
                vault_root,
                "日常/2024-03-14_星期四.md",
                """# 一、工作任务

- [x] 完成 digest graph

# 二、今日总结

今天接通了 DAILY_DIGEST。
""",
            )

            batch = build_candidate_batch(
                vault_root=vault_root,
                approved_dataset=self._empty_dataset(),
                backlog=self._empty_backlog(),
                count=5,
            )

            for item in batch:
                self.assertTrue(item.expected_relevant_locators)
                locator = item.expected_relevant_locators[0]
                self.assertEqual(locator.note_path, "日常/2024-03-14_星期四.md")
                self.assertTrue(locator.heading_path)
                self.assertTrue(locator.excerpt_anchor)

    def test_build_candidate_batch_skips_existing_case_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(
                vault_root,
                "日常/2024-03-14_星期四.md",
                """# 一、工作任务

- [x] 完成 digest graph
- [ ] 清理 backlog

# 二、今日总结

今天接通了 DAILY_DIGEST。
补充说明：今天先整理再收口。
""",
            )
            self._write_note(
                vault_root,
                "日常/2024-03-15_星期五.md",
                """# Summary

## Highlights

Ship the benchmark.
""",
            )
            approved = AskBenchmarkDataset(
                schema_version=1,
                cases=[
                    self._make_case(
                        case_id="ask_case_001",
                        user_query="这篇笔记的工作任务部分讲了什么？",
                        note_path="日常/2024-03-14_星期四.md",
                        heading_path="一、工作任务",
                        excerpt_anchor="完成 digest graph",
                    )
                ],
            )
            backlog = AskBenchmarkReviewBacklog(
                schema_version=1,
                items=[
                    AskBenchmarkBacklogItem.model_construct(
                        case_id="ask_backlog_001",
                        bucket="single_hop",
                        user_query="这篇笔记列了哪些待办？",
                        source_origin="sample_vault",
                        expected_relevant_paths=["日常/2024-03-14_星期四.md"],
                        expected_relevant_locators=[
                            self._make_locator(
                                note_path="日常/2024-03-14_星期四.md",
                                heading_path="一、工作任务",
                                excerpt_anchor="清理 backlog",
                            )
                        ],
                        expected_facts=["清理 backlog"],
                        forbidden_claims=[],
                        allow_tool=False,
                        expected_tool_names=[],
                        allow_retrieval_only=True,
                        should_generate_answer=True,
                        review_status="revise",
                        review_notes="seed",
                    )
                ],
            )

            batch = build_candidate_batch(
                vault_root=vault_root,
                approved_dataset=approved,
                backlog=backlog,
                count=5,
            )

            self.assertEqual(len(batch), 5)
            self.assertNotIn(
                "这篇笔记的工作任务部分讲了什么？",
                {item.user_query for item in batch},
            )
            self.assertNotIn(
                "这篇笔记列了哪些待办？",
                {item.user_query for item in batch},
            )

    def test_build_candidate_batch_orders_conservative_queries_before_freer_paraphrase(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(
                vault_root,
                "日常/2024-03-14_星期四.md",
                """# 一、工作任务

- [x] 完成 digest graph
- [ ] 清理 backlog

# 二、今日总结

今天接通了 DAILY_DIGEST。
补充说明：今天先整理再收口。
""",
            )
            self._write_note(
                vault_root,
                "日常/2024-03-15_星期五.md",
                """# Summary

## Highlights

Ship the benchmark.
""",
            )

            batch = build_candidate_batch(
                vault_root=vault_root,
                approved_dataset=self._empty_dataset(),
                backlog=self._empty_backlog(),
                count=5,
            )

            self.assertEqual(
                [item.user_query for item in batch[:5]],
                [
                    "这篇笔记的工作任务部分讲了什么？",
                    "这篇笔记列了哪些待办？",
                    "2024-03-14 这天做了什么？",
                    "今天接通了 DAILY_DIGEST。这段在说什么？",
                    "这篇笔记主要讲了什么？",
                ],
            )


