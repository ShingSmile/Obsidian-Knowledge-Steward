# TASK-046 Ask Graph ReAct Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor ask into a graph-only ReAct workflow where LangGraph owns the loop, checkpoint boundaries, and trace visibility, while service-layer code is reduced to node-scoped helper functions.

**Architecture:** Remove `run_minimal_ask()` as the complete ask execution path and promote `invoke_ask_graph()` to the single workflow entrypoint. Split ask business logic into retrieval, tool-decision, tool-execution, context reassembly, and final-answer helpers, then wire those helpers into a conditional-edge graph with explicit per-round state, loop limits, and final result assembly.

**Tech Stack:** Python 3.12, LangGraph `StateGraph`, Pydantic, SQLite `SqliteSaver`, FastAPI workflow wrapper, `unittest`.

---

## File Structure

Keep the change inside the existing ask boundary. Do not widen the API surface beyond the already-planned `AskWorkflowResult.tool_call_rounds` field, and do not touch ingest/digest workflow semantics.

### Modify

- `backend/app/contracts/workflow.py`
  - Add `tool_call_rounds` to `AskWorkflowResult`.
- `backend/app/graphs/state.py`
  - Extend `StewardState` with explicit ask-loop state fields used by graph nodes.
- `backend/app/services/ask.py`
  - Remove `run_minimal_ask()` as the main workflow path and replace it with focused helper functions for graph nodes.
- `backend/app/graphs/ask_graph.py`
  - Replace the linear three-node ask graph with a conditional-edge ReAct loop and a graph-native finalization path.
- `backend/tests/test_ask_workflow.py`
  - Migrate direct `run_minimal_ask()` coverage to helper-level and graph-level tests; add loop, round-count, trace, and resume assertions.

### No Changes Expected

- `backend/app/main.py`
  - The backend should continue invoking `invoke_ask_graph()` without new route-level branching.
- `backend/app/graphs/runtime.py`
  - Shared runtime helpers should stay reusable without ask-specific branching.
- plugin files
  - `TASK-046` is backend-only.

### Skills To Use During Execution

- `@test-driven-development` before each production edit.
- `@verification-before-completion` before any success claim or commit.
- `@requesting-code-review` after implementation and verification stabilize.

## Implementation Tasks

### Task 1: Lock the new graph contract in tests

**Files:**
- Modify: `backend/tests/test_ask_workflow.py`
- Modify: `backend/app/contracts/workflow.py`
- Modify: `backend/app/graphs/state.py`

- [ ] **Step 1: Write the failing graph-level tests**

Add tests that express the new desired shape:

```python
def test_invoke_ask_graph_loops_from_llm_to_tool_to_llm_before_finalize(self) -> None:
    execution = invoke_ask_graph(...)
    self.assertEqual(
        [event["node_name"] for event in execution.trace_events],
        [
            "prepare_ask",
            "llm_call",
            "tool_node",
            "llm_call",
            "finalize_ask",
        ],
    )
    self.assertEqual(execution.ask_result.tool_call_rounds, 1)


def test_invoke_ask_graph_forces_finalize_after_max_rounds(self) -> None:
    execution = invoke_ask_graph(...)
    self.assertEqual(execution.ask_result.tool_call_rounds, 3)
    self.assertEqual(execution.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)
```

Also update the existing trace assertions that currently assume exactly three nodes.

- [ ] **Step 2: Run the targeted ask graph tests and confirm they fail for the expected reason**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_keeps_thread_id_and_emits_trace_events tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_emits_tool_and_guardrail_trace_fields -v
```

Expected: FAIL because the graph still emits `prepare_ask -> execute_ask -> finalize_ask`, and `AskWorkflowResult` has no `tool_call_rounds`.

- [ ] **Step 3: Extend the ask result and graph state contracts minimally**

Add the planned result field:

```python
class AskWorkflowResult(BaseModel):
    ...
    tool_call_rounds: int = 0
