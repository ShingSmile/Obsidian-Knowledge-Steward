# TASK-052 Runtime Semantic Gate Design

**Task:** `TASK-052`

**Session:** `SES-20260402-01`

**Problem**

`TASK-051` already landed a shared claim-level semantic faithfulness core in
`backend/app/quality/faithfulness.py`, and offline ask / governance / digest eval
now reuses it. Runtime behavior is still split: ask uses the older
`build_ask_faithfulness_snapshot()` heuristic in `backend/app/guardrails/ask.py`,
while digest has no runtime quality gate or structured low-confidence outcome at all.
This leaves runtime safety and offline quality speaking different languages.

**Goal**

Reuse the shared semantic core at runtime so ask and digest both emit a stable
quality outcome with score / threshold / backend / reason metadata, while keeping
the scope to one medium task.

**Non-Goals**

- Do not add an external LLM judge or new model-serving subsystem.
- Do not implement ingest runtime faithfulness gating.
- Do not build the ask four-dimension offline evaluation panel.
- Do not expose runtime quality metadata in the plugin UI.

**Recommended Approach**

Add one shared runtime evaluator in `backend/app/quality/faithfulness.py` that wraps
the existing claim-level report and reduces it to a conservative runtime outcome:
`allow`, `downgrade_to_retrieval_only`, or `low_confidence`. Ask consumes it after
generated-answer validation and downgrades to `retrieval_only` when the unsupported
ratio breaches the configured threshold. Digest consumes the same evaluator against
its generated markdown and assembled evidence, but keeps the digest result while
marking it as low confidence instead of refusing output.

**Alternatives Considered**

1. Keep ask on the heuristic snapshot and add digest-only runtime metadata.
   Rejected because runtime semantics would stay split across chains.
2. Push the full gate to graph orchestration instead of services/contracts.
   Rejected because it expands this slice into a graph refactor.
3. Add digest metadata under `context_bundle_summary` without changing contracts.
   Rejected because the quality outcome would remain weakly structured.

**Design**

Introduce a small shared runtime-quality shape with:

- `outcome`
- `score`
- `threshold`
- `backend`
- `reason`
- `claim_count`
- `unsupported_claim_count`

Ask wiring:

1. Generated answer passes citation validation and existing final guardrails.
2. Runtime semantic evaluator compares the answer against cited evidence.
3. If the unsupported ratio breaches threshold, runtime downgrades to the existing
   `retrieval_only` path and records the semantic guardrail reason.
4. Otherwise ask returns the generated answer unchanged.

Digest wiring:

1. `run_minimal_digest()` builds the digest markdown and the assembled evidence set.
2. Runtime semantic evaluator compares the digest markdown against the evidence.
3. The digest result always returns, but now includes a structured quality outcome.
4. Low-confidence outcomes are written to trace metadata so later runtime review and
   offline eval can talk about the same failure mode.

**Contract Changes**

- Extend `DigestWorkflowResult` with structured runtime quality metadata rather than
  burying it in `context_bundle_summary`.
- Keep the ask external result mode stable.
- Reuse the existing `GuardrailAction.REFUSE_STRONG_CLAIM` for ask downgrade.

**Files**

- Modify: `backend/app/quality/faithfulness.py`
- Modify: `backend/app/guardrails/ask.py`
- Modify: `backend/app/services/ask.py`
- Modify: `backend/app/services/digest.py`
- Modify: `backend/app/contracts/workflow.py`
- Modify: `backend/app/graphs/digest_graph.py`
- Modify: `backend/tests/test_faithfulness.py`
- Modify: `backend/tests/test_ask_workflow.py`
- Modify: `backend/tests/test_digest_workflow.py`

**Testing Strategy**

- Add an ask runtime test that still downgrades an unsupported semantic overclaim.
- Add an ask runtime test proving a grounded answer is not downgraded by the new
  semantic evaluator.
- Add a digest test that returns a low-confidence quality outcome when the markdown
  claims exceed the assembled evidence.
- Add a digest trace assertion that score / threshold / outcome metadata is emitted.

**Risks**

- The shared semantic runtime gate may over-downgrade grounded ask answers.
- Digest may surface low-confidence results too often because its template text is
  broader than the raw evidence.
- Contract changes for digest can ripple into graph and workflow tests.

**Mitigations**

- Keep the runtime policy conservative and threshold-based, not contradiction-based
  perfectionism.
- Add one positive ask case and one digest low-confidence regression guard.
- Limit this slice to backend contracts and trace metadata only.
