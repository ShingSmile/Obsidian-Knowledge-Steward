# TASK-048 Runtime Faithfulness Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the existing ask groundedness heuristic into a shared quality module and use it to conservatively downgrade unsupported generated answers at runtime.

**Architecture:** Move ask-faithfulness evaluation out of `eval/run_eval.py` into a small shared `backend/app/quality/faithfulness.py` module. Reuse that evaluator from both runtime ask generation and offline eval so they speak the same bucket/reason language without changing the external ask result contract.

**Tech Stack:** Python 3.12, Pydantic, FastAPI backend services, LangGraph ask graph, `unittest`.

---

## File Structure

### Create

- `backend/app/quality/__init__.py`
  - Shared quality helpers package marker.
- `backend/app/quality/faithfulness.py`
  - Shared ask-faithfulness evaluator and lightweight term extraction helpers.

### Modify

- `backend/app/guardrails/ask.py`
  - Add a runtime helper that converts the shared faithfulness snapshot into a
    guardrail downgrade when bucket is `unsupported_claim`.
- `backend/app/services/ask.py`
  - Call the shared evaluator after citation validation and before returning a
    generated answer.
- `eval/run_eval.py`
  - Replace inline groundedness logic with calls to the shared evaluator.
- `backend/tests/test_ask_guardrails.py`
  - Lock the runtime downgrade contract.
- `backend/tests/test_ask_workflow.py`
  - Lock end-to-end ask behavior for grounded and unsupported generated answers.
- `backend/tests/test_eval_runner.py`
  - Preserve existing offline overclaim behavior after the refactor.

### No Changes Expected

- `backend/app/graphs/ask_graph.py`
  - Runtime gate should fit inside existing ask generation/fallback flow.
- plugin files
  - This slice is backend-only.

## Implementation Tasks

### Task 1: Lock the runtime gate behavior in failing tests

**Files:**
- Modify: `backend/tests/test_ask_guardrails.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write the failing guardrail and workflow tests**

Add tests for:

- unsupported generated answer with valid citations downgrades to `retrieval_only`
- grounded generated answer still returns `generated_answer`

- [ ] **Step 2: Run the targeted tests and verify they fail for the expected reason**

Run:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_guardrails \
  tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_downgrades_semantic_overclaim_answer \
  tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_keeps_grounded_generated_answer \
  -v
```

Expected: fail because runtime does not yet downgrade unsupported generated answers.

### Task 2: Extract the shared faithfulness evaluator

**Files:**
- Create: `backend/app/quality/__init__.py`
- Create: `backend/app/quality/faithfulness.py`

- [ ] **Step 1: Write the failing shared-evaluator test**

Add a focused test in `backend/tests/test_ask_guardrails.py` or a nearby backend
test module that asserts the evaluator returns `unsupported_claim` for legal
citations with unsupported terms.

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_guardrails -v
```

Expected: fail because the shared evaluator module does not exist yet.

- [ ] **Step 3: Implement the minimal shared evaluator**

Move the current ask groundedness logic out of `eval/run_eval.py` into
`backend/app/quality/faithfulness.py`. Keep the existing bucket names and result
shape stable.

- [ ] **Step 4: Re-run the focused tests and verify they pass**

### Task 3: Wire runtime ask to the shared evaluator

**Files:**
- Modify: `backend/app/guardrails/ask.py`
- Modify: `backend/app/services/ask.py`

- [ ] **Step 1: Keep the workflow tests failing only on missing runtime wiring**

After Task 2, re-run the targeted ask workflow tests so failures point at missing
runtime integration, not missing helper code.

- [ ] **Step 2: Implement the runtime downgrade**

After citation validation and before returning `AskWorkflowResult(mode=generated_answer)`,
evaluate the generated answer. If the bucket is `unsupported_claim`, return the
existing retrieval-only fallback path with a guardrail action that clearly signals a
semantic overclaim downgrade.

- [ ] **Step 3: Re-run the targeted runtime tests and verify they pass**

### Task 4: Make offline eval reuse the shared evaluator

**Files:**
- Modify: `eval/run_eval.py`
- Modify: `backend/tests/test_eval_runner.py`

- [ ] **Step 1: Refactor `run_eval.py` to import the shared evaluator**

Replace the inline `build_ask_groundedness_snapshot()` helpers with the shared
module while preserving the existing snapshot schema used by eval results.

- [ ] **Step 2: Run the targeted eval regression tests**

Run:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_eval_runner.EvalRunnerTests.test_run_eval_flags_semantic_overclaim_cases \
  -v
```

Expected: pass with existing `unsupported_claim` buckets preserved.

### Task 5: Run final verification

**Files:**
- No new files

- [ ] **Step 1: Run the full targeted backend verification set**

Run:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_guardrails \
  tests.test_ask_workflow \
  tests.test_eval_runner \
  -v
```

- [ ] **Step 2: Run the focused eval CLI regression**

Run:

```bash
../.conda/knowledge-steward/bin/python eval/run_eval.py \
  --case-id ask_fixture_semantic_overclaim_writeback \
  --case-id ask_fixture_semantic_overclaim_governance \
  --case-id ask_fixture_generated_answer_citation_valid \
  --output /tmp/task048-runtime-faithfulness-gate.json
```

Expected: the two overclaim cases remain `unsupported_claim`; the grounded case
stays `grounded`.
