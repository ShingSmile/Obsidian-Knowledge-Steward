from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.config import get_settings
from app.contracts.workflow import (
    PatchOp,
    Proposal,
    RiskLevel,
    SafetyChecks,
    WorkflowAction,
)
from app.indexing.store import connect_sqlite, initialize_index_db, save_proposal
from app.services.proposal_validation import (
    ProposalValidationError,
    validate_proposal_for_persistence,
)


class ProposalValidationTests(unittest.TestCase):
    def test_validate_proposal_for_persistence_rejects_target_note_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            settings = replace(get_settings(), sample_vault_dir=vault_path)
            proposal = self._build_proposal(
                target_note_path=temp_root / "outside" / "note.md",
            )

            with self.assertRaises(ProposalValidationError):
                validate_proposal_for_persistence(
                    proposal,
                    settings=settings,
                )

    def test_validate_proposal_for_persistence_rejects_oversized_text_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            settings = replace(get_settings(), sample_vault_dir=vault_path)
            proposal = self._build_proposal(
                target_note_path=vault_path / "Digest" / "2026-03-14.md",
                content="x" * 2001,
            )

            with self.assertRaises(ProposalValidationError):
                validate_proposal_for_persistence(
                    proposal,
                    settings=settings,
                )

    def test_save_proposal_rejects_patch_target_outside_vault_before_insert(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)
            proposal = self._build_proposal(
                target_note_path=vault_path / "Digest" / "2026-03-14.md",
                patch_target_path=temp_root / "outside" / "note.md",
            )
            settings = replace(get_settings(), sample_vault_dir=vault_path)

            connection = connect_sqlite(db_path)
            try:
                with patch("app.indexing.store.get_settings", return_value=settings):
                    with self.assertRaises(ProposalValidationError):
                        save_proposal(
                            connection,
                            thread_id="thread_validation",
                            proposal=proposal,
                            approval_required=True,
                        )

                row = connection.execute(
                    "SELECT COUNT(*) FROM proposal WHERE proposal_id = ?;",
                    (proposal.proposal_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], 0)

    def test_save_proposal_uses_explicit_settings_for_vault_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)
            proposal = self._build_proposal(
                target_note_path=vault_path / "Digest" / "2026-03-14.md",
            )
            settings = replace(get_settings(), sample_vault_dir=vault_path)

            connection = connect_sqlite(db_path)
            try:
                save_proposal(
                    connection,
                    thread_id="thread_validation_settings",
                    proposal=proposal,
                    approval_required=True,
                    settings=settings,
                )
                row = connection.execute(
                    "SELECT COUNT(*) FROM proposal WHERE proposal_id = ?;",
                    (proposal.proposal_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row[0], 1)

    def _build_proposal(
        self,
        *,
        target_note_path: Path,
        patch_target_path: Path | None = None,
        content: str = "- Review retrieval fallback cases",
    ) -> Proposal:
        patch_target_path = patch_target_path or target_note_path
        return Proposal(
            proposal_id="prop_static_validation",
            action_type=WorkflowAction.DAILY_DIGEST,
            target_note_path=str(target_note_path.resolve()),
            summary="Insert the generated digest into the daily review note.",
            risk_level=RiskLevel.MEDIUM,
            patch_ops=[
                PatchOp(
                    op="merge_frontmatter",
                    target_path=str(patch_target_path.resolve()),
                    payload={"reviewed": False},
                ),
                PatchOp(
                    op="insert_under_heading",
                    target_path=str(patch_target_path.resolve()),
                    payload={
                        "heading_path": "## Digest",
                        "content": content,
                    },
                ),
            ],
            safety_checks=SafetyChecks(
                before_hash="sha256:before",
                max_changed_lines=12,
                contains_delete=False,
            ),
        )
