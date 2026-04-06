# TASK-054 Ingest And Digest Eval Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make offline eval report scenario-specific ingest and digest quality metrics that satisfy `TASK-054`, while leaving ask’s four-dimension panel unchanged.

**Architecture:** Keep `eval/run_eval.py` as the single eval snapshot entrypoint, but split metric construction by scenario. Governance emits `rationale_faithfulness` and `patch_safety`; digest emits `faithfulness` and `coverage`; ask keeps the existing four ask metrics. Update metric overview aggregation and the governance/digest golden suites to match.

**Tech Stack:** Python 3.12, FastAPI workflow entrypoints, Pydantic snapshots, offline JSON golden suites, `unittest`.

---

## File Structure

### Modify

- `eval/run_eval.py`
  - Dispatch quality snapshot construction by scenario and aggregate only present metric keys.
- `backend/tests/test_eval_runner.py`
  - Lock the new governance/digest metric contracts and mixed-scenario overview behavior.
- `eval/golden/governance_cases.json`
  - Replace ask-style generic metric expectations with governance-specific keys and add one more governance case if needed.
- `eval/golden/digest_cases.json`
  - Replace generic metric expectations with digest `faithfulness + coverage` and add one more digest case if needed.

## Implementation Tasks

### Task 1: Lock the new eval contract in failing tests

**Files:**
- Modify: `backend/tests/test_eval_runner.py`

- [ ] **Step 1: Write the failing tests**

Add targeted assertions that:

- mixed ask/governance/digest runs still report ask four-dimension metrics
- governance cases expose `rationale_faithfulness` and `patch_safety`
- digest cases expose `faithfulness` and `coverage`
- metric overview only aggregates metric keys that are actually present

- [ ] **Step 2: Run the targeted tests and verify they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.worktrees/task-054-ingest-digest-eval/backend && \
  /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python -m unittest \
    tests.test_eval_runner.EvalRunnerTests.test_run_eval_reports_metric_overview_for_hybrid_and_governance_cases \
    -v
```

Expected: fail because `eval/run_eval.py` and the golden suites still emit ask-style governance/digest metric keys.

### Task 2: Update the golden suites to the new scenario-specific metric names

**Files:**
- Modify: `eval/golden/governance_cases.json`
- Modify: `eval/golden/digest_cases.json`

- [ ] **Step 1: Rewrite the expected metric payloads**

Update governance cases to expect:

- `rationale_faithfulness`
- `patch_safety`

Update digest metric-bearing cases to expect:

- `faithfulness`
- `coverage`

- [ ] **Step 2: Bring coverage up to the task minimum**

Ensure ingest and digest each have at least three golden cases that exercise
success, deviation, and conservative fallback/proposal paths.

### Task 3: Implement scenario-specific quality metric builders

**Files:**
- Modify: `eval/run_eval.py`

- [ ] **Step 1: Keep the failing tests focused on metric construction**

Re-run the targeted eval-runner test so the remaining failures point at
`build_quality_metrics_snapshot()` and overview aggregation.

- [ ] **Step 2: Write the minimal implementation**

Add:

- a scenario dispatcher for quality metric snapshots
- governance metric helpers for `rationale_faithfulness` and `patch_safety`
- digest metric helpers for `faithfulness` and `coverage`
- ask path preserved as-is behind a dedicated helper

- [ ] **Step 3: Update metric overview aggregation**

Only aggregate metric keys present in the selected cases instead of assuming
every scenario emits ask metrics.

- [ ] **Step 4: Re-run the targeted eval-runner test and verify it passes**

### Task 4: Verify the broader TASK-054 slice

**Files:**
- No new files

- [ ] **Step 1: Run the focused eval-runner suite**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.worktrees/task-054-ingest-digest-eval/backend && \
  /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python -m unittest \
    tests.test_eval_runner \
    -v
```

- [ ] **Step 2: Run the exact governance/digest eval cases used by the new contract**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.worktrees/task-054-ingest-digest-eval && \
  /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python eval/run_eval.py \
    --case-id governance_fixture_waiting_proposal_hybrid \
    --case-id governance_fixture_no_proposal_fallback \
    --case-id digest_fixture_structured_result_metrics \
    --case-id digest_fixture_waiting_proposal_metrics
```

- [ ] **Step 3: If a new governance or digest case is added, run that case directly too**

Keep verification narrow and evidence-driven; do not jump to full backend or plugin runs unless this slice changes shared contracts outside offline eval.
