from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Response

from app.config import get_settings
from app.contracts.workflow import (
    ApprovalDecision,
    PatchOp,
    Proposal,
    ProposalEvidence,
    RiskLevel,
    SafetyChecks,
    RunStatus,
    WorkflowAction,
    WorkflowRollbackRequest,
    WorkflowResumeRequest,
    WritebackResult,
)
from app.graphs.checkpoint import (
    WorkflowCheckpointStatus,
    load_graph_checkpoint,
    save_graph_checkpoint,
)
from app.indexing.ingest import ingest_vault
from app.indexing.store import connect_sqlite, initialize_index_db, load_proposal, save_proposal
from app.services.resume_workflow import ResumeWorkflowValidationError, resume_workflow
from app.main import (
    list_pending_approvals_endpoint,
    resume_workflow_endpoint,
    rollback_workflow_endpoint,
)


class ResumeWorkflowTests(unittest.TestCase):
    def test_resume_workflow_records_approval_and_completes_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                result = resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_a",
                            comment="Looks safe.",
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertTrue(result.approval_decision.approved)
            self.assertEqual(len(result.approval_decision.approved_patch_ops), 2)
            self.assertIsNotNone(result.audit_event_id)
            self.assertIn("Writeback execution is still out of scope", result.message)

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_resume_digest",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertEqual(checkpoint.checkpoint_status, WorkflowCheckpointStatus.COMPLETED)
            self.assertFalse(checkpoint.state["approval_required"])
            self.assertTrue(checkpoint.state["approval_decision"].approved)
            self.assertEqual(len(checkpoint.state["patch_plan"]), 2)
            self.assertEqual(checkpoint.state["audit_event_id"], result.audit_event_id)

            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            try:
                row = connection.execute(
                    """
                    SELECT approval_status, reviewer, approval_comment, proposal_id
                    FROM audit_log
                    WHERE audit_event_id = ?;
                    """,
                    (result.audit_event_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["approval_status"], "approved")
            self.assertEqual(row["reviewer"], "reviewer_a")
            self.assertEqual(row["proposal_id"], proposal.proposal_id)

    def test_resume_workflow_records_rejection_and_clears_patch_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                result = resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=False,
                            reviewer="reviewer_b",
                            comment="Risk is too high.",
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertFalse(result.approval_decision.approved)
            self.assertEqual(result.approval_decision.approved_patch_ops, [])
            self.assertEqual(
                result.message,
                "Workflow resume recorded rejection. No writeback was executed.",
            )

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_resume_digest",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertEqual(checkpoint.checkpoint_status, WorkflowCheckpointStatus.COMPLETED)
            self.assertEqual(checkpoint.state["patch_plan"], [])
            self.assertFalse(checkpoint.state["approval_decision"].approved)

    def test_resume_workflow_records_successful_writeback_result_and_refreshes_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            target_note_path = vault_path / "Digest" / "2026-03-14.md"
            target_note_path.parent.mkdir(parents=True)
            target_note_path.write_text(
                "# Digest\n\nlegacydigest token\n",
                encoding="utf-8",
            )
            db_path = temp_root / "knowledge_steward.sqlite3"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            proposal = self._seed_waiting_approval_fixture(
                db_path,
                target_note_path=target_note_path,
            )
            target_note_path.write_text(
                "# Digest\n\nrefresheddigest token\n",
                encoding="utf-8",
            )

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                ),
            ):
                result = resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_success",
                            comment="apply now",
                        ),
                        writeback_result=WritebackResult(
                            applied=True,
                            target_note_path=proposal.target_note_path,
                            before_hash=proposal.safety_checks.before_hash,
                            after_hash="sha256:after_success",
                            applied_patch_ops=proposal.patch_ops,
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(
                result.message,
                "Workflow resume recorded approval, persisted a successful writeback result, "
                "and refreshed the target note via scoped ingest.",
            )
            self.assertIsNotNone(result.writeback_result)
            assert result.writeback_result is not None
            self.assertTrue(result.writeback_result.applied)
            self.assertEqual(result.writeback_result.after_hash, "sha256:after_success")
            self.assertIsNotNone(result.post_writeback_sync)
            assert result.post_writeback_sync is not None
            self.assertTrue(result.post_writeback_sync.succeeded)
            self.assertIsNotNone(result.post_writeback_sync.ingest_result)
            assert result.post_writeback_sync.ingest_result is not None
            self.assertEqual(result.post_writeback_sync.ingest_result.scanned_notes, 1)
            self.assertEqual(result.post_writeback_sync.ingest_result.updated_notes, 1)

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_resume_digest",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertIsNotNone(checkpoint.state["writeback_result"])
            self.assertTrue(checkpoint.state["writeback_result"].applied)
            self.assertEqual(
                checkpoint.state["writeback_result"].after_hash,
                "sha256:after_success",
            )
            self.assertIsNotNone(checkpoint.state["post_writeback_sync"])
            self.assertTrue(checkpoint.state["post_writeback_sync"].succeeded)

            connection = sqlite3.connect(db_path)
            try:
                refreshed_texts = {
                    row[0]
                    for row in connection.execute(
                        """
                        SELECT chunk.text
                        FROM chunk
                        JOIN note ON note.note_id = chunk.note_id
                        WHERE note.path = ?;
                        """,
                        (str(target_note_path.resolve()),),
                    ).fetchall()
                }
                refreshed_hits = connection.execute(
                    "SELECT COUNT(*) FROM chunk_fts WHERE chunk_fts MATCH 'refresheddigest';"
                ).fetchone()[0]
                legacy_hits = connection.execute(
                    "SELECT COUNT(*) FROM chunk_fts WHERE chunk_fts MATCH 'legacydigest';"
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(refreshed_texts, {"# Digest\n\nrefresheddigest token"})
            self.assertGreater(refreshed_hits, 0)
            self.assertEqual(legacy_hits, 0)

            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            try:
                row = connection.execute(
                    """
                    SELECT before_hash, after_hash, writeback_applied, error
                    FROM audit_log
                    WHERE audit_event_id = ?;
                    """,
                    (result.audit_event_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["before_hash"], proposal.safety_checks.before_hash)
            self.assertEqual(row["after_hash"], "sha256:after_success")
            self.assertEqual(row["writeback_applied"], 1)
            self.assertIsNone(row["error"])

    def test_resume_workflow_reports_scoped_sync_failure_after_successful_writeback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            target_note_path = vault_path / "Digest" / "2026-03-14.md"
            target_note_path.parent.mkdir(parents=True)
            target_note_path.write_text(
                "# Digest\n\nlegacydigest token\n",
                encoding="utf-8",
            )
            db_path = temp_root / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(
                db_path,
                target_note_path=target_note_path,
            )
            target_note_path.write_text(
                "# Digest\n\nrefresheddigest token\n",
                encoding="utf-8",
            )

            with patch(
                "app.services.resume_workflow.ingest_vault",
                side_effect=RuntimeError("scoped ingest refresh exploded"),
            ), patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                ),
            ):
                result = resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_sync_failure",
                            comment="record local writeback first",
                        ),
                        writeback_result=WritebackResult(
                            applied=True,
                            target_note_path=proposal.target_note_path,
                            before_hash=proposal.safety_checks.before_hash,
                            after_hash="sha256:after_success",
                            applied_patch_ops=proposal.patch_ops,
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertIsNotNone(result.post_writeback_sync)
            assert result.post_writeback_sync is not None
            self.assertFalse(result.post_writeback_sync.succeeded)
            self.assertEqual(
                result.post_writeback_sync.error,
                "scoped ingest refresh exploded",
            )
            self.assertIn("scoped ingest refresh failed", result.message)
            self.assertIn("scoped ingest refresh exploded", result.message)

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_resume_digest",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertEqual(checkpoint.checkpoint_status, WorkflowCheckpointStatus.COMPLETED)
            self.assertIsNotNone(checkpoint.state["post_writeback_sync"])
            self.assertFalse(checkpoint.state["post_writeback_sync"].succeeded)
            self.assertEqual(
                checkpoint.state["post_writeback_sync"].error,
                "scoped ingest refresh exploded",
            )
            self.assertIsNotNone(result.audit_event_id)

    def test_resume_workflow_records_failed_writeback_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                result = resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_failed",
                            comment="record the failure",
                        ),
                        writeback_result=WritebackResult(
                            applied=False,
                            target_note_path=proposal.target_note_path,
                            before_hash="sha256:current_hash",
                            applied_patch_ops=[],
                            error="before_hash mismatch: current file changed",
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(
                result.message,
                "Workflow resume recorded approval, but the plugin reported a failed writeback result.",
            )
            self.assertIsNotNone(result.writeback_result)
            assert result.writeback_result is not None
            self.assertFalse(result.writeback_result.applied)
            self.assertEqual(
                result.writeback_result.error,
                "before_hash mismatch: current file changed",
            )

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_resume_digest",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertEqual(
                checkpoint.state["writeback_result"].error,
                "before_hash mismatch: current file changed",
            )

            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            try:
                row = connection.execute(
                    """
                    SELECT before_hash, after_hash, writeback_applied, error
                    FROM audit_log
                    WHERE audit_event_id = ?;
                    """,
                    (result.audit_event_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["before_hash"], "sha256:current_hash")
            self.assertIsNone(row["after_hash"])
            self.assertEqual(row["writeback_applied"], 0)
            self.assertEqual(row["error"], "before_hash mismatch: current file changed")

    def test_resume_workflow_rejects_mismatched_thread_and_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                with self.assertRaises(HTTPException) as raised:
                    resume_workflow_endpoint(
                        WorkflowResumeRequest(
                            thread_id="thread_other",
                            proposal_id=proposal.proposal_id,
                            approval_decision=ApprovalDecision(
                                approved=True,
                                reviewer="reviewer_c",
                            ),
                        ),
                        Response(),
                    )

            self.assertEqual(raised.exception.status_code, 404)

    def test_resume_workflow_rejects_partial_patch_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                with self.assertRaises(HTTPException) as raised:
                    resume_workflow_endpoint(
                        WorkflowResumeRequest(
                            thread_id="thread_resume_digest",
                            proposal_id=proposal.proposal_id,
                            approval_decision=ApprovalDecision(
                                approved=True,
                                reviewer="reviewer_d",
                                approved_patch_ops=[proposal.patch_ops[0]],
                            ),
                        ),
                        Response(),
                    )

            self.assertEqual(raised.exception.status_code, 400)
            self.assertIn("Partial patch approval is not supported yet", raised.exception.detail)

    def test_resume_workflow_rejects_writeback_result_on_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                with self.assertRaises(HTTPException) as raised:
                    resume_workflow_endpoint(
                        WorkflowResumeRequest(
                            thread_id="thread_resume_digest",
                            proposal_id=proposal.proposal_id,
                            approval_decision=ApprovalDecision(
                                approved=False,
                                reviewer="reviewer_reject_invalid",
                            ),
                            writeback_result=WritebackResult(
                                applied=False,
                                target_note_path=proposal.target_note_path,
                                before_hash="sha256:current_hash",
                                error="should not exist on rejection",
                            ),
                        ),
                        Response(),
                    )

            self.assertEqual(raised.exception.status_code, 400)
            self.assertIn("must not include writeback_result", raised.exception.detail)

    def test_resume_workflow_rejects_stored_proposal_that_fails_static_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            target_note_path = vault_path / "Digest" / "2026-03-14.md"
            db_path = temp_root / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(
                db_path,
                target_note_path=target_note_path,
            )

            connection = sqlite3.connect(db_path)
            try:
                connection.execute(
                    """
                    UPDATE patch_op
                    SET payload_json = ?
                    WHERE proposal_id = ? AND ordinal = 1;
                    """,
                    (
                        json.dumps(
                            {
                                "heading_path": "## Digest",
                                "content": "<script>alert(1)</script>",
                            }
                        ),
                        proposal.proposal_id,
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            )

            with self.assertRaises(ResumeWorkflowValidationError) as raised:
                resume_workflow(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_static_validation",
                        ),
                    ),
                    settings=settings,
                    run_id="run_static_validation",
                )

            self.assertIn("script", str(raised.exception).lower())

    def test_resume_workflow_is_idempotent_for_the_same_approval_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                first_result = resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_idempotent",
                            comment="approve once",
                        ),
                    ),
                    Response(),
                )
                second_result = resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_idempotent",
                            comment="approve once",
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(
                second_result.message,
                "Workflow resume was already resolved with the same approval decision.",
            )
            self.assertEqual(second_result.audit_event_id, first_result.audit_event_id)

            connection = sqlite3.connect(db_path)
            try:
                audit_count = connection.execute(
                    "SELECT COUNT(*) FROM audit_log WHERE proposal_id = ?;",
                    (proposal.proposal_id,),
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(audit_count, 1)

    def test_rollback_workflow_records_successful_rollback_and_updates_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            target_note_path = vault_path / "Digest" / "2026-03-14.md"
            target_note_path.parent.mkdir(parents=True)
            target_note_path.write_text(
                "# Digest\n\nlegacydigest token\n",
                encoding="utf-8",
            )
            db_path = temp_root / "knowledge_steward.sqlite3"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            proposal = self._seed_waiting_approval_fixture(
                db_path,
                target_note_path=target_note_path,
            )
            self._complete_successful_writeback(
                db_path=db_path,
                vault_path=vault_path,
                proposal=proposal,
            )

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                ),
            ):
                result = rollback_workflow_endpoint(
                    WorkflowRollbackRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        rollback_result=WritebackResult(
                            applied=True,
                            target_note_path=proposal.target_note_path,
                            before_hash="sha256:after_success",
                            after_hash=proposal.safety_checks.before_hash,
                            applied_patch_ops=[],
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertEqual(
                result.message,
                "Workflow rollback recorded a successful local rollback result.",
            )
            self.assertTrue(result.rollback_result.applied)
            self.assertEqual(
                result.rollback_result.after_hash,
                proposal.safety_checks.before_hash,
            )

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_resume_digest",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertIsNotNone(checkpoint.state["rollback_result"])
            self.assertTrue(checkpoint.state["rollback_result"].applied)
            self.assertEqual(
                checkpoint.state["rollback_result"].before_hash,
                "sha256:after_success",
            )
            self.assertEqual(
                checkpoint.state["rollback_result"].after_hash,
                proposal.safety_checks.before_hash,
            )
            self.assertEqual(
                checkpoint.state["rollback_audit_event_id"],
                result.audit_event_id,
            )

            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            try:
                row = connection.execute(
                    """
                    SELECT before_hash, after_hash, writeback_applied, error, model_info_json
                    FROM audit_log
                    WHERE audit_event_id = ?;
                    """,
                    (result.audit_event_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["before_hash"], "sha256:after_success")
            self.assertEqual(row["after_hash"], proposal.safety_checks.before_hash)
            self.assertEqual(row["writeback_applied"], 1)
            self.assertIsNone(row["error"])
            self.assertEqual(
                json.loads(row["model_info_json"])["event_kind"],
                "rollback",
            )

    def test_rollback_workflow_records_failed_rollback_without_locking_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            target_note_path = vault_path / "Digest" / "2026-03-14.md"
            target_note_path.parent.mkdir(parents=True)
            target_note_path.write_text(
                "# Digest\n\nlegacydigest token\n",
                encoding="utf-8",
            )
            db_path = temp_root / "knowledge_steward.sqlite3"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            proposal = self._seed_waiting_approval_fixture(
                db_path,
                target_note_path=target_note_path,
            )
            self._complete_successful_writeback(
                db_path=db_path,
                vault_path=vault_path,
                proposal=proposal,
            )

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                ),
            ):
                result = rollback_workflow_endpoint(
                    WorkflowRollbackRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        rollback_result=WritebackResult(
                            applied=False,
                            target_note_path=proposal.target_note_path,
                            before_hash="sha256:different_current",
                            applied_patch_ops=[],
                            error=(
                                "Rollback refused for /vault/Digest/2026-03-14.md. "
                                "expected current hash sha256:after_success, got sha256:different_current."
                            ),
                        ),
                    ),
                    Response(),
                )

            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertFalse(result.rollback_result.applied)
            self.assertEqual(
                result.message,
                "Workflow rollback recorded a failed local rollback result. No content was reverted.",
            )

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_resume_digest",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertNotIn("rollback_result", checkpoint.state)
            self.assertNotIn("rollback_audit_event_id", checkpoint.state)

            connection = sqlite3.connect(db_path)
            connection.row_factory = sqlite3.Row
            try:
                row = connection.execute(
                    """
                    SELECT before_hash, after_hash, writeback_applied, error, model_info_json
                    FROM audit_log
                    WHERE audit_event_id = ?;
                    """,
                    (result.audit_event_id,),
                ).fetchone()
            finally:
                connection.close()

            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["before_hash"], "sha256:different_current")
            self.assertIsNone(row["after_hash"])
            self.assertEqual(row["writeback_applied"], 0)
            self.assertIn("Rollback refused", row["error"])
            self.assertEqual(
                json.loads(row["model_info_json"])["event_kind"],
                "rollback",
            )

    def test_pending_approvals_endpoint_omits_resolved_proposal_after_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            proposal = self._seed_waiting_approval_fixture(db_path)

            with patch(
                "app.main.settings",
                replace(get_settings(), index_db_path=db_path),
            ):
                pending_before = list_pending_approvals_endpoint()
                self.assertEqual(len(pending_before.items), 1)
                self.assertEqual(pending_before.items[0].proposal_id, proposal.proposal_id)

                resume_workflow_endpoint(
                    WorkflowResumeRequest(
                        thread_id="thread_resume_digest",
                        proposal_id=proposal.proposal_id,
                        approval_decision=ApprovalDecision(
                            approved=True,
                            reviewer="reviewer_pending_list",
                        ),
                    ),
                    Response(),
                )
                pending_after = list_pending_approvals_endpoint()

            self.assertEqual(pending_after.items, [])

    def _seed_waiting_approval_fixture(
        self,
        db_path: Path,
        *,
        target_note_path: Path | None = None,
    ) -> Proposal:
        initialize_index_db(db_path)
        normalized_target_note_path = (
            target_note_path.resolve()
            if target_note_path is not None
            else get_settings().sample_vault_dir / "Digest" / "2026-03-14.md"
        )
        before_hash = (
            self._compute_file_hash(normalized_target_note_path)
            if normalized_target_note_path.exists()
            else "sha256:resume_before"
        )
        proposal = Proposal(
            proposal_id="prop_digest_resume",
            action_type=WorkflowAction.DAILY_DIGEST,
            target_note_path=str(normalized_target_note_path),
            summary="Insert the generated digest into the daily review note.",
            risk_level=RiskLevel.HIGH,
            evidence=[
                ProposalEvidence(
                    source_path="/vault/Daily/2026-03-14.md",
                    heading_path="Summary",
                    chunk_id="chunk_digest_source",
                    reason="The digest is grounded in the latest indexed note summary.",
                )
            ],
            patch_ops=[
                PatchOp(
                    op="frontmatter_merge",
                    target_path=str(normalized_target_note_path),
                    payload={"reviewed": False},
                ),
                PatchOp(
                    op="insert_under_heading",
                    target_path=str(normalized_target_note_path),
                    payload={
                        "heading_path": "## Digest",
                        "content": "- Review retrieval fallback cases",
                    },
                ),
            ],
            safety_checks=SafetyChecks(
                before_hash=before_hash,
                max_changed_lines=12,
                contains_delete=False,
            ),
        )
        proposal_settings = replace(
            get_settings(),
            sample_vault_dir=normalized_target_note_path.parent.parent,
        )

        connection = connect_sqlite(db_path)
        try:
            with patch("app.indexing.store.get_settings", return_value=proposal_settings):
                save_proposal(
                    connection,
                    thread_id="thread_resume_digest",
                    proposal=proposal,
                    approval_required=True,
                    run_id="run_waiting_digest",
                    idempotency_key="resume_digest_20260314",
                )
            persisted = load_proposal(connection, proposal_id=proposal.proposal_id)
            self.assertIsNotNone(persisted)
        finally:
            connection.close()

        save_graph_checkpoint(
            db_path,
            graph_name="digest_graph",
            checkpoint_status=WorkflowCheckpointStatus.WAITING_FOR_APPROVAL,
            last_completed_node="build_digest_proposal",
            next_node_name="human_approval",
            state={
                "thread_id": "thread_resume_digest",
                "run_id": "run_waiting_digest",
                "action_type": WorkflowAction.DAILY_DIGEST,
                "proposal": proposal,
                "approval_required": True,
                "approval_decision": None,
                "patch_plan": [
                    patch_op.model_dump(mode="json") for patch_op in proposal.patch_ops
                ],
                "before_hash": proposal.safety_checks.before_hash,
                "request_metadata": {"trigger": "test_fixture"},
                "errors": [],
                "trace_events": [],
                "transient_prompt_context": {},
            },
        )
        return proposal

    def _complete_successful_writeback(
        self,
        *,
        db_path: Path,
        vault_path: Path,
        proposal: Proposal,
    ) -> None:
        with patch(
            "app.main.settings",
            replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            ),
        ):
            resume_workflow_endpoint(
                WorkflowResumeRequest(
                    thread_id="thread_resume_digest",
                    proposal_id=proposal.proposal_id,
                    approval_decision=ApprovalDecision(
                        approved=True,
                        reviewer="reviewer_for_rollback",
                        comment="apply before rollback test",
                    ),
                    writeback_result=WritebackResult(
                        applied=True,
                        target_note_path=proposal.target_note_path,
                        before_hash=proposal.safety_checks.before_hash,
                        after_hash="sha256:after_success",
                        applied_patch_ops=proposal.patch_ops,
                    ),
                ),
                Response(),
            )

    def _compute_file_hash(self, target_note_path: Path) -> str:
        return "sha256:" + hashlib.sha256(target_note_path.read_bytes()).hexdigest()
