from __future__ import annotations

import unittest

from app.contracts.workflow import ContextBundle, ContextEvidenceItem, WorkflowAction


class ContextContractTests(unittest.TestCase):
    def test_context_bundle_round_trips_with_tool_and_safety_metadata(self) -> None:
        bundle = ContextBundle(
            user_intent="find governance note",
            workflow_action=WorkflowAction.ASK_QA,
            evidence_items=[
                ContextEvidenceItem(
                    source_path="Alpha.md",
                    chunk_id="chunk-alpha",
                    heading_path="Alpha > Notes",
                    text="governance overview",
                    score=0.91,
                    source_kind="retrieval",
                )
            ],
            tool_results=[],
            allowed_tool_names=["search_notes"],
            token_budget=1200,
            safety_flags=["suspicious_instruction"],
            assembly_notes=["deduplicated:1"],
        )
        payload = bundle.model_dump(mode="json")
        self.assertEqual(payload["workflow_action"], "ask_qa")
        self.assertEqual(payload["evidence_items"][0]["source_kind"], "retrieval")
        self.assertEqual(payload["safety_flags"], ["suspicious_instruction"])


if __name__ == "__main__":
    unittest.main()
