from __future__ import annotations

import unittest

from app.contracts.workflow import ToolSpec, WorkflowAction


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


if __name__ == "__main__":
    unittest.main()