```

Add explicit ask-loop state needed by the graph:

```python
class StewardState(TypedDict, total=False):
    ...
    ask_query: str
    ask_candidates: list[dict]
    ask_bundle: dict
    ask_tool_decision: dict | None
    ask_tool_results: list[dict]
    ask_prompt_candidates: list[dict]
    ask_citations: list[dict]
    ask_tool_call_rounds: int
    ask_max_tool_rounds: int
    ask_should_finalize: bool
```

Keep fields JSON/checkpoint friendly so LangGraph can persist loop state cleanly.

- [ ] **Step 4: Re-run the targeted tests and confirm the failures now point at missing behavior, not missing contract fields**

Run:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_keeps_thread_id_and_emits_trace_events -v
```

Expected: FAIL on node sequence / behavior, not on missing attributes.

- [ ] **Step 5: Commit the contract groundwork**

```bash
git add backend/app/contracts/workflow.py backend/app/graphs/state.py backend/tests/test_ask_workflow.py
git commit -m "test: lock ask graph react loop contract"
```

### Task 2: Split ask business logic into graph-node helpers

**Files:**
- Modify: `backend/app/services/ask.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write the failing helper-level tests**

Replace direct `run_minimal_ask()` workflow tests with focused helper tests, for example:

```python
def test_build_initial_ask_turn_returns_prompt_visible_candidates_and_citations(self) -> None:
    turn = build_initial_ask_turn(...)
    self.assertEqual([candidate.chunk_id for candidate in turn.prompt_candidates], ["chunk-1"])
    self.assertEqual(len(turn.citations), 1)


def test_execute_ask_tool_turn_reassembles_context_after_verified_tool_result(self) -> None:
    next_turn = execute_ask_tool_turn(...)
    self.assertEqual(next_turn.tool_results[0].tool_name, "load_note_excerpt")
    self.assertIn("excerpt", next_turn.bundle.model_dump(mode="json"))
```

Target the business boundaries directly:
- initial retrieval + bundle assembly
- tool decision parsing / guardrail evaluation
- verified tool execution and reassembly
- grounded answer generation
- retrieval-only fallback building

- [ ] **Step 2: Run the helper-focused tests and confirm they fail because the helpers do not exist yet**

Run:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -k ask_turn -v
```

Expected: FAIL because the helper API is not implemented.

- [ ] **Step 3: Implement the minimal helper decomposition**

Restructure `backend/app/services/ask.py` into graph-consumable helpers, for example:

```python
@dataclass(frozen=True)
class AskTurnContext:
    query: str
    candidates: list[RetrievedChunkCandidate]
    bundle: ContextBundle
    prompt_candidates: list[RetrievedChunkCandidate]
    citations: list[AskCitation]
    tool_results: list[ToolExecutionResult]


def build_initial_ask_turn(...) -> AskTurnContext: ...
def decide_next_tool_call(...) -> tuple[ToolCallDecision, GuardrailOutcome]: ...
def execute_verified_tool_turn(...) -> AskTurnContext | AskWorkflowResult: ...
def generate_final_ask_result(...) -> AskWorkflowResult: ...
def build_retrieval_only_result(...) -> AskWorkflowResult: ...
```

Do not keep `run_minimal_ask()` as a complete execution path. If a compatibility wrapper remains temporarily during the refactor, remove it before the task is complete.

- [ ] **Step 4: Re-run the helper tests and confirm they pass**

Run:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -k ask_turn -v
```

Expected: PASS for the new helper-focused coverage.

- [ ] **Step 5: Commit the service decomposition**

```bash
git add backend/app/services/ask.py backend/tests/test_ask_workflow.py
git commit -m "refactor: split ask service into graph node helpers"
```

### Task 3: Rebuild ask graph as a conditional-edge ReAct loop

**Files:**
- Modify: `backend/app/graphs/ask_graph.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write the failing integration tests for loop control and finalize behavior**

