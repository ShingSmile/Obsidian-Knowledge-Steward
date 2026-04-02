# TASK-052 Runtime Semantic Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse the shared claim-level semantic faithfulness core at runtime so ask and digest emit aligned quality outcomes with structured score and threshold metadata.

**Architecture:** Add one shared runtime semantic gate in `backend/app/quality/faithfulness.py`, then wire ask and digest to consume it. Ask keeps its existing external behavior by downgrading unsafe generated answers to `retrieval_only`, while digest gains structured low-confidence metadata and trace fields without changing its basic execution flow.

**Tech Stack:** Python 3.12, Pydantic, FastAPI backend services, LangGraph digest/ask graphs, `unittest`.

---

## File Structure

### Modify

- `backend/app/quality/faithfulness.py`
  - Add a shared runtime semantic gate wrapper around the claim-level report.
- `backend/app/guardrails/ask.py`
  - Convert runtime semantic gate results into ask guardrail outcomes.
- `backend/app/services/ask.py`
  - Replace the older heuristic runtime faithfulness check with the shared semantic gate.
- `backend/app/services/digest.py`
  - Evaluate digest markdown against assembled evidence and attach structured runtime quality metadata.
- `backend/app/contracts/workflow.py`
  - Add structured digest runtime quality models/fields.
- `backend/app/graphs/digest_graph.py`
  - Write digest runtime quality details into trace metadata.
- `backend/tests/test_faithfulness.py`
  - Lock the shared runtime semantic gate behavior.
- `backend/tests/test_ask_workflow.py`
  - Lock ask downgrade / non-downgrade runtime behavior.
- `backend/tests/test_digest_workflow.py`
  - Lock digest low-confidence outcome and trace metadata.

## Implementation Tasks

### Task 1: Lock the shared runtime gate behavior in failing tests

**Files:**
- Modify: `backend/tests/test_faithfulness.py`

- [ ] **Step 1: Write the failing test**

Add focused tests for:

- semantic runtime gate returns a downgrade outcome for unsupported claims
- semantic runtime gate returns allow for fully supported claims

- [ ] **Step 2: Run the targeted test and verify it fails**

Run:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_faithfulness.FaithfulnessTests \
  -v
```

Expected: fail because the runtime semantic gate helper does not exist yet.

### Task 2: Lock ask and digest runtime behavior in failing tests

**Files:**
- Modify: `backend/tests/test_ask_workflow.py`
- Modify: `backend/tests/test_digest_workflow.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:

- ask unsupported generated answer downgrades through the shared semantic gate
- ask grounded generated answer stays generated
- digest returns low-confidence quality metadata for unsupported markdown
- digest trace includes runtime quality score / threshold / outcome

- [ ] **Step 2: Run the targeted tests and verify they fail**

Run:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_downgrades_semantic_overclaim_answer \
  tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_keeps_grounded_generated_answer \
  tests.test_digest_workflow.DigestWorkflowTests \
  -v
```

Expected: fail because digest has no structured runtime quality outcome yet.

### Task 3: Implement the shared runtime semantic gate

**Files:**
- Modify: `backend/app/quality/faithfulness.py`

- [ ] **Step 1: Write the minimal implementation**

Add a shared helper that reduces the existing claim-level report to runtime fields:
`outcome`, `score`, `threshold`, `backend`, `reason`, `claim_count`, and
`unsupported_claim_count`.

- [ ] **Step 2: Run the focused helper tests and verify they pass**

### Task 4: Wire ask and digest to the shared runtime gate

**Files:**
- Modify: `backend/app/guardrails/ask.py`
- Modify: `backend/app/services/ask.py`
- Modify: `backend/app/services/digest.py`
- Modify: `backend/app/contracts/workflow.py`
- Modify: `backend/app/graphs/digest_graph.py`

- [ ] **Step 1: Keep tests failing only on missing wiring**

Re-run the targeted ask/digest tests so failures point to integration gaps.

- [ ] **Step 2: Implement minimal runtime wiring**

- ask consumes the shared runtime gate and downgrades to `retrieval_only` when the
  semantic outcome says so
- digest attaches structured runtime quality metadata and trace details

- [ ] **Step 3: Re-run the targeted ask/digest tests and verify they pass**

### Task 5: Run final verification

**Files:**
- No new files

- [ ] **Step 1: Run the focused backend verification set**

Run:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_faithfulness \
  tests.test_ask_workflow \
  tests.test_digest_workflow \
  -v
```

- [ ] **Step 2: If needed, run targeted eval or graph regressions affected by the contract change**

Run only the smallest commands needed to verify no ask/digest regression remains.
