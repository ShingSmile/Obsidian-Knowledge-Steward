from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, call, patch

from app.benchmark.ask_dataset import AskBenchmarkCase, AskBenchmarkDataset, AskBenchmarkLocator
from app.benchmark.ask_retrieval_benchmark import (
    TASK_058_V1_BENCHMARK_KIND,
    TASK_058_V1_SCHEMA_VERSION,
    build_default_output_path,
    run_ask_retrieval_benchmark,
    select_task_058_v1_cases,
    write_retrieval_benchmark_result,
)
from app.benchmark.ask_retrieval_modes import RetrievalBenchmarkMode, RetrievalBenchmarkModeError
from app.config import ROOT_DIR, get_settings
from app.contracts.workflow import RetrievedChunkCandidate


def _locator(
    *,
    note_path: str = "Notes/Alpha.md",
    heading_path: str = "Summary",
    excerpt_anchor: str = "alpha evidence",
) -> AskBenchmarkLocator:
    return AskBenchmarkLocator(
        note_path=note_path,
        heading_path=heading_path,
        excerpt_anchor=excerpt_anchor,
    )


def _case(
    *,
    case_id: str,
    bucket: str = "single_hop",
    allow_tool: bool = False,
    locator: AskBenchmarkLocator | None = None,
) -> AskBenchmarkCase:
    return AskBenchmarkCase(
        case_id=case_id,
        bucket=bucket,
        user_query=f"query for {case_id}",
        source_origin="fixture",
        expected_relevant_paths=["Notes/Alpha.md"],
        expected_relevant_locators=[locator or _locator()],
        expected_facts=["fact"],
        forbidden_claims=[],
        allow_tool=allow_tool,
        expected_tool_names=[],
        allow_retrieval_only=True,
        should_generate_answer=False,
        review_status="approved",
        review_notes="ready",
    )


def _dataset(*cases: AskBenchmarkCase) -> AskBenchmarkDataset:
    return AskBenchmarkDataset.model_construct(schema_version=1, cases=list(cases))


def _candidate(
    *,
    chunk_id: str,
    path: str = "Notes/Alpha.md",
    heading_path: str | None = "Summary",
    text: str = "alpha evidence",
    retrieval_source: str = "sqlite_fts",
) -> RetrievedChunkCandidate:
    return RetrievedChunkCandidate(
        retrieval_source=retrieval_source,
        chunk_id=chunk_id,
        note_id=f"note-{chunk_id}",
        path=path,
        title="Alpha",
        heading_path=heading_path,
        note_type="note",
        template_family="default",
        daily_note_date=None,
        source_mtime_ns=1,
        start_line=1,
        end_line=2,
        score=1.0,
        snippet="snippet",
        text=text,
    )


