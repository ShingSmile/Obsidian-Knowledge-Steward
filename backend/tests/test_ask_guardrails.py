from __future__ import annotations

import unittest

from app.contracts.workflow import GuardrailAction, GuardrailOutcome


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


if __name__ == "__main__":
    unittest.main()
