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
    load_ask_benchmark_backlog,
    load_ask_benchmark_dataset,
    write_ask_benchmark_backlog,
    write_ask_benchmark_dataset,
)
from app.benchmark.ask_dataset_candidates import AskBenchmarkCandidate, _candidate_fingerprint
from app.benchmark.ask_dataset_review import ReviewDecision, apply_review_outcomes


class AskBenchmarkReviewTests(unittest.TestCase):
    def _make_candidate(
        self,
        *,
        case_id: str,
        fingerprint: str,
        bucket: str = "single_hop",
        note_path: str = "Summary.md",
        heading_path: str = "Summary > Highlights",
        excerpt_anchor: str = "Ship the benchmark.",
        user_query: str = "Summarize the note.",
    ) -> AskBenchmarkCandidate:
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
                self._make_candidate(case_id="ask_case_010", fingerprint="fingerprint-010"),
                self._make_candidate(
                    case_id="ask_case_011",
                    fingerprint="fingerprint-011",
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
            self.assertEqual(backlog.items[0].fingerprint, "fingerprint-011")

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

            candidate_batch = [self._make_candidate(case_id="ask_case_012", fingerprint="fingerprint-012")]
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
            self.assertEqual(backlog.items[0].fingerprint, "fingerprint-012")

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
                self._make_candidate(case_id="ask_case_100", fingerprint="fingerprint-100"),
                self._make_candidate(
                    case_id="ask_case_101",
                    fingerprint="fingerprint-101",
                    user_query="Summarize the other note.",
                ),
                self._make_candidate(
                    case_id="ask_case_102",
                    fingerprint="fingerprint-102",
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
                    fingerprint="fingerprint-020",
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
                self._make_candidate(case_id="ask_case_030", fingerprint="fingerprint-030"),
                self._make_candidate(case_id="ask_case_030", fingerprint="fingerprint-031"),
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
                self._make_candidate(case_id="ask_case_031", fingerprint="fingerprint-032"),
                self._make_candidate(case_id="ask_case_032", fingerprint="fingerprint-032"),
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
                self._make_candidate(case_id="ask_case_new", fingerprint="fingerprint-shared"),
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
                self._make_candidate(case_id="ask_case_new", fingerprint="candidate-fingerprint")
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
                    fingerprint="different-fingerprint",
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
