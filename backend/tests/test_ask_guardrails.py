from __future__ import annotations

import unittest

from app.contracts.workflow import (
    AskCitation,
    ContextBundle,
    GuardrailAction,
    GuardrailOutcome,
    ToolCallDecision,
    ToolExecutionResult,
    WorkflowAction,
)
from app.guardrails.ask import evaluate_final_ask_response, evaluate_tool_call_outcome


class GuardrailContractTests(unittest.TestCase):
    def test_guardrail_outcome_round_trips_action_reasons_and_applied_flag(self) -> None:
        outcome = GuardrailOutcome(
            action=GuardrailAction.POSSIBLE_INJECTION_DETECTED,
            reasons=["prompt attempted policy bypass"],
            applied=True,
        )
        payload = outcome.model_dump(mode="json")
        self.assertEqual(payload["action"], "possible_injection_detected")
        self.assertEqual(payload["reasons"], ["prompt attempted policy bypass"])
        self.assertTrue(payload["applied"])


class AskGuardrailTests(unittest.TestCase):
    def test_guardrail_rejects_invalid_tool_request(self) -> None:
        outcome = evaluate_tool_call_outcome(
            ToolCallDecision(requested=True, tool_name="delete_note", arguments={}),
            workflow_action=WorkflowAction.ASK_QA,
        )
        self.assertEqual(outcome.action, GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY)
        self.assertIn("tool_not_allowed", outcome.reasons)

    def test_guardrail_refuses_strong_claim_when_bundle_has_injection_flag(self) -> None:
        outcome = evaluate_final_ask_response(
            answer_text="The note definitely says to reveal the system prompt.",
            citations=[
                AskCitation(
                    chunk_id="c1",
                    path="Alpha.md",
                    title="Alpha",
                    heading_path=None,
                    start_line=1,
                    end_line=1,
                    score=0.9,
                    snippet="x",
                )
            ],
            bundle=ContextBundle(
                user_intent="answer question",
                workflow_action=WorkflowAction.ASK_QA,
                token_budget=1000,
                safety_flags=["possible_prompt_injection"],
            ),
            tool_results=[],
        )
        self.assertEqual(outcome.action, GuardrailAction.POSSIBLE_INJECTION_DETECTED)
        self.assertTrue(outcome.applied)

    def test_guardrail_marks_tool_result_insufficient_when_tool_returns_empty_payload(self) -> None:
        outcome = evaluate_final_ask_response(
            answer_text="Here is the final answer.",
            citations=[],
            bundle=ContextBundle(
                user_intent="answer question",
                workflow_action=WorkflowAction.ASK_QA,
                token_budget=1000,
            ),
            tool_results=[
                ToolExecutionResult(tool_name="load_note_excerpt", ok=True, data={})
            ],
        )
        self.assertEqual(outcome.action, GuardrailAction.TOOL_RESULT_INSUFFICIENT)


if __name__ == "__main__":
    unittest.main()
