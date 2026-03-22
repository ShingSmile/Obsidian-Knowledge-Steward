from __future__ import annotations

from app.contracts.workflow import (
    AskCitation,
    ContextBundle,
    GuardrailAction,
    GuardrailOutcome,
    ToolCallDecision,
    ToolExecutionResult,
    WorkflowAction,
)
from app.tools.registry import validate_tool_call


def evaluate_tool_call_outcome(
    decision: ToolCallDecision,
    *,
    workflow_action: WorkflowAction,
) -> GuardrailOutcome:
    if not decision.requested:
        return GuardrailOutcome(action=GuardrailAction.ALLOW, applied=False)
    if not decision.tool_name:
        return GuardrailOutcome(
            action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY,
            applied=True,
            reasons=["missing_tool_name"],
        )
    return validate_tool_call(decision, workflow_action=workflow_action)


def evaluate_final_ask_response(
    *,
    answer_text: str,
    citations: list[AskCitation],
    bundle: ContextBundle,
    tool_results: list[ToolExecutionResult],
) -> GuardrailOutcome:
    _ = answer_text

    if "possible_prompt_injection" in bundle.safety_flags:
        return GuardrailOutcome(
            action=GuardrailAction.POSSIBLE_INJECTION_DETECTED,
            applied=True,
            reasons=["bundle_flagged"],
        )
    if any(result.ok and not result.data for result in tool_results):
        return GuardrailOutcome(
            action=GuardrailAction.TOOL_RESULT_INSUFFICIENT,
            applied=True,
            reasons=["empty_tool_payload"],
        )
    if not citations:
        return GuardrailOutcome(
            action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY,
            applied=True,
            reasons=["missing_citations"],
        )
    return GuardrailOutcome(action=GuardrailAction.ALLOW, applied=False)
