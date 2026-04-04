from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app.config import get_settings
from app.contracts.workflow import (
    ApprovalDecision,
    AskResultMode,
    AskWorkflowResult,
    AuditEvent,
    PatchOp,
    Proposal,
    ProposalEvidence,
    RetrievalMetadataFilter,
    RiskLevel,
    SafetyChecks,
    WorkflowAction,
    WritebackResult,
)
from app.graphs.checkpoint import (
    WorkflowCheckpointStatus,
    hydrate_business_checkpoint_state,
    load_graph_checkpoint,
    save_graph_checkpoint,
)
from app.indexing.parser import parse_markdown_note
from app.indexing.store import (
    SCHEMA_VERSION,
    append_audit_log_event,
    build_chunk_records,
    build_note_record,
    connect_sqlite,
    initialize_index_db,
    list_pending_approval_records,
    load_proposal,
    save_proposal,
)


class IndexStoreTests(unittest.TestCase):
    def test_initialize_index_db_creates_expected_tables_and_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            connection = sqlite3.connect(db_path)
            try:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table';"
                    ).fetchall()
                }
                self.assertIn("note", tables)
                self.assertIn("chunk", tables)
                self.assertIn("chunk_fts", tables)
                self.assertIn("chunk_embedding", tables)
                self.assertIn("run_trace", tables)
                self.assertIn("workflow_checkpoint", tables)
                self.assertIn("proposal", tables)
                self.assertIn("proposal_evidence", tables)
                self.assertIn("patch_op", tables)
                self.assertIn("audit_log", tables)
                self.assertEqual(
                    connection.execute("PRAGMA user_version;").fetchone()[0],
                    SCHEMA_VERSION,
                )

                note_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(note);").fetchall()
                }
                self.assertTrue(
                    {
                        "path",
                        "content_hash",
                        "source_mtime_ns",
                        "tags_json",
                        "aliases_json",
                        "out_links_json",
                    }.issubset(note_columns)
                )

                chunk_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(chunk);").fetchall()
                }
                self.assertTrue(
                    {
                        "note_id",
                        "chunk_type",
                        "heading_path",
                        "start_line",
                        "end_line",
                        "content_hash",
                    }.issubset(chunk_columns)
                )

                chunk_indexes = {
                    row[1] for row in connection.execute("PRAGMA index_list(chunk);").fetchall()
                }
                self.assertIn("idx_chunk_heading_path", chunk_indexes)
                self.assertIn("idx_chunk_note_id_chunk_type", chunk_indexes)

                chunk_embedding_columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(chunk_embedding);").fetchall()
                }
                self.assertTrue(
                    {
                        "chunk_id",
                        "provider_key",
                        "provider_name",
                        "model_name",
                        "embedding_dim",
                        "vector_norm",
                        "embedding_json",
                    }.issubset(chunk_embedding_columns)
                )

                chunk_embedding_indexes = {
                    row[1]
                    for row in connection.execute("PRAGMA index_list(chunk_embedding);").fetchall()
                }
                self.assertIn("idx_chunk_embedding_provider_model", chunk_embedding_indexes)
                self.assertIn("idx_chunk_embedding_note_id", chunk_embedding_indexes)

                run_trace_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(run_trace);").fetchall()
                }
                self.assertTrue(
                    {
                        "trace_id",
                        "run_id",
                        "thread_id",
                        "graph_name",
                        "node_name",
                        "event_type",
                        "action_type",
                        "event_timestamp",
                        "details_json",
                    }.issubset(run_trace_columns)
                )

                run_trace_indexes = {
                    row[1] for row in connection.execute("PRAGMA index_list(run_trace);").fetchall()
                }
                self.assertIn("idx_run_trace_run_id", run_trace_indexes)
                self.assertIn("idx_run_trace_thread_id", run_trace_indexes)

                checkpoint_columns = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(workflow_checkpoint);"
                    ).fetchall()
                }
                self.assertTrue(
                    {
                        "checkpoint_id",
                        "thread_id",
                        "graph_name",
                        "action_type",
                        "last_run_id",
                        "checkpoint_status",
                        "state_json",
                    }.issubset(checkpoint_columns)
                )

                checkpoint_indexes = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA index_list(workflow_checkpoint);"
                    ).fetchall()
                }
                self.assertIn(
                    "idx_workflow_checkpoint_thread_graph",
                    checkpoint_indexes,
                )

                proposal_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(proposal);").fetchall()
                }
                self.assertTrue(
                    {
                        "thread_id",
                        "run_id",
                        "before_hash",
                        "idempotency_key",
                        "safety_checks_json",
                    }.issubset(proposal_columns)
                )

                proposal_indexes = {
                    row[1] for row in connection.execute("PRAGMA index_list(proposal);").fetchall()
                }
                self.assertIn("idx_proposal_thread_id", proposal_indexes)
                self.assertIn("idx_proposal_target_note_path", proposal_indexes)

                evidence_columns = {
                    row[1]
                    for row in connection.execute(
                        "PRAGMA table_info(proposal_evidence);"
                    ).fetchall()
                }
                self.assertTrue(
                    {
                        "proposal_id",
                        "ordinal",
                        "source_path",
                        "chunk_id",
                        "reason",
                    }.issubset(evidence_columns)
                )

                patch_op_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(patch_op);").fetchall()
                }
                self.assertTrue(
                    {
                        "proposal_id",
                        "ordinal",
                        "op",
                        "target_path",
                        "payload_json",
                    }.issubset(patch_op_columns)
                )

                audit_columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(audit_log);").fetchall()
                }
                self.assertTrue(
                    {
                        "proposal_id",
                        "approval_status",
                        "before_hash",
                        "after_hash",
                        "writeback_applied",
                        "approval_payload_json",
                        "writeback_result_json",
                    }.issubset(audit_columns)
                )

                audit_indexes = {
                    row[1] for row in connection.execute("PRAGMA index_list(audit_log);").fetchall()
                }
                self.assertIn("idx_audit_log_thread_id", audit_indexes)
                self.assertIn("idx_audit_log_proposal_id", audit_indexes)
            finally:
                connection.close()

    def test_build_records_from_parsed_note_preserves_schema_required_fields(self) -> None:
        markdown = """# Summary

- [ ] ship schema
link to [[Roadmap]]

## Detail

body text
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir) / "vault"
            vault_path.mkdir()
            note_path = vault_path / "2026-03-12 Summary.md"
            note_path.write_text(markdown, encoding="utf-8")

            parsed_note = parse_markdown_note(note_path)
            note_record = build_note_record(
                note_path,
                parsed_note,
                vault_root=vault_path,
            )
            chunk_records = build_chunk_records(note_record.note_id, parsed_note)

            self.assertEqual(note_record.path, "2026-03-12 Summary.md")
            self.assertEqual(note_record.task_count, parsed_note.task_count)
            self.assertEqual(note_record.out_links, tuple(parsed_note.wikilinks))
            self.assertTrue(note_record.content_hash)
            self.assertGreater(note_record.source_mtime_ns, 0)

            self.assertEqual(len(chunk_records), len(parsed_note.chunks))
            self.assertGreater(len(chunk_records), 0)
            self.assertEqual(chunk_records[0].note_id, note_record.note_id)
            self.assertEqual(chunk_records[0].heading_path, parsed_note.chunks[0].heading_path)
            self.assertTrue(all(record.content_hash for record in chunk_records))

    def test_save_and_load_graph_checkpoint_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            save_graph_checkpoint(
                db_path,
                graph_name="ask_graph",
                checkpoint_status=WorkflowCheckpointStatus.IN_PROGRESS,
                last_completed_node="prepare_ask",
                next_node_name="execute_ask",
                state={
                    "thread_id": "thread_checkpoint_roundtrip",
                    "run_id": "run_checkpoint_roundtrip",
                    "action_type": WorkflowAction.ASK_QA,
                    "user_query": "Roadmap",
                    "note_paths": [],
                    "retrieval_filter": RetrievalMetadataFilter(note_types=["summary_note"]),
                    "request_metadata": {"source": "unit_test"},
                    "approval_required": False,
                    "errors": [],
                },
            )

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_checkpoint_roundtrip",
                graph_name="ask_graph",
            )

            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertEqual(checkpoint.thread_id, "thread_checkpoint_roundtrip")
            self.assertEqual(checkpoint.last_run_id, "run_checkpoint_roundtrip")
            self.assertEqual(checkpoint.checkpoint_status, WorkflowCheckpointStatus.IN_PROGRESS)
            self.assertEqual(checkpoint.last_completed_node, "prepare_ask")
            self.assertEqual(checkpoint.next_node_name, "execute_ask")
            self.assertEqual(checkpoint.action_type, WorkflowAction.ASK_QA)
            self.assertEqual(checkpoint.state["user_query"], "Roadmap")
            self.assertEqual(
                checkpoint.state["retrieval_filter"].note_types,
                ["summary_note"],
            )

    def test_save_and_load_graph_checkpoint_keeps_business_fields_without_trace_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            save_graph_checkpoint(
                db_path,
                graph_name="ask_graph",
                checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
                last_completed_node="finalize_ask",
                next_node_name=None,
                state={
                    "thread_id": "thread_checkpoint_business_state",
                    "run_id": "run_checkpoint_business_state",
                    "action_type": WorkflowAction.ASK_QA,
                    "user_query": "Roadmap",
                    "ask_result": AskWorkflowResult(
                        mode=AskResultMode.RETRIEVAL_ONLY,
                        query="Roadmap",
                        answer="Summary",
                    ),
                    "approval_required": False,
                    "trace_events": [{"stale": True}],
                    "transient_prompt_context": {"stale": True},
                    "errors": [],
                },
            )

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_checkpoint_business_state",
                graph_name="ask_graph",
            )

            self.assertIsNotNone(checkpoint)
            assert checkpoint is not None
            self.assertEqual(checkpoint.checkpoint_status, WorkflowCheckpointStatus.COMPLETED)
            self.assertEqual(checkpoint.last_completed_node, "finalize_ask")
            self.assertEqual(checkpoint.last_run_id, "run_checkpoint_business_state")
            self.assertEqual(checkpoint.state["ask_result"].answer, "Summary")
            self.assertNotIn("trace_events", checkpoint.state)
            self.assertNotIn("transient_prompt_context", checkpoint.state)

    def test_hydrate_business_checkpoint_state_resets_run_identity_and_transient_fields(self) -> None:
        hydrated_state = hydrate_business_checkpoint_state(
            current_state={
                "thread_id": "thread_current",
                "run_id": "run_current",
                "action_type": WorkflowAction.ASK_QA,
            },
            restored_state={
                "thread_id": "thread_restored",
                "run_id": "run_restored",
                "action_type": WorkflowAction.ASK_QA,
                "ask_result": AskWorkflowResult(
                    mode=AskResultMode.RETRIEVAL_ONLY,
                    query="Roadmap",
                    answer="Summary",
                ),
                "trace_events": [{"old": True}],
                "transient_prompt_context": {"old": True},
            },
        )

        self.assertEqual(hydrated_state["thread_id"], "thread_current")
        self.assertEqual(hydrated_state["run_id"], "run_current")
        self.assertEqual(hydrated_state["action_type"], WorkflowAction.ASK_QA)
        self.assertEqual(hydrated_state["trace_events"], [])
        self.assertEqual(hydrated_state["transient_prompt_context"], {})
        self.assertEqual(hydrated_state["ask_result"].answer, "Summary")

    def test_save_and_load_proposal_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            connection = connect_sqlite(db_path)
            try:
                proposal_settings = replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                )
                proposal = Proposal(
                    proposal_id="prop_roundtrip",
                    action_type=WorkflowAction.INGEST_STEWARD,
                    target_note_path=str((vault_path / "daily" / "2026-03-14.md").resolve()),
                    summary="补两个标签并在 Summary 下插入一段回链建议",
                    evidence=[
                        ProposalEvidence(
                            source_path=str((vault_path / "notes" / "langgraph.md").resolve()),
                            heading_path="Overview > Why",
                            chunk_id="chunk_langgraph_1",
                            reason="当前笔记缺少这条概念回链。",
                        )
                    ],
                    patch_ops=[
                        PatchOp(
                            op="frontmatter_merge",
                            target_path=str(
                                (vault_path / "daily" / "2026-03-14.md").resolve()
                            ),
                            payload={"tags_add": ["langgraph", "review"]},
                        ),
                        PatchOp(
                            op="insert_under_heading",
                            target_path=str(
                                (vault_path / "daily" / "2026-03-14.md").resolve()
                            ),
                            payload={"heading_path": "Summary", "text": "- Related: [[LangGraph]]"},
                        ),
                    ],
                    safety_checks=SafetyChecks(
                        before_hash="sha256:before_hash_v1",
                        max_changed_lines=18,
                        contains_delete=False,
                    ),
                )

                save_proposal(
                    connection,
                    thread_id="thread_prop_roundtrip",
                    proposal=proposal,
                    approval_required=True,
                    run_id="run_prop_roundtrip",
                    idempotency_key="idem_prop_roundtrip",
                    settings=proposal_settings,
                )

                persisted = load_proposal(connection, proposal_id=proposal.proposal_id)
                self.assertIsNotNone(persisted)
                assert persisted is not None
                self.assertEqual(persisted.thread_id, "thread_prop_roundtrip")
                self.assertEqual(persisted.run_id, "run_prop_roundtrip")
                self.assertEqual(persisted.idempotency_key, "idem_prop_roundtrip")
                self.assertTrue(persisted.approval_required)
                self.assertEqual(
                    persisted.proposal.safety_checks.before_hash,
                    "sha256:before_hash_v1",
                )
                self.assertEqual(len(persisted.proposal.evidence), 1)
                self.assertEqual(
                    persisted.proposal.evidence[0].chunk_id,
                    "chunk_langgraph_1",
                )
                self.assertEqual(len(persisted.proposal.patch_ops), 2)
                self.assertEqual(
                    persisted.proposal.patch_ops[1].payload["heading_path"],
                    "Summary",
                )
            finally:
                connection.close()

    def test_save_proposal_persists_absolute_in_vault_paths_as_canonical_relative_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            target_note_path = vault_path / "Digest" / "2026-03-14.md"
            target_note_path.parent.mkdir(parents=True)
            target_note_path.write_text("# Digest\n", encoding="utf-8")
            linked_note_path = vault_path / "Notes" / "Alpha.md"
            linked_note_path.parent.mkdir(parents=True)
            linked_note_path.write_text("# Alpha\n", encoding="utf-8")

            db_path = temp_root / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            proposal = Proposal(
                proposal_id="prop_canonical_store",
                action_type=WorkflowAction.DAILY_DIGEST,
                target_note_path=str(target_note_path.resolve()),
                summary="Insert the generated digest into the daily review note.",
                evidence=[
                    ProposalEvidence(
                        source_path=str(linked_note_path.resolve()),
                        heading_path="Summary",
                        chunk_id="chunk_alpha",
                        reason="The note is grounded in a vault-local source.",
                    )
                ],
                patch_ops=[
                    PatchOp(
                        op="merge_frontmatter",
                        target_path=str(target_note_path.resolve()),
                        payload={"reviewed": False},
                    ),
                    PatchOp(
                        op="add_wikilink",
                        target_path=str(target_note_path.resolve()),
                        payload={
                            "heading": "## Links",
                            "linked_note_path": str(linked_note_path.resolve()),
                        },
                    ),
                ],
                safety_checks=SafetyChecks(
                    before_hash="sha256:canonical_before",
                    max_changed_lines=12,
                    contains_delete=False,
                ),
            )

            connection = connect_sqlite(db_path)
            try:
                save_proposal(
                    connection,
                    thread_id="thread_prop_canonical",
                    proposal=proposal,
                    approval_required=True,
                    run_id="run_prop_canonical",
                    idempotency_key="idem_prop_canonical",
                    settings=replace(get_settings(), sample_vault_dir=vault_path),
                )

                persisted = load_proposal(connection, proposal_id=proposal.proposal_id)
                self.assertIsNotNone(persisted)
                assert persisted is not None
                self.assertEqual(persisted.thread_id, "thread_prop_canonical")
                self.assertEqual(persisted.run_id, "run_prop_canonical")
                self.assertEqual(persisted.idempotency_key, "idem_prop_canonical")
                self.assertTrue(persisted.approval_required)
                self.assertEqual(
                    persisted.proposal.target_note_path,
                    "Digest/2026-03-14.md",
                )
                self.assertEqual(len(persisted.proposal.evidence), 1)
                self.assertEqual(
                    persisted.proposal.evidence[0].source_path,
                    "Notes/Alpha.md",
                )
                self.assertEqual(len(persisted.proposal.patch_ops), 2)
                self.assertEqual(
                    persisted.proposal.patch_ops[0].target_path,
                    "Digest/2026-03-14.md",
                )
                self.assertEqual(
                    persisted.proposal.patch_ops[1].target_path,
                    "Digest/2026-03-14.md",
                )
                self.assertEqual(
                    persisted.proposal.patch_ops[1].payload["linked_note_path"],
                    "Notes/Alpha.md",
                )

                proposal_row = connection.execute(
                    """
                    SELECT target_note_path
                    FROM proposal
                    WHERE proposal_id = ?;
                    """,
                    (proposal.proposal_id,),
                ).fetchone()
                evidence_row = connection.execute(
                    """
                    SELECT source_path
                    FROM proposal_evidence
                    WHERE proposal_id = ?;
                    """,
                    (proposal.proposal_id,),
                ).fetchone()
                patch_op_rows = connection.execute(
                    """
                    SELECT target_path, payload_json
                    FROM patch_op
                    WHERE proposal_id = ?
                    ORDER BY ordinal ASC;
                    """,
                    (proposal.proposal_id,),
                ).fetchall()

                assert proposal_row is not None
                assert evidence_row is not None
                self.assertEqual(proposal_row[0], "Digest/2026-03-14.md")
                self.assertEqual(evidence_row[0], "Notes/Alpha.md")
                self.assertEqual(patch_op_rows[0][0], "Digest/2026-03-14.md")
                self.assertEqual(patch_op_rows[1][0], "Digest/2026-03-14.md")
                self.assertEqual(
                    json.loads(patch_op_rows[1][1])["linked_note_path"],
                    "Notes/Alpha.md",
                )
            finally:
                connection.close()

    def test_list_pending_approval_records_only_returns_waiting_checkpoint_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            waiting_proposal = Proposal(
                proposal_id="prop_waiting_digest",
                action_type=WorkflowAction.DAILY_DIGEST,
                target_note_path=str((vault_path / "daily" / "2026-03-16.md").resolve()),
                summary="把今日摘要写回日记，并补两条待跟进问题。",
                risk_level=RiskLevel.MEDIUM,
                evidence=[
                    ProposalEvidence(
                        source_path=str((vault_path / "daily" / "2026-03-16.md").resolve()),
                        heading_path="今日总结",
                        chunk_id="chunk_waiting_digest",
                        reason="这条摘要已经有索引证据，可进入审批。",
                    )
                ],
                patch_ops=[
                    PatchOp(
                        op="insert_under_heading",
                        target_path=str((vault_path / "daily" / "2026-03-16.md").resolve()),
                        payload={"heading_path": "## Digest", "content": "- Follow up on eval drift"},
                    )
                ],
                safety_checks=SafetyChecks(
                    before_hash="sha256:waiting_before",
                    max_changed_lines=8,
                    contains_delete=False,
                ),
            )
            completed_proposal = Proposal(
                proposal_id="prop_completed_digest",
                action_type=WorkflowAction.DAILY_DIGEST,
                target_note_path=str((vault_path / "daily" / "2026-03-15.md").resolve()),
                summary="这条 proposal 已经被处理，不应再出现在收件箱。",
                risk_level=RiskLevel.HIGH,
                evidence=[],
                patch_ops=[],
                safety_checks=SafetyChecks(
                    before_hash="sha256:completed_before",
                    max_changed_lines=0,
                    contains_delete=False,
                ),
            )

            connection = connect_sqlite(db_path)
            try:
                proposal_settings = replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                )
                save_proposal(
                    connection,
                    thread_id="thread_waiting_digest",
                    proposal=waiting_proposal,
                    approval_required=True,
                    run_id="run_waiting_digest",
                    settings=proposal_settings,
                )
                save_proposal(
                    connection,
                    thread_id="thread_completed_digest",
                    proposal=completed_proposal,
                    approval_required=True,
                    run_id="run_completed_digest",
                    settings=proposal_settings,
                )
            finally:
                connection.close()

            save_graph_checkpoint(
                db_path,
                graph_name="digest_graph",
                checkpoint_status=WorkflowCheckpointStatus.WAITING_FOR_APPROVAL,
                last_completed_node="build_digest_proposal",
                next_node_name="human_approval",
                state={
                    "thread_id": "thread_waiting_digest",
                    "run_id": "run_waiting_digest",
                    "action_type": WorkflowAction.DAILY_DIGEST,
                    "proposal": waiting_proposal,
                    "approval_required": True,
                    "errors": [],
                },
            )
            save_graph_checkpoint(
                db_path,
                graph_name="digest_graph",
                checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
                last_completed_node="human_approval",
                next_node_name=None,
                state={
                    "thread_id": "thread_completed_digest",
                    "run_id": "run_completed_digest",
                    "action_type": WorkflowAction.DAILY_DIGEST,
                    "proposal": completed_proposal,
                    "approval_required": False,
                    "errors": [],
                },
            )

            connection = connect_sqlite(db_path)
            try:
                pending_records = list_pending_approval_records(connection)
            finally:
                connection.close()

            self.assertEqual(len(pending_records), 1)
            self.assertEqual(pending_records[0].thread_id, "thread_waiting_digest")
            self.assertEqual(
                pending_records[0].persisted_proposal.proposal.proposal_id,
                "prop_waiting_digest",
            )
            self.assertEqual(
                pending_records[0].persisted_proposal.proposal.summary,
                "把今日摘要写回日记，并补两条待跟进问题。",
            )

    def test_save_proposal_rejects_duplicate_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            connection = connect_sqlite(db_path)
            try:
                proposal_settings = replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                )
                first_proposal = Proposal(
                    proposal_id="prop_idem_1",
                    action_type=WorkflowAction.DAILY_DIGEST,
                    target_note_path=str((vault_path / "digest" / "daily.md").resolve()),
                    summary="first proposal",
                )
                second_proposal = Proposal(
                    proposal_id="prop_idem_2",
                    action_type=WorkflowAction.DAILY_DIGEST,
                    target_note_path=str((vault_path / "digest" / "daily.md").resolve()),
                    summary="second proposal",
                )

                save_proposal(
                    connection,
                    thread_id="thread_idem",
                    proposal=first_proposal,
                    approval_required=True,
                    idempotency_key="idem_conflict",
                    settings=proposal_settings,
                )

                with self.assertRaises(sqlite3.IntegrityError):
                    save_proposal(
                        connection,
                        thread_id="thread_idem",
                        proposal=second_proposal,
                        approval_required=True,
                        idempotency_key="idem_conflict",
                        settings=proposal_settings,
                    )
            finally:
                connection.close()

    def test_append_audit_log_event_persists_flattened_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            initialize_index_db(db_path)

            connection = connect_sqlite(db_path)
            try:
                proposal_settings = replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                )
                proposal = Proposal(
                    proposal_id="prop_audit_1",
                    action_type=WorkflowAction.INGEST_STEWARD,
                    target_note_path=str((vault_path / "notes" / "example.md").resolve()),
                    summary="写回一条治理建议",
                    patch_ops=[
                        PatchOp(
                            op="insert_under_heading",
                            target_path=str((vault_path / "notes" / "example.md").resolve()),
                            payload={"heading_path": "Summary", "text": "todo"},
                        )
                    ],
                    safety_checks=SafetyChecks(before_hash="sha256:audit_before"),
                )
                save_proposal(
                    connection,
                    thread_id="thread_audit",
                    proposal=proposal,
                    approval_required=True,
                    run_id="run_audit_proposal",
                    settings=proposal_settings,
                )

                audit_event = AuditEvent(
                    audit_event_id="audit_event_1",
                    thread_id="thread_audit",
                    proposal_id=proposal.proposal_id,
                    action_type=WorkflowAction.INGEST_STEWARD,
                    target_note_path=proposal.target_note_path,
                    approval_required=True,
                    approval_decision=ApprovalDecision(
                        approved=True,
                        reviewer="human_reviewer",
                        comment="风险可接受，允许写回",
                    ),
                    writeback_result=WritebackResult(
                        applied=True,
                        target_note_path=proposal.target_note_path,
                        before_hash="sha256:audit_before",
                        after_hash="sha256:audit_after",
                        applied_patch_ops=proposal.patch_ops,
                    ),
                    model_info={"provider": "mock", "model": "gpt-test"},
                    retrieved_chunk_ids=["chunk_langgraph_1", "chunk_langgraph_2"],
                    latency_ms=321,
                    created_at=datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc),
                )

                append_audit_log_event(
                    connection,
                    audit_event=audit_event,
                    run_id="run_audit_1",
                )

                row = connection.execute(
                    """
                    SELECT
                        thread_id,
                        run_id,
                        proposal_id,
                        approval_status,
                        reviewer,
                        before_hash,
                        after_hash,
                        writeback_applied,
                        retrieved_chunk_ids_json,
                        approval_payload_json,
                        writeback_result_json,
                        applied_patch_ops_json,
                        latency_ms
                    FROM audit_log
                    WHERE audit_event_id = ?;
                    """,
                    (audit_event.audit_event_id,),
                ).fetchone()
                self.assertIsNotNone(row)
                assert row is not None
                self.assertEqual(row["thread_id"], "thread_audit")
                self.assertEqual(row["run_id"], "run_audit_1")
                self.assertEqual(row["proposal_id"], proposal.proposal_id)
                self.assertEqual(row["approval_status"], "approved")
                self.assertEqual(row["reviewer"], "human_reviewer")
                self.assertEqual(row["before_hash"], "sha256:audit_before")
                self.assertEqual(row["after_hash"], "sha256:audit_after")
                self.assertEqual(row["writeback_applied"], 1)
                self.assertEqual(json.loads(row["retrieved_chunk_ids_json"]), audit_event.retrieved_chunk_ids)
                self.assertTrue(json.loads(row["approval_payload_json"])["approved"])
                self.assertTrue(json.loads(row["writeback_result_json"])["applied"])
                self.assertEqual(len(json.loads(row["applied_patch_ops_json"])), 1)
                self.assertEqual(row["latency_ms"], 321)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