Add explicit tests for:
- no-tool first turn goes directly to `finalize_ask`
- one tool turn loops back into `llm_call`
- repeated tool requests stop at max rounds
- checkpoint resume still short-circuits completed ask runs
- trace details include round counters and per-node decision metadata

Example:

```python
def test_invoke_ask_graph_directly_finalizes_when_llm_requests_no_tool(self) -> None:
    execution = invoke_ask_graph(...)
    self.assertEqual(
        [event["node_name"] for event in execution.trace_events],
        ["prepare_ask", "llm_call", "finalize_ask"],
    )
    self.assertEqual(execution.ask_result.tool_call_rounds, 0)
```

- [ ] **Step 2: Run the ask workflow suite and confirm the graph tests fail on the old linear implementation**

Run:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v
```

Expected: FAIL because the graph still uses `execute_ask` and lacks conditional edges / loop state.

- [ ] **Step 3: Implement the graph-native loop**

Refactor `backend/app/graphs/ask_graph.py` roughly to:

```python
workflow.add_node("prepare_ask", ...)
workflow.add_node("llm_call", ...)
workflow.add_node("tool_node", ...)
workflow.add_node("finalize_ask", ...)

workflow.add_edge(START, "prepare_ask")
workflow.add_edge("prepare_ask", "llm_call")
workflow.add_conditional_edges(
    "llm_call",
    _route_after_llm_call,
    {
        "tool_node": "tool_node",
        "finalize_ask": "finalize_ask",
    },
)
workflow.add_edge("tool_node", "llm_call")
workflow.add_edge("finalize_ask", END)
```

Implementation requirements:
- `prepare_ask` performs retrieval and seeds state.
- `llm_call` decides whether to call a tool or finalize, and records trace details including current round.
- `tool_node` executes one verified tool call, reassembles context, increments round count, and marks forced-finalize when the round cap is reached.
- `finalize_ask` builds `AskWorkflowResult` and stores `tool_call_rounds`.
- checkpoint persistence continues to happen between graph nodes via `SqliteSaver`.

- [ ] **Step 4: Re-run the full ask workflow suite and confirm all ask tests pass**

Run:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v
```

Expected: PASS with updated node sequences, result fields, and trace assertions.

- [ ] **Step 5: Commit the graph refactor**

```bash
git add backend/app/graphs/ask_graph.py backend/tests/test_ask_workflow.py backend/app/services/ask.py
git commit -m "feat: refactor ask into graph native react loop"
```

### Task 4: Run final verification and prepare governed-session tail sync

**Files:**
- Modify: none for implementation
- Review for tail sync only: `docs/CURRENT_STATE.md`, `docs/TASK_QUEUE.md`, `docs/SESSION_LOG.md`

- [ ] **Step 1: Run the focused verification commands**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v
```

If available and still relevant, also run:

```bash
../.conda/knowledge-steward/bin/python eval/run_eval.py --case-id ask_fixture_hybrid_retrieval_only --case-id ask_fixture_generated_answer_citation_valid --output /tmp/task046-ask-eval.json
```

- [ ] **Step 2: Inspect for scope drift and code/document mismatches**

Confirm:
- no lingering direct workflow use of `run_minimal_ask()`
- `tool_call_rounds` is populated
- trace assertions reflect graph-native node boundaries
- governed-session tail sync still notes the stale `stash@{0}` statement in `docs/CURRENT_STATE.md`

- [ ] **Step 3: If verification is green, commit the verification-only changes**

```bash
git add backend
git commit -m "test: verify ask graph react loop"
```

- [ ] **Step 4: Handoff for governed-session closeout**

Record for the later closeout decision:
- `TASK-046` status change, if achieved
- whether new derived tasks were discovered
- whether `CURRENT_STATE` and `TASK_QUEUE` need Level 2 sync
- whether any stable architecture language in `PROJECT_MASTER_PLAN` now needs Level 3 sync