class AskRetrievalBenchmarkTest(unittest.TestCase):
    def test_select_task_058_v1_cases_filters_to_supported_non_tool_buckets(self) -> None:
        dataset = _dataset(
            _case(case_id="single", bucket="single_hop"),
            _case(case_id="multi", bucket="multi_hop"),
            _case(case_id="metadata", bucket="metadata_filter"),
            _case(case_id="tool-eligible", bucket="single_hop", allow_tool=True),
            _case(case_id="tool-bucket", bucket="tool_allowed", allow_tool=True),
            _case(case_id="abstain", bucket="abstain_or_no_hit"),
        )

        selected_cases, excluded_cases = select_task_058_v1_cases(dataset)

        self.assertEqual([case.case_id for case in selected_cases], ["single", "multi", "metadata"])
        self.assertEqual(
            excluded_cases,
            [
                {
                    "case_id": "tool-eligible",
                    "bucket": "single_hop",
                    "exclusion_reason": "allow_tool=true",
                },
                {
                    "case_id": "tool-bucket",
                    "bucket": "tool_allowed",
                    "exclusion_reason": "allow_tool=true",
                },
                {
                    "case_id": "abstain",
                    "bucket": "abstain_or_no_hit",
                    "exclusion_reason": "bucket_not_in_task_058_v1",
                },
            ],
        )

    def test_build_default_output_path_uses_results_dir_and_timestamped_filename(self) -> None:
        results_dir = ROOT_DIR / "eval" / "results"

        with patch("app.benchmark.ask_retrieval_benchmark.datetime") as mocked_datetime:
            mocked_datetime.now.return_value = datetime(2026, 4, 20, 15, 30, 45)

            output_path = build_default_output_path(results_dir)

        self.assertEqual(output_path, results_dir / "retrieval-benchmark-20260420-153045.json")

    def test_write_retrieval_benchmark_result_writes_json_payload(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "result.json"
            result = {"schema_version": 1, "benchmark_kind": "ask_retrieval"}

            written_path = write_retrieval_benchmark_result(result, output_path)

            self.assertEqual(written_path, output_path)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                '{\n  "schema_version": 1,\n  "benchmark_kind": "ask_retrieval"\n}\n',
            )

    def test_run_ask_retrieval_benchmark_builds_successful_result_and_writes_artifact(self) -> None:
        dataset = _dataset(
            _case(case_id="case-1", locator=_locator(excerpt_anchor="alpha evidence")),
            _case(case_id="case-2", bucket="metadata_filter", locator=_locator(excerpt_anchor="beta evidence")),
            _case(case_id="excluded-tool", allow_tool=True),
        )
        settings = get_settings()

        fts_case_1 = [_candidate(chunk_id="fts-1", text="prefix alpha evidence suffix")]
        fts_case_2 = [_candidate(chunk_id="fts-2", text="no match")]
        vector_case_1 = [_candidate(chunk_id="vector-1", text="no vector match", retrieval_source="sqlite_vector")]
        vector_case_2 = [_candidate(
            chunk_id="vector-2",
            text="prefix beta evidence suffix",
            retrieval_source="sqlite_vector",
        )]
        hybrid_case_1 = [_candidate(chunk_id="hybrid-1", text="alpha evidence", retrieval_source="hybrid_rrf")]
        hybrid_case_2 = [_candidate(chunk_id="hybrid-2", text="beta evidence", retrieval_source="hybrid_rrf")]

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "retrieval.json"
            connection = Mock()

            with patch(
                "app.benchmark.ask_retrieval_benchmark.load_ask_benchmark_dataset",
                return_value=dataset,
            ) as mocked_load_dataset:
                with patch(
                    "app.benchmark.ask_retrieval_benchmark.initialize_index_db",
                    return_value=Path(tmp_dir) / "initialized.sqlite3",
                ) as mocked_initialize_db:
                    with patch(
                        "app.benchmark.ask_retrieval_benchmark.connect_sqlite",
                        return_value=connection,
                    ) as mocked_connect_sqlite:
                        with patch(
                            "app.benchmark.ask_retrieval_benchmark.run_retrieval_mode",
                            side_effect=[
                                fts_case_1,
                                fts_case_2,
                                vector_case_1,
                                vector_case_2,
                                hybrid_case_1,
                                hybrid_case_2,
                            ],
                        ) as mocked_run_mode:
                            with patch(
                                "app.benchmark.ask_retrieval_benchmark.write_retrieval_benchmark_result",
                                wraps=write_retrieval_benchmark_result,
                            ) as mocked_write_result:
                                result = run_ask_retrieval_benchmark(
                                    settings=settings,
                                    dataset_path=Path(tmp_dir) / "dataset.json",
                                    output_path=output_path,
                                )

            self.assertEqual(result["schema_version"], TASK_058_V1_SCHEMA_VERSION)
            self.assertEqual(result["benchmark_kind"], TASK_058_V1_BENCHMARK_KIND)
            self.assertEqual(result["run_status"], "passed")
            self.assertEqual(result["dataset_schema_version"], 1)
            self.assertEqual(result["selected_case_count"], 2)
            self.assertEqual(result["selected_case_ids"], ["case-1", "case-2"])
            self.assertEqual(
                result["excluded_cases"],
                [
                    {
                        "case_id": "excluded-tool",
                        "bucket": "single_hop",
                        "exclusion_reason": "allow_tool=true",
                    }
                ],
            )
            self.assertEqual(set(result["modes"]), {"fts_only", "vector_only", "hybrid_rrf"})
            self.assertEqual(result["modes"]["fts_only"]["status"], "passed")
            self.assertEqual(result["modes"]["fts_only"]["selected_case_count"], 2)
            self.assertEqual(
                result["modes"]["fts_only"]["summary_metrics"],
                {"Recall@5": 0.5, "Recall@10": 0.5, "NDCG@10": 0.5},
            )
            self.assertEqual(
                set(result["modes"]["fts_only"]["summary_metrics"]),
                {"Recall@5", "Recall@10", "NDCG@10"},
            )
            self.assertEqual(
                result["modes"]["vector_only"]["summary_metrics"],
                {"Recall@5": 0.5, "Recall@10": 0.5, "NDCG@10": 0.5},
            )
            self.assertEqual(
                result["modes"]["hybrid_rrf"]["summary_metrics"],
                {"Recall@5": 1.0, "Recall@10": 1.0, "NDCG@10": 1.0},
            )
            self.assertEqual(len(result["cases"]), 2)
            self.assertEqual(
                result["cases"][0]["expected_locators"],
                [_locator(excerpt_anchor="alpha evidence").to_dict()],
            )
            self.assertNotIn("expected_relevant_locators", result["cases"][0])
            self.assertEqual(
                [mode_result["mode"] for mode_result in result["cases"][0]["mode_results"]],
                ["fts_only", "vector_only", "hybrid_rrf"],
            )
            self.assertEqual(result["cases"][0]["mode_results"][0]["top_k"], 10)
            self.assertEqual(result["cases"][0]["mode_results"][0]["matched_locator_ranks"], [1])
            self.assertEqual(result["cases"][0]["mode_results"][1]["matched_locator_ranks"], [])
            self.assertEqual(result["cases"][0]["mode_results"][2]["retrieved_candidates"][0]["retrieval_source"], "hybrid_rrf")
            self.assertTrue(output_path.exists())
            self.assertEqual(mocked_load_dataset.call_args, call(Path(tmp_dir) / "dataset.json"))
            mocked_initialize_db.assert_called_once_with(settings.index_db_path, settings=settings)
            mocked_connect_sqlite.assert_called_once_with(Path(tmp_dir) / "initialized.sqlite3")
            self.assertEqual(
                mocked_run_mode.call_args_list,
                [
                    call(connection=connection, query="query for case-1", settings=settings, mode=RetrievalBenchmarkMode.FTS_ONLY),
                    call(connection=connection, query="query for case-2", settings=settings, mode=RetrievalBenchmarkMode.FTS_ONLY),
                    call(connection=connection, query="query for case-1", settings=settings, mode=RetrievalBenchmarkMode.VECTOR_ONLY),
                    call(connection=connection, query="query for case-2", settings=settings, mode=RetrievalBenchmarkMode.VECTOR_ONLY),
                    call(connection=connection, query="query for case-1", settings=settings, mode=RetrievalBenchmarkMode.HYBRID_RRF),
                    call(connection=connection, query="query for case-2", settings=settings, mode=RetrievalBenchmarkMode.HYBRID_RRF),
                ],
            )
            mocked_write_result.assert_called_once_with(result, output_path)
            connection.close.assert_called_once_with()

    def test_run_ask_retrieval_benchmark_fails_closed_on_mid_mode_error_and_closes_connection(self) -> None:
        dataset = _dataset(
            _case(case_id="case-1"),
            _case(case_id="case-2", bucket="multi_hop", locator=_locator(excerpt_anchor="beta evidence")),
        )
        settings = get_settings()
        connection = Mock()

        with TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "retrieval.json"

            with patch(
                "app.benchmark.ask_retrieval_benchmark.load_ask_benchmark_dataset",
                return_value=dataset,
            ):
                with patch(
                    "app.benchmark.ask_retrieval_benchmark.initialize_index_db",
                    return_value=Path(tmp_dir) / "initialized.sqlite3",
                ):
                    with patch(
                        "app.benchmark.ask_retrieval_benchmark.connect_sqlite",
                        return_value=connection,
                    ):
                        with patch(
                            "app.benchmark.ask_retrieval_benchmark.run_retrieval_mode",
                            side_effect=[
                                [_candidate(chunk_id="fts-1", text="alpha evidence")],
                                [_candidate(chunk_id="fts-2", text="beta evidence")],
                                [_candidate(chunk_id="vector-1", text="alpha evidence", retrieval_source="sqlite_vector")],
                                RetrievalBenchmarkModeError("Retrieval mode vector_only is disabled: vector_index_not_ready"),
                            ],
                        ) as mocked_run_mode:
                            result = run_ask_retrieval_benchmark(
                                settings=settings,
                                output_path=output_path,
                            )

        self.assertEqual(result["run_status"], "failed")
        self.assertNotIn("summary_metrics", result["modes"]["fts_only"])
        self.assertEqual(result["modes"]["fts_only"]["status"], "completed_before_failure")
        self.assertEqual(result["modes"]["vector_only"]["status"], "failed")
        self.assertEqual(
            result["modes"]["vector_only"]["failure_reason"],
            "Retrieval mode vector_only is disabled: vector_index_not_ready",
        )
        self.assertEqual(result["modes"]["hybrid_rrf"]["status"], "not_run")
        self.assertIn("stopped after mode failure", result["modes"]["hybrid_rrf"]["failure_reason"])
        self.assertEqual(len(result["cases"][0]["mode_results"]), 1)
        self.assertEqual(result["cases"][0]["mode_results"][0]["mode"], "fts_only")
        self.assertEqual(len(result["cases"][1]["mode_results"]), 1)
        self.assertEqual(result["cases"][1]["mode_results"][0]["mode"], "fts_only")
        self.assertEqual(
            mocked_run_mode.call_args_list,
            [
                call(connection=connection, query="query for case-1", settings=settings, mode=RetrievalBenchmarkMode.FTS_ONLY),
                call(connection=connection, query="query for case-2", settings=settings, mode=RetrievalBenchmarkMode.FTS_ONLY),
                call(connection=connection, query="query for case-1", settings=settings, mode=RetrievalBenchmarkMode.VECTOR_ONLY),
                call(connection=connection, query="query for case-2", settings=settings, mode=RetrievalBenchmarkMode.VECTOR_ONLY),
            ],
        )
        connection.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
