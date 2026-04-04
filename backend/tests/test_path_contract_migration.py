from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from app.config import get_settings
from app.contracts.workflow import ToolCallDecision, WorkflowAction
from app.graphs.checkpoint import WorkflowCheckpointStatus
from app.indexing.ingest import ingest_vault
from app.indexing.parser import parse_markdown_note
from app.indexing.store import (
    build_chunk_records,
    build_note_record,
    connect_sqlite,
    initialize_index_db,
    sync_note_and_chunks,
)
from app.tools.registry import execute_tool_call


class PathContractMigrationTests(unittest.TestCase):
    def test_initialize_index_db_migrates_legacy_absolute_note_paths_before_reingest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            alpha_path = vault_path / "Alpha.md"
            alpha_path.write_text("# Alpha\n\nalpha body\n", encoding="utf-8")

            initialize_index_db(db_path)
            connection = connect_sqlite(db_path)
            try:
                parsed_note = parse_markdown_note(alpha_path)
                canonical_note_record = build_note_record(
                    alpha_path,
                    parsed_note,
                    vault_root=vault_path,
                )
                legacy_note_path = str(alpha_path.resolve())
                legacy_note_id = _legacy_note_id(legacy_note_path)
                legacy_note_record = replace(
                    canonical_note_record,
                    note_id=legacy_note_id,
                    path=legacy_note_path,
                )
                legacy_chunk_records = [
                    replace(chunk_record, note_id=legacy_note_id)
                    for chunk_record in build_chunk_records(
                        canonical_note_record.note_id,
                        parsed_note,
                    )
                ]
                sync_note_and_chunks(connection, legacy_note_record, legacy_chunk_records)
            finally:
                connection.close()

            settings = replace(get_settings(), sample_vault_dir=vault_path)
            initialize_index_db(db_path, settings=settings)
            stats = ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)

            connection = connect_sqlite(db_path)
            try:
                stored_paths = [
                    row["path"]
                    for row in connection.execute(
                        "SELECT path FROM note ORDER BY path ASC;"
                    ).fetchall()
                ]
                chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(stats.scanned_notes, 1)
            self.assertEqual(stats.created_notes, 0)
            self.assertEqual(stats.updated_notes, 1)
            self.assertEqual(stored_paths, ["Alpha.md"])
            self.assertEqual(chunk_count, 1)

    def test_initialize_index_db_migrates_legacy_note_paths_for_backlink_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            target_path = vault_path / "Target.md"
            source_path = vault_path / "Source.md"
            target_path.write_text("# Target\n\nBody\n", encoding="utf-8")
            source_path.write_text("# Source\n\nLinks to [[Target]].\n", encoding="utf-8")

            initialize_index_db(db_path)
            connection = connect_sqlite(db_path)
            try:
                target_parsed = parse_markdown_note(target_path)
                target_record = build_note_record(
                    target_path,
                    target_parsed,
                    vault_root=vault_path,
                )
                target_chunks = build_chunk_records(target_record.note_id, target_parsed)
                sync_note_and_chunks(connection, target_record, target_chunks)

                source_parsed = parse_markdown_note(source_path)
                canonical_source_record = build_note_record(
                    source_path,
                    source_parsed,
                    vault_root=vault_path,
                )
                legacy_source_path = "/vault/Source.md"
                legacy_source_id = _legacy_note_id(legacy_source_path)
                legacy_source_record = replace(
                    canonical_source_record,
                    note_id=legacy_source_id,
                    path=legacy_source_path,
                )
                legacy_source_chunks = [
                    replace(chunk_record, note_id=legacy_source_id)
                    for chunk_record in build_chunk_records(
                        canonical_source_record.note_id,
                        source_parsed,
                    )
                ]
                sync_note_and_chunks(connection, legacy_source_record, legacy_source_chunks)
            finally:
                connection.close()

            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            )
            initialize_index_db(db_path, settings=settings)
            result = execute_tool_call(
                ToolCallDecision(
                    requested=True,
                    tool_name="find_backlinks",
                    arguments={"note_path": "Target.md"},
                ),
                workflow_action=WorkflowAction.ASK_QA,
                settings=settings,
            )

            self.assertTrue(result.ok)
            self.assertEqual(result.data["target_path"], "Target.md")
            self.assertEqual(result.data["backlinks"][0]["source_path"], "Source.md")

    def test_initialize_index_db_rewrites_legacy_checkpoint_state_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"

            initialize_index_db(db_path)
            connection = connect_sqlite(db_path)
            try:
                state_payload = {
                    "thread_id": "thread_path_migration",
                    "run_id": "run_path_migration",
                    "action_type": WorkflowAction.DAILY_DIGEST.value,
                    "approval_required": True,
                    "note_paths": [str((vault_path / "Digest.md").resolve())],
                    "proposal": {
                        "target_note_path": str((vault_path / "Digest.md").resolve()),
                        "patch_ops": [
                            {
                                "target_path": str((vault_path / "Digest.md").resolve()),
                            }
                        ],
                        "evidence": [
                            {
                                "source_path": "/vault/Source.md",
                            }
                        ],
                    },
                    "writeback_result": {
                        "target_note_path": "/vault/Digest.md",
                        "applied_patch_ops": [
                            {
                                "target_path": str((vault_path / "Digest.md").resolve()),
                            }
                        ],
                    },
                    "errors": [],
                }
                connection.execute(
                    """
                    INSERT INTO workflow_checkpoint (
                        checkpoint_id,
                        thread_id,
                        graph_name,
                        action_type,
                        last_run_id,
                        checkpoint_status,
                        last_completed_node,
                        next_node_name,
                        state_json,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
                    """,
                    (
                        "ckpt_path_migration",
                        "thread_path_migration",
                        "digest_graph",
                        WorkflowAction.DAILY_DIGEST.value,
                        "run_path_migration",
                        WorkflowCheckpointStatus.WAITING_FOR_APPROVAL.value,
                        "await_approval",
                        "resume_after_approval",
                        json.dumps(state_payload),
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            settings = replace(get_settings(), sample_vault_dir=vault_path)
            initialize_index_db(db_path, settings=settings)

            connection = connect_sqlite(db_path)
            try:
                migrated_state = json.loads(
                    connection.execute(
                        """
                        SELECT state_json
                        FROM workflow_checkpoint
                        WHERE checkpoint_id = ?;
                        """,
                        ("ckpt_path_migration",),
                    ).fetchone()["state_json"]
                )
            finally:
                connection.close()

            self.assertEqual(migrated_state["note_paths"], ["Digest.md"])
            self.assertEqual(migrated_state["proposal"]["target_note_path"], "Digest.md")
            self.assertEqual(
                migrated_state["proposal"]["patch_ops"][0]["target_path"],
                "Digest.md",
            )
            self.assertEqual(
                migrated_state["proposal"]["evidence"][0]["source_path"],
                "Source.md",
            )
            self.assertEqual(
                migrated_state["writeback_result"]["target_note_path"],
                "Digest.md",
            )
            self.assertEqual(
                migrated_state["writeback_result"]["applied_patch_ops"][0]["target_path"],
                "Digest.md",
            )


def _legacy_note_id(path: str) -> str:
    return f"note_{hashlib.sha1(path.encode('utf-8')).hexdigest()[:16]}"


if __name__ == "__main__":
    unittest.main()
