# TASK-054 Ingest And Digest Eval Baseline Design

**Task:** `TASK-054`

**Session:** `SES-20260406-01`

**Problem**

`TASK-053` already gave ask a stable offline quality baseline with four explicit
dimensions. Ingest and digest are still evaluated through the same generic
`quality_metrics` shape in `eval/run_eval.py`, but the keys are ask-centric:
`answer_relevancy`, `context_precision`, and `context_recall`. That leaves the
governance and digest chains with names that do not match the task contract,
even when the underlying signal is useful. The current golden suites also do not
yet enforce the `TASK-054` requirement that ingest expose `Rationale Faithfulness`
plus `Patch Safety`, and digest expose `Faithfulness` plus `Coverage`.

**Goal**

Keep ask unchanged, but make ingest and digest emit scenario-specific offline
metrics that match `TASK-054`, then update golden cases and eval overview output
so the governance benchmark no longer depends on misleading ask-style metric
names.

**Non-Goals**

- Do not change ingest or digest runtime behavior.
- Do not move offline eval logic into runtime services.
- Do not redesign the benchmark grouping layout.
- Do not start `TASK-049` or any tool-calling refactor.

**Approaches Considered**

1. Add alias names on top of the current generic metrics.
   Rejected because the contract would still be semantically loose: governance
   would keep speaking in `relevancy/context_precision/context_recall`.
2. Make the eval runner dispatch by scenario and compute domain metrics per chain.
   Recommended because it satisfies `TASK-054` directly and keeps ask isolated.
3. Introduce a fully generic metric registry with pluggable scenario adapters.
   Rejected for this slice because it adds framework weight without a second user.

**Recommended Approach**

Split offline metric construction in `eval/run_eval.py` by scenario:

- ask keeps the existing four-dimension panel untouched
- governance emits `rationale_faithfulness` and `patch_safety`
- digest emits `faithfulness` and `coverage`

The metric overview should aggregate only the metric keys that actually exist for
the selected scenarios, instead of assuming every scenario emits the ask panel.
Existing benchmark and scenario overview structures stay in place; only the
metric payloads and their aggregators become scenario-aware.

**Metric Definitions**

Governance:

- `rationale_faithfulness`
  - reuse the existing claim-level faithfulness core against the proposal-facing
    textual rationale and evidence
  - success means the generated governance reasoning stays supported by the note
    and retrieved related candidates
- `patch_safety`
  - score the emitted patch plan against conservative static invariants already
    visible in the snapshot:
    - proposal absent when fallback path is expected counts as safe success
    - proposal patch ops must stay within the allowed op set for the case
    - evidence must exist when a proposal is present
    - target note path and patch op count must match the expected constrained plan

Digest:

- `faithfulness`
  - reuse the existing claim-level faithfulness core against `digest_markdown`
    and source note evidence
- `coverage`
  - explicit rename of the digest/source-note coverage signal that is currently
    hidden inside `context_recall`
  - measures how well the selected digest source notes cover the expected
    reference context paths for the case

Ask:

- leave `faithfulness`, `answer_relevancy`, `relevancy`, `context_precision`,
  and `context_recall` unchanged

**Design**

1. Keep one public `build_quality_metrics_snapshot()` entrypoint, but dispatch to
   scenario-specific helpers.
2. Extend the governance snapshot logic so it can score patch safety from the
   already materialized proposal snapshot and expected contract.
3. Reuse the existing semantic faithfulness helper for both governance and digest
   so the quality language stays aligned with `TASK-051` and `TASK-052`.
4. Change metric overview builders to aggregate only present metric keys.
5. Keep the benchmark grouping and failure-type breakdown stable so downstream
   docs and dashboards do not need a parallel migration.

**Golden Changes**

- Rewrite governance cases to expect `rationale_faithfulness` and `patch_safety`
  instead of generic ask-style metrics.
- Rewrite digest metric-bearing cases to expect `faithfulness` and `coverage`.
- Add at least one more governance case and one more digest case so each chain
  satisfies the `>= 3` case coverage requirement in `TASK-054`.

**Files**

- Modify: `eval/run_eval.py`
- Modify: `backend/tests/test_eval_runner.py`
- Modify: `eval/golden/governance_cases.json`
- Modify: `eval/golden/digest_cases.json`
- Optionally modify: `eval/golden/resume_cases.json` only if governance benchmark
  aggregation needs an additional non-digest governance control

**Testing Strategy**

- First lock failing eval-runner tests that assert the new governance and digest
  metric keys plus benchmark overview behavior.
- Then update golden files so those targeted eval runs pass.
- Finally run the focused eval-runner suite plus the exact governance/digest cases
  exercised by the new tests.

**Risks**

- Governance `patch_safety` can become too coupled to golden details rather than
  true safety constraints.
- Digest `coverage` can look perfect if the fixture and source-note selection are
  accidentally identical rather than meaningfully validated.
- Metric overview changes can regress ask reporting if aggregation becomes
  scenario-blind in a new way.

**Mitigations**

- Keep `patch_safety` scoped to stable constrained-plan signals already enforced
  elsewhere: patch ops, evidence presence, and target-note consistency.
- Preserve ask’s existing metric path unchanged and add regression assertions for
  mixed ask/governance/digest runs.
- Use deterministic fixture cases rather than only sample-vault cases for the new
  metric coverage assertions.
