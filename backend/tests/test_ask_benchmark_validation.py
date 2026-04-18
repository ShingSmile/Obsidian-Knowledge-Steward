from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.benchmark.ask_dataset import (
    AskBenchmarkCase,
    AskBenchmarkDataset,
    AskBenchmarkLocator,
)
from app.benchmark.ask_dataset_validation import (
    validate_ask_benchmark_case,
    validate_ask_benchmark_dataset,
)


class AskBenchmarkValidationTests(unittest.TestCase):
    def _write_note(self, vault_root: Path) -> Path:
        note_path = vault_root / "Summary.md"
        note_path.write_text(
            "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
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
    ) -> AskBenchmarkCase:
        return AskBenchmarkCase.model_construct(
            case_id=case_id,
            bucket=bucket,
            user_query="Summarize the note.",
            source_origin=source_origin,
            expected_relevant_paths=["Summary.md"],
            expected_relevant_locators=[locator or self._make_locator()],
            expected_facts=["Ship the benchmark."],
            forbidden_claims=[],
            allow_tool=False,
            expected_tool_names=[],
            allow_retrieval_only=False,
            should_generate_answer=True,
            review_status="approved",
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
            self.assertIn("does not exist", result.errors[0])

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

    def test_validate_locator_rejects_line_range_outside_heading_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            self._write_note(vault_root)
            case = self._make_case(
                locator=self._make_locator(
                    line_range={"start_line": 1, "end_line": 2},
                )
            )

            result = validate_ask_benchmark_case(case=case, vault_root=vault_root)

            self.assertTrue(result.errors)
            self.assertIn("line_range", result.errors[0])

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
