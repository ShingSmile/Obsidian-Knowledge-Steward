from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from contextlib import redirect_stderr
from unittest.mock import patch

from app.benchmark.ask_dataset import (
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
from app.benchmark.ask_dataset_candidates import AskBenchmarkCandidate, _candidate_fingerprint
from app.benchmark.ask_dataset_review import ReviewDecision, apply_review_outcomes, main


class AskBenchmarkReviewTests(unittest.TestCase):
    def _make_candidate(
        self,
        *,
        case_id: str,
        fingerprint: str | None = None,
        bucket: str = "single_hop",
        note_path: str = "Summary.md",
        heading_path: str = "Summary > Highlights",
        excerpt_anchor: str = "Ship the benchmark.",
        user_query: str = "Summarize the note.",
    ) -> AskBenchmarkCandidate:
        if fingerprint is None:
            fingerprint = _candidate_fingerprint(
                note_path=note_path,
                heading_path=heading_path,
                user_query=user_query,
            )
        return AskBenchmarkCandidate.model_construct(
            case_id=case_id,
            fingerprint=fingerprint,
            bucket=bucket,
            user_query=user_query,
            source_origin="sample_vault",
            expected_relevant_paths=["Summary.md"],
            expected_relevant_locators=[
                AskBenchmarkLocator.model_construct(
                    note_path=note_path,
                    heading_path=heading_path,
                    excerpt_anchor=excerpt_anchor,
                )
            ],
            expected_facts=["Ship the benchmark."],
            forbidden_claims=[],
            allow_tool=False,
            expected_tool_names=[],
            allow_retrieval_only=False,
            should_generate_answer=True,
        )

    def _make_backlog_item(
        self,
        *,
        case_id: str,
        fingerprint: str,
        review_status: str = "revise",
        review_notes: str = "seed",
    ) -> AskBenchmarkBacklogItem:
        return AskBenchmarkBacklogItem.model_construct(
            case_id=case_id,
            fingerprint=fingerprint,
            bucket="single_hop",
            user_query="Summarize the note.",
            source_origin="sample_vault",
            expected_relevant_paths=["Summary.md"],
            expected_relevant_locators=[
                AskBenchmarkLocator.model_construct(
                    note_path="Summary.md",
                    heading_path="Summary > Highlights",
                    excerpt_anchor="Ship the benchmark.",
                )
            ],
            expected_facts=["Ship the benchmark."],
            forbidden_claims=[],
            allow_tool=False,
            expected_tool_names=[],
            allow_retrieval_only=False,
            should_generate_answer=True,
            review_status=review_status,
            review_notes=review_notes,
        )

    def _seed_dataset(
        self,
        path: Path,
        cases: list[AskBenchmarkCase] | None = None,
    ) -> None:
        write_ask_benchmark_dataset(
            AskBenchmarkDataset.model_construct(schema_version=1, cases=cases or []),
            path,
        )

    def _seed_backlog(
        self,
        path: Path,
        items: list[AskBenchmarkBacklogItem],
    ) -> None:
        write_ask_benchmark_backlog(
            AskBenchmarkReviewBacklog.model_construct(schema_version=1, items=items),
            path,
        )

    def _make_case(
        self,
        *,
        case_id: str,
        note_path: str = "Summary.md",
        heading_path: str = "Summary > Highlights",
        user_query: str = "Summarize the note.",
        review_notes: str = "seed",
    ) -> AskBenchmarkCase:
        return AskBenchmarkCase.model_construct(
            case_id=case_id,
            bucket="single_hop",
            user_query=user_query,
            source_origin="sample_vault",
            expected_relevant_paths=["Summary.md"],
            expected_relevant_locators=[
                AskBenchmarkLocator.model_construct(
                    note_path=note_path,
                    heading_path=heading_path,
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
            review_notes=review_notes,
        )

    def test_apply_review_outcomes_routes_approved_and_backlog_separately(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            candidate_batch = [
                self._make_candidate(case_id="ask_case_010"),
                self._make_candidate(
                    case_id="ask_case_011",
                    user_query="Summarize the other note.",
                ),
            ]
            review_input = [
                {"case_id": "ask_case_010", "decision": "approve", "review_notes": "keep"},
                {"case_id": "ask_case_011", "decision": "revise", "review_notes": "bucket wrong"},
            ]

            result = apply_review_outcomes(
                candidate_batch=candidate_batch,
                review_decisions=[ReviewDecision.model_validate(item) for item in review_input],
                dataset_path=dataset_path,
                backlog_path=backlog_path,
                vault_root=vault_root,
            )

            dataset = load_ask_benchmark_dataset(dataset_path)
            backlog = load_ask_benchmark_backlog(backlog_path)

            self.assertEqual(result.approved_count, 1)
            self.assertEqual(result.backlog_count, 1)
            self.assertEqual([case.case_id for case in dataset.cases], ["ask_case_010"])
            self.assertEqual([item.case_id for item in backlog.items], ["ask_case_011"])
            self.assertEqual(dataset.cases[0].review_status, "approved")
            self.assertEqual(dataset.cases[0].review_notes, "keep")
            self.assertEqual(backlog.items[0].review_status, "revise")
            self.assertEqual(backlog.items[0].review_notes, "bucket wrong")
            self.assertEqual(
                backlog.items[0].fingerprint,
                _candidate_fingerprint(
                    note_path="Summary.md",
                    heading_path="Summary > Highlights",
                    user_query="Summarize the other note.",
                ),
            )

    def test_apply_review_outcomes_routes_reject_to_backlog_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            candidate_batch = [self._make_candidate(case_id="ask_case_012")]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_012", "decision": "reject", "review_notes": "out of scope"}
                )
            ]

            result = apply_review_outcomes(
                candidate_batch=candidate_batch,
                review_decisions=review_decisions,
                dataset_path=dataset_path,
                backlog_path=backlog_path,
                vault_root=vault_root,
            )

            dataset = load_ask_benchmark_dataset(dataset_path)
            backlog = load_ask_benchmark_backlog(backlog_path)

            self.assertEqual(result.approved_count, 0)
            self.assertEqual(result.backlog_count, 1)
            self.assertEqual(dataset.cases, [])
            self.assertEqual([item.case_id for item in backlog.items], ["ask_case_012"])
            self.assertEqual(backlog.items[0].review_status, "reject")
            self.assertEqual(backlog.items[0].review_notes, "out of scope")
            self.assertEqual(
                backlog.items[0].fingerprint,
                _candidate_fingerprint(
                    note_path="Summary.md",
                    heading_path="Summary > Highlights",
                    user_query="Summarize the note.",
                ),
            )

    def test_apply_review_outcomes_ignores_unreviewed_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            candidate_batch = [
                self._make_candidate(case_id="ask_case_100"),
                self._make_candidate(
                    case_id="ask_case_101",
                    user_query="Summarize the other note.",
                ),
                self._make_candidate(
                    case_id="ask_case_102",
                    user_query="Summarize a third note.",
                ),
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_100", "decision": "reject", "review_notes": "out of scope"}
                )
            ]

            result = apply_review_outcomes(
                candidate_batch=candidate_batch,
                review_decisions=review_decisions,
                dataset_path=dataset_path,
                backlog_path=backlog_path,
                vault_root=vault_root,
            )

            dataset = load_ask_benchmark_dataset(dataset_path)
            backlog = load_ask_benchmark_backlog(backlog_path)

            self.assertEqual(result.approved_count, 0)
            self.assertEqual(result.backlog_count, 1)
            self.assertEqual(dataset.cases, [])
            self.assertEqual([item.case_id for item in backlog.items], ["ask_case_100"])
            self.assertEqual(backlog.items[0].review_status, "reject")
            self.assertEqual(backlog.items[0].review_notes, "out of scope")

    def test_apply_review_outcomes_revalidates_approved_cases_before_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            candidate_batch = [
                self._make_candidate(
                    case_id="ask_case_020",
                    note_path="Missing.md",
                )
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_020", "decision": "approve", "review_notes": "keep"}
                )
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=candidate_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

            dataset = load_ask_benchmark_dataset(dataset_path)
            backlog = load_ask_benchmark_backlog(backlog_path)
            self.assertEqual(dataset.cases, [])
            self.assertEqual(backlog.items, [])

    def test_apply_review_outcomes_rejects_duplicate_case_ids_and_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            duplicate_case_batch = [
                self._make_candidate(case_id="ask_case_030"),
                self._make_candidate(case_id="ask_case_030"),
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_030", "decision": "approve", "review_notes": "keep"}
                )
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=duplicate_case_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

            duplicate_fingerprint_batch = [
                self._make_candidate(case_id="ask_case_031"),
                self._make_candidate(case_id="ask_case_032"),
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_031", "decision": "approve", "review_notes": "keep"}
                ),
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_032", "decision": "approve", "review_notes": "keep"}
                ),
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=duplicate_fingerprint_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

    def test_apply_review_outcomes_rejects_duplicate_stored_candidate_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            candidate_batch = [
                self._make_candidate(
                    case_id="ask_case_a",
                    fingerprint="shared-fp",
                    user_query="Summarize the note.",
                ),
                self._make_candidate(
                    case_id="ask_case_b",
                    fingerprint="shared-fp",
                    user_query="Summarize the other note.",
                ),
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_a", "decision": "reject", "review_notes": "keep"}
                ),
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_b", "decision": "reject", "review_notes": "keep"}
                ),
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=candidate_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

    def test_apply_review_outcomes_rejects_ambiguous_multi_locator_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            (vault_root / "Other.md").write_text(
                "# Other\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            candidate_batch = [
                AskBenchmarkCandidate.model_construct(
                    case_id="ask_case_multi",
                    fingerprint="shared-fp",
                    bucket="single_hop",
                    user_query="Summarize the note.",
                    source_origin="sample_vault",
                    expected_relevant_paths=["Summary.md", "Other.md"],
                    expected_relevant_locators=[
                        AskBenchmarkLocator.model_construct(
                            note_path="Summary.md",
                            heading_path="Summary > Highlights",
                            excerpt_anchor="Ship the benchmark.",
                        ),
                        AskBenchmarkLocator.model_construct(
                            note_path="Other.md",
                            heading_path="Other > Highlights",
                            excerpt_anchor="Ship the benchmark.",
                        ),
                    ],
                    expected_facts=["Ship the benchmark."],
                    forbidden_claims=[],
                    allow_tool=False,
                    expected_tool_names=[],
                    allow_retrieval_only=False,
                    should_generate_answer=True,
                )
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_multi", "decision": "reject", "review_notes": "ambiguous"}
                )
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=candidate_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

    def test_apply_review_outcomes_rejects_persisted_fingerprint_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            collision_fingerprint = _candidate_fingerprint(
                note_path="Summary.md",
                heading_path="Summary > Highlights",
                user_query="Summarize the note.",
            )
            self._seed_backlog(
                backlog_path,
                [
                    self._make_backlog_item(
                        case_id="ask_case_persisted",
                        fingerprint=collision_fingerprint,
                    )
                ],
            )

            candidate_batch = [
                self._make_candidate(case_id="ask_case_new"),
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_new", "decision": "approve", "review_notes": "keep"}
                )
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=candidate_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

    def test_validate_review_files_rejects_tampered_backlog_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(
                backlog_path,
                [
                    self._make_backlog_item(
                        case_id="ask_case_backlog_tampered",
                        fingerprint="tampered-fp",
                    )
                ],
            )

            from app.benchmark.ask_dataset_review import validate_ask_benchmark_review_files

            result = validate_ask_benchmark_review_files(
                dataset_path=dataset_path,
                backlog_path=backlog_path,
                vault_root=vault_root,
            )

            self.assertTrue(result.errors)
            self.assertTrue(any("fingerprint" in error for error in result.errors), msg=result.errors)

    def test_validate_review_files_rejects_backlog_overlap_with_approved_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path, [self._make_case(case_id="ask_case_existing")])
            self._seed_backlog(
                backlog_path,
                [
                    self._make_backlog_item(
                        case_id="ask_case_backlog_overlap",
                        fingerprint=_candidate_fingerprint(
                            note_path="Summary.md",
                            heading_path="Summary > Highlights",
                            user_query="Summarize the note.",
                        ),
                    )
                ],
            )

            from app.benchmark.ask_dataset_review import validate_ask_benchmark_review_files

            result = validate_ask_benchmark_review_files(
                dataset_path=dataset_path,
                backlog_path=backlog_path,
                vault_root=vault_root,
            )

            self.assertTrue(result.errors)
            self.assertTrue(
                any("overlap" in error or "fingerprint" in error for error in result.errors),
                msg=result.errors,
            )

    def test_validate_review_files_rejects_missing_dataset_and_backlog_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir)
            from app.benchmark.ask_dataset_review import validate_ask_benchmark_review_files

            result = validate_ask_benchmark_review_files(
                dataset_path=vault_root / "missing_cases.json",
                backlog_path=vault_root / "missing_backlog.json",
                vault_root=vault_root,
            )

            self.assertTrue(result.errors)
            self.assertTrue(any("dataset_path" in error for error in result.errors), msg=result.errors)
            self.assertTrue(any("backlog_path" in error for error in result.errors), msg=result.errors)

    def test_apply_review_outcomes_rolls_back_dataset_on_backlog_write_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])
            original_dataset_text = dataset_path.read_text(encoding="utf-8")
            original_backlog_text = backlog_path.read_text(encoding="utf-8")

            candidate_batch = [self._make_candidate(case_id="ask_case_rollback")]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_rollback", "decision": "reject", "review_notes": "keep"}
                )
            ]

            with patch("app.benchmark.ask_dataset_review.write_ask_benchmark_backlog", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    apply_review_outcomes(
                        candidate_batch=candidate_batch,
                        review_decisions=review_decisions,
                        dataset_path=dataset_path,
                        backlog_path=backlog_path,
                        vault_root=vault_root,
                    )

            self.assertEqual(dataset_path.read_text(encoding="utf-8"), original_dataset_text)
            self.assertEqual(backlog_path.read_text(encoding="utf-8"), original_backlog_text)

    def test_apply_review_outcomes_rejects_fingerprint_collision_with_approved_dataset_case(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path, [self._make_case(case_id="ask_case_existing")])
            self._seed_backlog(backlog_path, [])

            candidate_batch = [
                self._make_candidate(case_id="ask_case_new")
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_new", "decision": "approve", "review_notes": "keep"}
                )
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=candidate_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

    def test_apply_review_outcomes_rejects_case_id_collision_with_approved_dataset_case(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path, [self._make_case(case_id="ask_case_dup")])
            self._seed_backlog(backlog_path, [])

            candidate_batch = [
                self._make_candidate(
                    case_id="ask_case_dup",
                    note_path="Other.md",
                    heading_path="Other > Highlights",
                    excerpt_anchor="Different payload.",
                )
            ]
            review_decisions = [
                ReviewDecision.model_validate(
                    {"case_id": "ask_case_dup", "decision": "reject", "review_notes": "duplicate"}
                )
            ]

            with self.assertRaises(ValueError):
                apply_review_outcomes(
                    candidate_batch=candidate_batch,
                    review_decisions=review_decisions,
                    dataset_path=dataset_path,
                    backlog_path=backlog_path,
                    vault_root=vault_root,
                )

    def test_main_reports_clean_error_for_missing_batch_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])
            review_path = temp_root / "ask_review.json"
            review_path.write_text("[]\n", encoding="utf-8")

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "apply-review",
                        "--batch",
                        str(temp_root / "missing_batch.json"),
                        "--review",
                        str(review_path),
                        "--dataset",
                        str(dataset_path),
                        "--backlog",
                        str(backlog_path),
                        "--vault-root",
                        str(vault_root),
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("ERROR:", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_main_reports_clean_error_for_missing_generate_batch_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            output_path = temp_root / "ask_batch.json"
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(
                    [
                        "generate-batch",
                        "--count",
                        "1",
                        "--output",
                        str(output_path),
                        "--dataset",
                        str(temp_root / "missing_dataset.json"),
                        "--backlog",
                        str(temp_root / "missing_backlog.json"),
                        "--vault-root",
                        str(temp_root / "vault"),
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("ERROR:", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_main_reports_skipped_count_for_partial_apply_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            dataset_path = temp_root / "ask_benchmark_cases.json"
            backlog_path = temp_root / "ask_benchmark_review_backlog.json"
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            (vault_root / "Summary.md").write_text(
                "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
                encoding="utf-8",
            )
            self._seed_dataset(dataset_path)
            self._seed_backlog(backlog_path, [])

            batch_path = temp_root / "ask_batch.json"
            review_path = temp_root / "ask_review.json"
            batch = {
                "schema_version": 1,
                "candidates": [
                    self._make_candidate(case_id="ask_case_200").model_dump(mode="json"),
                    self._make_candidate(
                        case_id="ask_case_201",
                        user_query="Summarize the other note.",
                    ).model_dump(mode="json"),
                    self._make_candidate(
                        case_id="ask_case_202",
                        user_query="Summarize a third note.",
                    ).model_dump(mode="json"),
                ],
            }
            batch_path.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            review_path.write_text(
                json.dumps(
                    [
                        {"case_id": "ask_case_200", "decision": "reject", "review_notes": "out of scope"}
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "apply-review",
                        "--batch",
                        str(batch_path),
                        "--review",
                        str(review_path),
                        "--dataset",
                        str(dataset_path),
                        "--backlog",
                        str(backlog_path),
                        "--vault-root",
                        str(vault_root),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("1 routed to backlog", stdout.getvalue())
            self.assertIn("2 skipped from batch", stdout.getvalue())
