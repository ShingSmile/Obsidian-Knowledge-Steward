# TASK-048 Runtime Faithfulness Gate Design

**Task:** `TASK-048`

**Session:** `SES-20260401-02`

**Problem**

The repo already has an offline ask-quality baseline in `eval/run_eval.py`, including
`ask_groundedness`, `unsupported_claim`, and four basic quality metrics. That logic is
currently trapped inside the eval script. Runtime ask guardrails still only check
citation presence, citation bounds, prompt-injection flags, and empty tool payloads.
As a result, offline eval and runtime safety do not share the same faithfulness model.

**Goal**

Land the first executable slice of `TASK-048` by extracting a shared ask-faithfulness
evaluator and wiring it into the ask runtime as a conservative downgrade gate, while
making offline eval reuse the same evaluator.

**Non-Goals**

- Do not implement full claim decomposition or NLI in this slice.
- Do not add ingest/digest runtime faithfulness gates in this slice.
- Do not change plugin UI or add new response fields to the external workflow API.
- Do not redesign the whole eval platform.

**Recommended Approach**

Create a small shared quality module under `backend/app/quality/` that evaluates a
generated ask answer against its cited evidence and produces a structured
faithfulness snapshot. The runtime ask path uses that snapshot after citation
alignment and before returning a generated answer. If the snapshot bucket is
`unsupported_claim`, runtime downgrades to `retrieval_only` through the existing
fallback path. `eval/run_eval.py` stops duplicating the same heuristics and imports
the shared evaluator instead.

**Alternatives Considered**

1. Keep the logic in `eval/run_eval.py` and reimplement a second version in
   `backend/app/guardrails/ask.py`.
   Rejected because runtime and offline semantics would drift immediately.
2. Build the full cross-link claim-NLI framework first.
   Rejected because it is larger than one safe session slice and would delay the
   first runtime protection.
3. Only improve offline eval and defer runtime changes.
   Rejected because it leaves the live ask path unprotected against known
   semantic-overclaim patterns.

**Design**

Introduce a shared evaluator that returns a stable snapshot with these fields:

- `bucket`
- `consistent`
- `reason`
- `citation_numbers`
- `cited_candidate_count`
- `unsupported_terms`
- `answer_text`

For this slice, bucket semantics stay aligned with the existing eval behavior:

- `not_generated_answer`
- `citation_missing`
- `citation_invalid`
- `unsupported_claim`
- `grounded`

The evaluator should accept an `AskWorkflowResult` and compute its result from the
generated answer text plus the cited `retrieved_candidates`. The term extraction and
unsupported-term logic can move with minimal behavior change from `eval/run_eval.py`
into the shared module.

**Runtime Flow**

1. Ask generation finishes and citation alignment passes.
2. The shared evaluator scores the generated answer.
3. If the bucket is `unsupported_claim`, runtime returns the existing
   `retrieval_only` fallback with a guardrail downgrade.
4. Otherwise the generated answer is returned unchanged.

This keeps the external contract stable while making the runtime safer.

**Files**

- Create: `backend/app/quality/__init__.py`
- Create: `backend/app/quality/faithfulness.py`
- Modify: `backend/app/guardrails/ask.py`
- Modify: `backend/app/services/ask.py`
- Modify: `backend/tests/test_ask_guardrails.py`
- Modify: `backend/tests/test_ask_workflow.py`
- Modify: `backend/tests/test_eval_runner.py`
- Modify: `eval/run_eval.py`

**Testing Strategy**

- Add a runtime ask test that currently returns a generated answer with legal
  citations but unsupported semantic claims; after the change it must downgrade to
  `retrieval_only`.
- Add a runtime ask test proving a grounded generated answer still passes.
- Add a shared-evaluator test around unsupported-term detection.
- Keep the existing eval overclaim cases passing while switching `run_eval.py` to
  the shared evaluator.

**Risks**

- The heuristic evaluator can over-downgrade grounded answers.
- The evaluator currently relies on lightweight term extraction instead of real NLI.
- Pulling the logic out of `eval/run_eval.py` may accidentally change existing eval
  snapshots if not covered by targeted regression tests.

**Mitigations**

- Reuse existing overclaim bad cases as regression guards.
- Add one positive runtime test so the new gate is not only tested on downgrade.
- Keep this slice ask-only so the interface can settle before extending it to
  ingest/digest.
