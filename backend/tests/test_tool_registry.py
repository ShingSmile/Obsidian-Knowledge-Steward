from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from app.config import get_settings
from app.contracts.workflow import (
    GuardrailAction,
    ToolCallDecision,
    ToolSpec,
    WorkflowAction,
)
from app.indexing.parser import parse_markdown_note
from app.indexing.store import (
    build_chunk_records,
    build_note_record,
    connect_sqlite,
    initialize_index_db,
    sync_note_and_chunks,
)
from app.tools.registry import execute_tool_call, get_allowed_tools_for_workflow, validate_tool_call


class ToolContractTests(unittest.TestCase):
    def test_tool_spec_defaults_to_read_only_and_requires_allowed_workflows(self) -> None:
        spec = ToolSpec(
            name="search_notes",
            purpose="search indexed notes",
            allowed_workflows=[WorkflowAction.ASK_QA],
            input_schema={"type": "object", "required": ["query"]},
            output_schema={"type": "object"},
            risk_level="low",
        )
        self.assertTrue(spec.read_only)
        self.assertEqual(spec.allowed_workflows, [WorkflowAction.ASK_QA])


class ToolRegistryTests(unittest.TestCase):
    def test_get_allowed_tools_for_ask_includes_outline_and_backlinks(self) -> None:
        specs = get_allowed_tools_for_workflow(WorkflowAction.ASK_QA)
        self.assertEqual(
            [spec.name for spec in specs],
            [
                "search_notes",
                "load_note_excerpt",
                "get_note_outline",
                "find_backlinks",
                "list_pending_approvals",
            ],
        )
        self.assertTrue(all(spec.read_only for spec in specs))

    def test_validate_tool_call_rejects_unknown_tool_and_wrong_workflow(self) -> None:
        outcome = validate_tool_call(
            ToolCallDecision(requested=True, tool_name="delete_note", arguments={}),
            workflow_action=WorkflowAction.ASK_QA,
        )
        self.assertEqual(outcome.action, GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY)
        self.assertIn("tool_not_allowed", outcome.reasons)

    def test_validate_tool_call_rejects_known_tool_for_disallowed_workflow(self) -> None:
        outcome = validate_tool_call(
            ToolCallDecision(
                requested=True,
                tool_name="search_notes",
                arguments={"query": "alpha"},
            ),
            workflow_action=WorkflowAction.DAILY_DIGEST,
        )
        self.assertEqual(outcome.action, GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY)
        self.assertIn("workflow_not_allowed", outcome.reasons)

    def test_validate_tool_call_rejects_invalid_arguments(self) -> None:
        outcome = validate_tool_call(
            ToolCallDecision(
                requested=True,
                tool_name="search_notes",
                arguments={"limit": 3, "extra": "x"},
            ),
            workflow_action=WorkflowAction.ASK_QA,
        )
        self.assertEqual(outcome.action, GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY)
        self.assertIn("invalid_tool_arguments", outcome.reasons)

    def test_execute_load_note_excerpt_reads_only_requested_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            (vault_path / "Alpha.md").write_text(
                "# Alpha\n\nThis note is used for excerpt testing.\n",
                encoding="utf-8",
            )
            settings = replace(get_settings(), sample_vault_dir=vault_path)

            result = execute_tool_call(
                ToolCallDecision(
                    requested=True,
                    tool_name="load_note_excerpt",
                    arguments={"note_path": "Alpha.md", "max_chars": 80},
                ),
                workflow_action=WorkflowAction.ASK_QA,
                settings=settings,
            )
            self.assertTrue(result.ok)
            self.assertIn("excerpt", result.data)

    def test_execute_get_note_outline_reads_current_heading_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            note_path = vault_path / "Alpha.md"
            frontmatter_block = """---
tags:
  - current
---
"""
            note_path.write_text(
                frontmatter_block
                + "# Alpha\n"
                + "\n"
                + "Intro\n"
                + "\n"
                + "## Detail\n"
                + "\n"
                + "More text\n",
                encoding="utf-8",
            )
            settings = replace(get_settings(), sample_vault_dir=vault_path)

            result = execute_tool_call(
                ToolCallDecision(
                    requested=True,
                    tool_name="get_note_outline",
                    arguments={"note_path": "Alpha.md"},
                ),
                workflow_action=WorkflowAction.ASK_QA,
                settings=settings,
            )

            self.assertTrue(result.ok)
            self.assertEqual(result.data["note_path"], "Alpha.md")
            self.assertEqual(result.data["title"], "Alpha")
            self.assertTrue(result.data["has_frontmatter"])
            self.assertEqual(
                result.data["frontmatter_summary"],
                {
                    "raw_text": frontmatter_block,
                    "line_count": 4,
                    "char_count": len(frontmatter_block),
                },
            )
            self.assertEqual(
                result.data["headings"],
                [
                    {
                        "level": 1,
                        "text": "Alpha",
                        "line_no": 5,
                        "heading_path": "Alpha",
                    },
                    {
                        "level": 2,
                        "text": "Detail",
                        "line_no": 9,
                        "heading_path": "Alpha > Detail",
                    },
                ],
            )

    def test_execute_get_note_outline_returns_empty_frontmatter_summary_without_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            note_path = vault_path / "Alpha.md"
            note_path.write_text("# Alpha\n\nIntro\n", encoding="utf-8")
            settings = replace(get_settings(), sample_vault_dir=vault_path)

            result = execute_tool_call(
                ToolCallDecision(
                    requested=True,
                    tool_name="get_note_outline",
                    arguments={"note_path": "Alpha.md"},
                ),
                workflow_action=WorkflowAction.ASK_QA,
                settings=settings,
            )

            self.assertTrue(result.ok)
            self.assertEqual(result.data["frontmatter_summary"], {})

    def test_execute_find_backlinks_fails_closed_when_candidate_note_is_stale(self) -> None:
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
                for note_path in (target_path, source_path):
                    parsed_note = parse_markdown_note(note_path)
                    note_record = build_note_record(
                        note_path,
                        parsed_note,
                        vault_root=vault_path,
                    )
                    chunk_records = build_chunk_records(note_record.note_id, parsed_note)
                    sync_note_and_chunks(connection, note_record, chunk_records)
            finally:
                connection.close()

            source_path.write_text("# Source\n\nLinks to [[Target]] and more.\n", encoding="utf-8")
            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            )

            result = execute_tool_call(
                ToolCallDecision(
                    requested=True,
                    tool_name="find_backlinks",
                    arguments={"note_path": "Target.md"},
                ),
                workflow_action=WorkflowAction.ASK_QA,
                settings=settings,
            )

            self.assertFalse(result.ok)
            self.assertEqual(result.error, "index_stale")
            self.assertEqual(result.data, {})
            self.assertEqual(result.diagnostics["failure_code"], "index_stale")

    def test_execute_find_backlinks_rejects_paths_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            settings = replace(get_settings(), sample_vault_dir=vault_path)

            result = execute_tool_call(
                ToolCallDecision(
                    requested=True,
                    tool_name="find_backlinks",
                    arguments={"note_path": "../outside.md"},
                ),
                workflow_action=WorkflowAction.ASK_QA,
                settings=settings,
            )

            self.assertFalse(result.ok)
            self.assertEqual(result.error, "note_path_outside_vault")
            self.assertEqual(result.data, {})
            self.assertEqual(result.diagnostics["failure_code"], "note_path_outside_vault")

    def test_execute_find_backlinks_returns_verified_backlinks(self) -> None:
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
                for note_path in (target_path, source_path):
                    parsed_note = parse_markdown_note(note_path)
                    note_record = build_note_record(
                        note_path,
                        parsed_note,
                        vault_root=vault_path,
                    )
                    chunk_records = build_chunk_records(note_record.note_id, parsed_note)
                    sync_note_and_chunks(connection, note_record, chunk_records)
            finally:
                connection.close()

            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            )

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
            self.assertEqual(
                result.data["backlinks"],
                [
                    {
                        "source_path": "Source.md",
                        "chunk_id": result.data["backlinks"][0]["chunk_id"],
                        "heading_path": "Source",
                        "start_line": 1,
                        "end_line": 3,
                        "link_text": "Target",
                    }
                ],
            )
            self.assertEqual(result.diagnostics["candidate_count"], 1)
            self.assertEqual(result.diagnostics["verified_candidate_count"], 1)


if __name__ == "__main__":
    unittest.main()
