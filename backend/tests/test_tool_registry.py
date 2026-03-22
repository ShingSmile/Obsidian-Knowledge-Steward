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
    def test_get_allowed_tools_for_ask_returns_only_read_only_specs(self) -> None:
        specs = get_allowed_tools_for_workflow(WorkflowAction.ASK_QA)
        self.assertEqual(
            [spec.name for spec in specs],
            ["search_notes", "load_note_excerpt", "list_pending_approvals"],
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


if __name__ == "__main__":
    unittest.main()
