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
    write_ask_benchmark_backlog,
    write_ask_benchmark_dataset,
)
from app.benchmark.ask_dataset_validation import (
    validate_ask_benchmark_case,
    validate_ask_benchmark_dataset,
)
from app.benchmark.ask_dataset_review import validate_ask_benchmark_review_backlog
from app.benchmark.ask_dataset_candidates import _candidate_fingerprint


class AskBenchmarkValidationTests(unittest.TestCase):
    def _write_note(self, vault_root: Path) -> Path:
        note_path = vault_root / "Summary.md"
        note_path.write_text(
            "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
            encoding="utf-8",
        )
        return note_path

    def _write_repeated_heading_note(self, vault_root: Path) -> Path:
        note_path = vault_root / "Repeated.md"
        note_path.write_text(
            "# Summary\n\n## Highlights\n\nFirst section.\n\n## Highlights\n\nSecond section.\n",
            encoding="utf-8",
        )
        return note_path

    def _make_locator(
        self,
        *,
        note_path: str = "Summary.md",
        heading_path: str = "Summary > Highlights",
        excerpt_anchor: str = "Ship the benchmark.",
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
        bucket: str = "single_hop",
        source_origin: str = "sample_vault",
        case_id: str = "ask_case_validation",
        locator: AskBenchmarkLocator | None = None,
        expected_relevant_paths: list[str] | None = None,
        expected_facts: list[str] | None = None,
    ) -> AskBenchmarkCase:
        return AskBenchmarkCase.model_construct(
            case_id=case_id,
            bucket=bucket,
            user_query="Summarize the note.",
            source_origin=source_origin,
            expected_relevant_paths=expected_relevant_paths or ["Summary.md"],
            expected_relevant_locators=[locator or self._make_locator()],
            expected_facts=expected_facts or ["Ship the benchmark."],
            forbidden_claims=[],
            allow_tool=False,
            expected_tool_names=[],
            allow_retrieval_only=False,
            should_generate_answer=True,
            review_status="approved",
            review_notes="seed",
        )

    def _make_backlog_item(
        self,
        *,
        case_id: str = "ask_case_backlog_validation",
        note_path: str = "Summary.md",
        heading_path: str = "Summary > Highlights",
        user_query: str = "Summarize the note.",
        expected_relevant_paths: list[str] | None = None,
        expected_facts: list[str] | None = None,
        fingerprint: str | None = None,
    ) -> AskBenchmarkBacklogItem:
        if fingerprint is None:
            fingerprint = _candidate_fingerprint(
                note_path=note_path,
                heading_path=heading_path,
                user_query=user_query,
            )
        return AskBenchmarkBacklogItem.model_construct(
            case_id=case_id,
            fingerprint=fingerprint,
            bucket="single_hop",
            user_query=user_query,
            source_origin="sample_vault",
            expected_relevant_paths=expected_relevant_paths or ["Summary.md"],
            expected_relevant_locators=[
                self._make_locator(
                    note_path=note_path,
                    heading_path=heading_path,
                )
            ],
            expected_facts=expected_facts or ["Ship the benchmark."],
            forbidden_claims=[],
            allow_tool=False,
            expected_tool_names=[],
            allow_retrieval_only=False,
            should_generate_answer=True,
            review_status="revise",
            review_notes="seed",
        )

    def _make_dataset(self, cases: list[AskBenchmarkCase]) -> AskBenchmarkDataset:
        return AskBenchmarkDataset.model_construct(schema_version=1, cases=cases)

    def test_validate_locator_resolves_note_and_heading_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(
                    line_range={"start_line": 3, "end_line": 4},
                )
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertEqual(result.errors, [])

    def test_validate_locator_rejects_excerpt_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(
                    line_range={"start_line": 3, "end_line": 4},
                    excerpt_anchor="Old content no longer present",
                )
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertIn("excerpt_anchor", result.errors[0])

    def test_validate_locator_rejects_missing_note_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(note_path=""),
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertIn("note_path", result.errors[0])

    def test_validate_locator_rejects_nonexistent_note_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(note_path="Missing.md"),
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertTrue(
                any("does not exist" in error or "not listed" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_locator_rejects_missing_heading_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(heading_path=""),
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertIn("heading_path", result.errors[0])

    def test_validate_locator_rejects_unresolved_heading_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(heading_path="Summary > Missing"),
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertIn("heading_path", result.errors[0])

    def test_validate_case_rejects_empty_grounding_collections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = AskBenchmarkCase.model_construct(
                case_id="ask_case_empty_grounding",
                bucket="single_hop",
                user_query="Summarize the note.",
                source_origin="sample_vault",
                expected_relevant_paths=[],
                expected_relevant_locators=[],
                expected_facts=[],
                forbidden_claims=[],
                allow_tool=False,
                expected_tool_names=[],
                allow_retrieval_only=False,
                should_generate_answer=True,
                review_status="approved",
                review_notes="seed",
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertTrue(
                any("expected_relevant_paths" in error for error in result.errors),
                msg=result.errors,
            )
            self.assertTrue(
                any("expected_relevant_locators" in error for error in result.errors),
                msg=result.errors,
            )
            self.assertTrue(
                any("expected_facts" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_case_rejects_locator_path_not_in_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            (vault_root / "Other.md").write_text(
                "# Other\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            case = AskBenchmarkCase.model_construct(
                case_id="ask_case_path_mismatch",
                bucket="single_hop",
                user_query="Summarize the note.",
                source_origin="sample_vault",
                expected_relevant_paths=["Summary.md"],
                expected_relevant_locators=[
                    AskBenchmarkLocator.model_construct(
                        note_path="Other.md",
                        heading_path="Other > Highlights",
                        excerpt_anchor="Ship the benchmark.",
                    )
                ],
                expected_facts=["Ship the benchmark."],
                forbidden_claims=[],
                allow_tool=False,
                expected_tool_names=[],
                allow_retrieval_only=False,
                should_generate_answer=True,
                review_status="approved",
                review_notes="seed",
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertTrue(
                any("expected_relevant_paths" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_backlog_rejects_empty_grounding_collections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            backlog = AskBenchmarkReviewBacklog.model_construct(
                schema_version=1,
                items=[
                    AskBenchmarkBacklogItem.model_construct(
                        case_id="ask_case_backlog_empty",
                        fingerprint="shared-fp",
                        bucket="single_hop",
                        user_query="Summarize the note.",
                        source_origin="sample_vault",
                        expected_relevant_paths=[],
                        expected_relevant_locators=[],
                        expected_facts=[],
                        forbidden_claims=[],
                        allow_tool=False,
                        expected_tool_names=[],
                        allow_retrieval_only=False,
                        should_generate_answer=True,
                        review_status="revise",
                        review_notes="seed",
                    )
                ],
            )

            result = validate_ask_benchmark_review_backlog(backlog, vault_root)

            self.assertTrue(result.errors)
            self.assertTrue(
                any("expected_relevant_paths" in error for error in result.errors),
                msg=result.errors,
            )
            self.assertTrue(
                any("expected_relevant_locators" in error for error in result.errors),
                msg=result.errors,
            )
            self.assertTrue(
                any("expected_facts" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_backlog_rejects_locator_path_not_in_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            (vault_root / "Other.md").write_text(
                "# Other\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            backlog = AskBenchmarkReviewBacklog.model_construct(
                schema_version=1,
                items=[
                    self._make_backlog_item(
                        case_id="ask_case_backlog_path_mismatch",
                        note_path="Other.md",
                        heading_path="Other > Highlights",
                        expected_relevant_paths=["Summary.md"],
                    )
                ],
            )

            result = validate_ask_benchmark_review_backlog(backlog, vault_root)

            self.assertTrue(result.errors)
            self.assertTrue(
                any("expected_relevant_paths" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_locator_warns_on_drifted_line_range_when_excerpt_matches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(
                    line_range={"start_line": 1, "end_line": 2},
                )
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertEqual(result.errors, [])
            self.assertTrue(any("line_range" in warning for warning in result.warnings), msg=result.warnings)

    def test_validate_locator_errors_when_drifted_line_range_and_excerpt_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(
                    line_range={"start_line": 1, "end_line": 2},
                    excerpt_anchor="Old content no longer present",
                )
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertTrue(any("line_range" in error for error in result.errors), msg=result.errors)
            self.assertTrue(any("excerpt_anchor" in error for error in result.errors), msg=result.errors)
            self.assertTrue(any("line_range" in warning for warning in result.warnings), msg=result.warnings)

    def test_validate_locator_rejects_blank_excerpt_anchor_even_when_bypassed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=AskBenchmarkLocator.model_construct(
                    note_path="Summary.md",
                    heading_path="Summary > Highlights",
                    excerpt_anchor="",
                )
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertIn("excerpt_anchor", result.errors[0])

    def test_validate_locator_uses_line_range_to_disambiguate_repeated_heading_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_repeated_heading_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(
                    note_path="Repeated.md",
                    heading_path="Summary > Highlights",
                    excerpt_anchor="Second section.",
                    line_range={"start_line": 7, "end_line": 8},
                ),
                expected_relevant_paths=["Repeated.md"],
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertEqual(result.errors, [])
            self.assertEqual(result.warnings, [])

    def test_validate_in_progress_dataset_allows_smaller_case_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            cases: list[AskBenchmarkCase] = []
            bucket_plan = (
                ("single_hop", 20),
                ("multi_hop", 10),
                ("metadata_filter", 8),
                ("abstain_or_no_hit", 6),
                ("tool_allowed", 5),
            )
            case_index = 0
            for bucket, count in bucket_plan:
                for _ in range(count):
                    source_origin = "sample_vault" if case_index < 39 else "fixture"
                    cases.append(
                        self._make_case(
                            bucket=bucket,
                            source_origin=source_origin,
                            case_id=f"ask_case_{case_index:02d}",
                        )
                    )
                    case_index += 1

            result = validate_ask_benchmark_dataset(
                dataset=self._make_dataset(cases),
                vault_root=vault_root,
            )

            self.assertEqual(result.errors, [])

    def test_validate_in_progress_dataset_rejects_final_bucket_cap_overflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            cases = [
                self._make_case(
                    bucket="single_hop",
                    case_id=f"ask_case_cap_overflow_{index:02d}",
                )
                for index in range(21)
            ]

            result = validate_ask_benchmark_dataset(
                dataset=self._make_dataset(cases),
                vault_root=vault_root,
            )

            self.assertTrue(result.errors)
            self.assertIn("cap", result.errors[0])

    def test_validate_in_progress_dataset_rejects_more_than_ten_fixture_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            cases = [
                self._make_case(
                    bucket="single_hop",
                    source_origin="fixture",
                    case_id=f"ask_fixture_case_{index:02d}",
                )
                for index in range(11)
            ]

            result = validate_ask_benchmark_dataset(
                dataset=self._make_dataset(cases),
                vault_root=vault_root,
            )

            self.assertTrue(result.errors)
            self.assertIn("fixture", result.errors[0])

    def test_validate_full_dataset_rejects_incorrect_bucket_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            cases: list[AskBenchmarkCase] = []
            bucket_plan = (
                ("single_hop", 19),
                ("multi_hop", 10),
                ("metadata_filter", 8),
                ("abstain_or_no_hit", 6),
                ("tool_allowed", 7),
            )
            case_index = 0
            for bucket, count in bucket_plan:
                for _ in range(count):
                    source_origin = "sample_vault" if case_index < 40 else "fixture"
                    cases.append(
                        self._make_case(
                            bucket=bucket,
                            source_origin=source_origin,
                            case_id=f"ask_case_bad_bucket_{case_index:02d}",
                        )
                    )
                    case_index += 1

            result = validate_ask_benchmark_dataset(
                dataset=self._make_dataset(cases),
                vault_root=vault_root,
            )

            self.assertTrue(result.errors)
            self.assertTrue(
                any("final dataset requires" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_full_dataset_rejects_sample_vault_shortfall(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            cases: list[AskBenchmarkCase] = []
            bucket_plan = (
                ("single_hop", 20),
                ("multi_hop", 10),
                ("metadata_filter", 8),
                ("abstain_or_no_hit", 6),
                ("tool_allowed", 6),
            )
            case_index = 0
            for bucket, count in bucket_plan:
                for _ in range(count):
                    source_origin = "sample_vault" if case_index < 39 else "fixture"
                    cases.append(
                        self._make_case(
                            bucket=bucket,
                            source_origin=source_origin,
                            case_id=f"ask_case_sample_shortfall_{case_index:02d}",
                        )
                    )
                    case_index += 1

            result = validate_ask_benchmark_dataset(
                dataset=self._make_dataset(cases),
                vault_root=vault_root,
            )

            self.assertTrue(result.errors)
            self.assertTrue(
                any("sample_vault cases" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_full_dataset_accepts_final_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            cases: list[AskBenchmarkCase] = []
            bucket_plan = (
                ("single_hop", 20),
                ("multi_hop", 10),
                ("metadata_filter", 8),
                ("abstain_or_no_hit", 6),
                ("tool_allowed", 6),
            )
            case_index = 0
            for bucket, count in bucket_plan:
                for _ in range(count):
                    source_origin = "sample_vault" if case_index < 40 else "fixture"
                    cases.append(
                        self._make_case(
                            bucket=bucket,
                            source_origin=source_origin,
                            case_id=f"ask_case_final_{case_index:02d}",
                        )
                    )
                    case_index += 1

            result = validate_ask_benchmark_dataset(
                dataset=self._make_dataset(cases),
                vault_root=vault_root,
            )

            self.assertEqual(result.errors, [])

    def test_locator_to_dict_omits_none_line_range(self) -> None:
        locator = self._make_locator()

        payload = locator.to_dict()

        self.assertNotIn("line_range", payload)

    def test_persisted_dataset_and_backlog_omit_legacy_locator_line_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            legacy_locator = self._make_locator()

            dataset = AskBenchmarkDataset.model_construct(
                schema_version=1,
                cases=[self._make_case(locator=legacy_locator, case_id="ask_case_dataset")],
            )
            backlog = AskBenchmarkReviewBacklog.model_construct(
                schema_version=1,
                items=[
                    AskBenchmarkBacklogItem.model_construct(
                        case_id="ask_case_backlog",
                        bucket="single_hop",
                        user_query="Summarize the note.",
                        source_origin="fixture",
                        expected_relevant_paths=["Summary.md"],
                        expected_relevant_locators=[legacy_locator],
                        expected_facts=["Ship the benchmark."],
                        forbidden_claims=[],
                        allow_tool=False,
                        expected_tool_names=[],
                        allow_retrieval_only=False,
                        should_generate_answer=True,
                        review_status="revise",
                        review_notes="seed",
                    )
                ],
            )

            write_ask_benchmark_dataset(dataset, dataset_path)
            write_ask_benchmark_backlog(backlog, backlog_path)

            dataset_payload = dataset_path.read_text(encoding="utf-8")
            backlog_payload = backlog_path.read_text(encoding="utf-8")

            self.assertNotIn('"line_range": null', dataset_payload)
            self.assertNotIn('"line_range": null', backlog_payload)
