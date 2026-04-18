from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.benchmark.ask_dataset import (
    ASK_BENCHMARK_DIR,
    AskBenchmarkBacklogItem,
    AskBenchmarkCase,
    AskBenchmarkDataset,
    AskBenchmarkLocator,
    AskBenchmarkReviewBacklog,
    load_ask_benchmark_backlog,
    load_ask_benchmark_dataset,
    write_ask_benchmark_backlog,
    write_ask_benchmark_dataset,
)


class AskBenchmarkDatasetTests(unittest.TestCase):
    def _build_case(self, bucket: str, review_status: str = "approved") -> AskBenchmarkCase:
        return AskBenchmarkCase(
            case_id=f"ask_case_{bucket}",
            bucket=bucket,
            user_query="总结这篇笔记",
            source_origin="sample_vault",
            expected_relevant_paths=["日常/2024-03-14_星期四.md"],
            expected_relevant_locators=[
                AskBenchmarkLocator(
                    note_path="日常/2024-03-14_星期四.md",
                    heading_path="一、工作任务",
                    excerpt_anchor="完成 digest graph",
                )
            ],
            expected_facts=["今天接通了 DAILY_DIGEST。"],
            forbidden_claims=[],
            allow_tool=False,
            expected_tool_names=[],
            allow_retrieval_only=False,
            should_generate_answer=True,
            review_status=review_status,
            review_notes="seed",
        )

    def test_case_accepts_only_allowed_buckets(self) -> None:
        allowed_buckets = (
            "single_hop",
            "multi_hop",
            "metadata_filter",
            "abstain_or_no_hit",
            "tool_allowed",
        )

        for bucket in allowed_buckets:
            case = self._build_case(bucket)
            self.assertEqual(case.bucket, bucket)

    def test_case_rejects_unknown_bucket(self) -> None:
        with self.assertRaisesRegex(ValueError, "bucket"):
            self._build_case("bad_bucket")

    def test_case_rejects_non_approved_review_status(self) -> None:
        with self.assertRaisesRegex(ValueError, "review_status"):
            self._build_case("single_hop", review_status="draft")

    def test_formal_dataset_rejects_missing_review_status(self) -> None:
        payload = {
            "case_id": "ask_case_missing_review_status",
            "bucket": "single_hop",
            "user_query": "总结这篇笔记",
            "source_origin": "sample_vault",
            "expected_relevant_paths": ["日常/2024-03-14_星期四.md"],
            "expected_relevant_locators": [
                {
                    "note_path": "日常/2024-03-14_星期四.md",
                    "heading_path": "一、工作任务",
                    "excerpt_anchor": "完成 digest graph",
                }
            ],
            "expected_facts": ["今天接通了 DAILY_DIGEST。"],
            "forbidden_claims": [],
            "allow_tool": False,
            "expected_tool_names": [],
            "allow_retrieval_only": False,
            "should_generate_answer": True,
            "review_notes": "seed",
        }

        with self.assertRaisesRegex(ValueError, "review_status"):
            AskBenchmarkCase.from_dict(payload)

    def test_locator_requires_core_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "note_path"):
            AskBenchmarkLocator(
                note_path="",
                heading_path="一、工作任务",
                excerpt_anchor="完成 digest graph",
            )

        with self.assertRaisesRegex(ValueError, "heading_path"):
            AskBenchmarkLocator(
                note_path="日常/2024-03-14_星期四.md",
                heading_path="",
                excerpt_anchor="完成 digest graph",
            )

        with self.assertRaisesRegex(ValueError, "excerpt_anchor"):
            AskBenchmarkLocator(
                note_path="日常/2024-03-14_星期四.md",
                heading_path="一、工作任务",
                excerpt_anchor="",
            )

    def test_seeded_dataset_file_has_minimal_shape(self) -> None:
        payload = json.loads((ASK_BENCHMARK_DIR / "ask_benchmark_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(payload, {"schema_version": 1, "cases": []})

    def test_seeded_backlog_file_has_minimal_shape(self) -> None:
        payload = json.loads((ASK_BENCHMARK_DIR / "ask_benchmark_review_backlog.json").read_text(encoding="utf-8"))
        self.assertEqual(payload, {"schema_version": 1, "items": []})

    def test_dataset_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ask_benchmark_cases.json"
            dataset = AskBenchmarkDataset(
                cases=[
                    AskBenchmarkCase(
                        case_id="ask_case_round_trip",
                        bucket="single_hop",
                        user_query="总结这篇笔记",
                        source_origin="sample_vault",
                        expected_relevant_paths=["日常/2024-03-14_星期四.md"],
                        expected_relevant_locators=[
                            AskBenchmarkLocator(
                                note_path="日常/2024-03-14_星期四.md",
                                heading_path="一、工作任务",
                                excerpt_anchor="完成 digest graph",
                            )
                        ],
                        expected_facts=["今天接通了 DAILY_DIGEST。"],
                        forbidden_claims=[],
                        allow_tool=False,
                        expected_tool_names=[],
                        allow_retrieval_only=False,
                        should_generate_answer=True,
                        review_status="approved",
                        review_notes="seed",
                    )
                ]
            )
            write_ask_benchmark_dataset(dataset, path)

            loaded = load_ask_benchmark_dataset(path)
            self.assertEqual(loaded, dataset)

    def test_backlog_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ask_benchmark_review_backlog.json"
            backlog = AskBenchmarkReviewBacklog(
                items=[
                    AskBenchmarkBacklogItem(
                        case_id="ask_case_backlog_round_trip",
                        bucket="multi_hop",
                        user_query="补充这条线索来自哪两篇笔记",
                        source_origin="fixture",
                        expected_relevant_paths=["A.md", "B.md"],
                        expected_relevant_locators=[
                            AskBenchmarkLocator(
                                note_path="A.md",
                                heading_path="Background",
                                excerpt_anchor="alpha",
                            )
                        ],
                        expected_facts=["A 和 B 共同说明了这件事。"],
                        forbidden_claims=[],
                        allow_tool=False,
                        expected_tool_names=[],
                        allow_retrieval_only=True,
                        should_generate_answer=True,
                        review_status="revise",
                        review_notes="needs tightening",
                    )
                ]
            )
            write_ask_benchmark_backlog(backlog, path)

            loaded = load_ask_benchmark_backlog(path)
            self.assertEqual(loaded, backlog)
