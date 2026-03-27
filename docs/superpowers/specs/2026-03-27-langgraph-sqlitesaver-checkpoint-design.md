# LangGraph SqliteSaver Checkpoint Migration Design

- Status: approved in conversation
- Date: 2026-03-27
- Scope: design only, no implementation
- Target repo: `Obsidian Knowledge Steward`
- Governed task: `TASK-044`
- Planned session: `SES-20260327-01`

## 1. Background

The current graph runtime already uses LangGraph-shaped `StateGraph` definitions, but actual execution and persistence are still handled by the repository's own linear checkpoint runner:

- `backend/app/graphs/runtime.py` uses `invoke_checkpointed_linear_graph()`
- `backend/app/graphs/checkpoint.py` serializes selected `StewardState` fields into `workflow_checkpoint.state_json`
- ask / ingest / digest all persist and resume through repo-local `load_graph_checkpoint()` and `save_graph_checkpoint()`
- ingest / digest approval branches manually write waiting checkpoints into the same table

This works for the current linear workflows, but it leaves a visible architecture gap:

- the project claims LangGraph as the workflow backbone
- the real checkpoint persistence is still a custom SQLite layer
- the runtime still carries compatibility shims and `used_langgraph` bookkeeping

`TASK-044` closes that gap without discarding the business safeguards the repo already depends on.

## 2. Problem Statement

Today the repo mixes two concerns inside the checkpoint layer:

1. framework-level graph state persistence
2. product-level business control state

That coupling causes three concrete problems:

- graph execution is not actually driven by `graph.compile(checkpointer=...)`
- persistence semantics are harder to explain in LangGraph terms because they are mostly custom
- future evolution of approval / waiting / resume flows stays tied to a repo-specific runner instead of LangGraph's checkpoint model

At the same time, the current custom layer contains business behavior that cannot be dropped:

- `resume_match_fields` validation
- completed-checkpoint idempotent short-circuiting
- `checkpoint_status` business state transitions
- hydration rules that keep current-run `run_id` / `trace_events` separate from restored state
- parallel business metadata in `workflow_checkpoint`

The migration therefore must replace framework persistence, not delete business control semantics.

## 3. Goals

### 3.1 Functional goals

- Execute ask / ingest / digest through compiled LangGraph graphs with `SqliteSaver`.
- Remove the custom linear checkpoint runner from the main execution path.
- Keep `workflow_checkpoint` as a business metadata table rather than the source of truth for full graph state.
- Preserve safe resume behavior:
  - action-type consistency
  - `resume_match_fields` validation
  - completed-checkpoint short-circuit
  - business `checkpoint_status` transitions
  - current-run field override during hydrate
- Keep existing external workflow invoke / resume contracts stable.

### 3.2 Narrative goals

- Make the repo's "LangGraph-based workflow system" claim fully literal.
- Improve interview defensibility around checkpointing and recovery:
  - why LangGraph saver is used
  - why business metadata remains separate
  - where framework persistence ends and product control begins

## 4. Non-Goals

This design explicitly does not do the following:

- no `add_conditional_edges`
- no `interrupt_before` rewrite for ingest or digest approval
- no migration of `workflow_checkpoint` audit metadata into LangGraph internal tables
- no change to outer `WorkflowInvokeRequest` / `WorkflowInvokeResponse`
- no plugin-side resume UX redesign
- no cleanup / query CLI for old checkpoint rows unless required for migration correctness

## 5. Design Summary

The migration splits checkpoint responsibilities into two layers.

### 5.1 Framework persistence layer

LangGraph `SqliteSaver` becomes the canonical persistence mechanism for workflow state snapshots.

Responsibilities:

- store graph state after node execution
- restore graph state by `thread_id`
- let compiled graphs invoke through official LangGraph execution flow

Non-responsibilities:

- product-specific approval state
- resume-scope validation
- stale-request rejection
- repo-specific interview-facing metadata

### 5.2 Business checkpoint layer

`workflow_checkpoint` remains as a product control table.

Responsibilities:

- track `checkpoint_status`
- track `last_completed_node` and `next_node_name`
- track business-facing run metadata
- validate whether a resume request is allowed
- decide whether a completed checkpoint can short-circuit safely
- annotate waiting / completed / failed states for approval and rollback control planes

Non-responsibilities:

- store the full serialized graph state payload
- act as the only recovery source

## 6. File Responsibilities

### 6.1 `backend/app/graphs/runtime.py`

Current role:

- shared runtime helpers
- custom linear checkpoint runner
- LangGraph availability shim

Target role:

- shared graph compilation helpers
- shared runtime trace hook composition
- shared invoke wrapper around compiled LangGraph graphs
- zero fallback runner logic

Expected removals:

- `LANGGRAPH_AVAILABLE`
- `_CompiledStateGraph`
- compatibility `StateGraph.compile()` shim behavior
- `invoke_checkpointed_linear_graph()`
- `used_langgraph` execution field

### 6.2 `backend/app/graphs/checkpoint.py`

Current role:

- serialize / deserialize selected `StewardState`
- save and load full graph state from `workflow_checkpoint`

Target role:

- business checkpoint metadata model
- resume validation helpers
- completed-checkpoint short-circuit guard
- current-run hydrate overlay helpers
- business metadata read/write helpers for `workflow_checkpoint`

Expected contraction:

- full-state persistence moves out to `SqliteSaver`
- `workflow_checkpoint.state_json` is no longer the canonical saved state path

### 6.3 `backend/app/graphs/ask_graph.py`

Target change:

- compile graph with `SqliteSaver`
- invoke through LangGraph with `config={"configurable": {"thread_id": ...}}`
- keep ask-specific business result extraction and final execution envelope unchanged

### 6.4 `backend/app/graphs/ingest_graph.py`

Target change:

- normal linear execution path moves to compiled LangGraph + saver
- approval path may still need explicit business metadata writes, but framework state persistence should be saver-backed
- note-scope matching remains business-layer validation

### 6.5 `backend/app/graphs/digest_graph.py`

Target change:

- same migration pattern as ingest:
  - compiled graph execution on normal path
  - approval-specific business metadata preserved

### 6.6 `backend/app/indexing/store.py`

Target change:

- schema remains responsible for `workflow_checkpoint`
- may require small schema evolution if `state_json` becomes optional, deprecated, or repurposed
- must coexist safely with LangGraph saver tables in the same SQLite database

## 7. Proposed Execution Model

### 7.1 Normal invoke path

New high-level flow:

`request`
-> `build initial state`
-> `load business checkpoint metadata`
-> `validate resume intent`
-> `compile graph with SqliteSaver`
-> `invoke graph with thread_id config`
-> `after each node, LangGraph persists state`
-> `business metadata updated in workflow_checkpoint`
-> `final result extraction`

### 7.2 Resume path

Resume uses two data sources with distinct responsibilities:

- `SqliteSaver`: source of framework state
- `workflow_checkpoint`: source of business permission and control metadata

Resume flow:

1. Check whether business metadata exists for `thread_id + graph_name`.
2. Validate action type and any `resume_match_fields`.
3. If business state is `COMPLETED` and required terminal fields are already available, short-circuit without replaying side effects.
4. Otherwise invoke compiled graph with the same `thread_id`, letting LangGraph restore the latest persisted state.
5. Hydrate current-run fields on top of restored state:
   - current `run_id`
   - empty fresh `trace_events`
   - fresh transient prompt context

### 7.3 Approval / waiting path

Approval flows are intentionally not redesigned into interrupt-first LangGraph flows in this task.

Instead:

- ingest / digest may still explicitly transition business metadata to `WAITING_FOR_APPROVAL`
- LangGraph saver still persists the graph state reached before waiting
- `workflow_checkpoint` continues to record proposal-facing control metadata
- later tasks can decide whether to convert this path to `interrupt_before`

## 8. State and Data Model Decisions

### 8.1 `workflow_checkpoint`

This table remains because LangGraph saver tables do not replace the repo's business control-plane needs.

The table should continue to represent:

- `thread_id`
- `graph_name`
- `action_type`
- `last_run_id`
- `checkpoint_status`
- `last_completed_node`
- `next_node_name`
- timestamps

The state payload field should no longer be treated as the primary recovery source.

Allowed outcomes:

- keep `state_json` temporarily for backward compatibility
- repurpose it for minimal business payload
- make it nullable if migration is safe

The design does not require dropping the column immediately.

### 8.2 LangGraph saver tables

LangGraph-managed SQLite tables become the canonical persisted state source.

They should be allowed to coexist in the same DB file as:

- `note`
- `chunk`
- `chunk_fts`
- `chunk_embedding`
- `run_trace`
- `workflow_checkpoint`
- `proposal`
- `audit_log`

### 8.3 Hydration contract

The migration preserves the current contract that recovery restores business state but not execution identity.

When state is resumed:

- `thread_id` stays the same
- `run_id` is replaced with the current run's ID
- `trace_events` starts fresh
- transient prompt context is rebuilt

This avoids blending historical trace data with the current execution attempt.

## 9. Testing Strategy

The implementation should be driven by tests in this order.

### 9.1 Runtime and persistence tests

- compiled graph uses `SqliteSaver`
- saver-backed invoke persists state for a thread
- resume invoke restores state for the same thread
- completed business checkpoint still short-circuits safely

### 9.2 Business metadata tests

- `resume_match_fields` mismatch rejects or safely falls back without replaying stale scope
- `checkpoint_status` transitions still write correct business metadata
- waiting approval paths still record `WAITING_FOR_APPROVAL`
- failed node execution still records `FAILED`

### 9.3 Workflow regression tests

- ask workflow still returns the same result envelope
- ingest workflow still supports note-scope matching and waiting proposal behavior
- digest workflow still supports waiting proposal behavior
- resume / rollback tests still observe expected checkpoint side effects

### 9.4 Migration safety tests

- old self-managed helper paths are gone from runtime execution
- `LANGGRAPH_AVAILABLE`, `_CompiledStateGraph`, and `used_langgraph` are removed
- DB initialization and tests tolerate coexistence of business and LangGraph tables

## 10. Risks and Mitigations

### 10.1 Risk: business metadata drifts from saver state

Mitigation:

- keep metadata writes centralized in `checkpoint.py`
- update business checkpoint state at explicit lifecycle points only
- test completed / waiting / failed transitions directly

### 10.2 Risk: completed short-circuit no longer protects side-effect nodes

Mitigation:

- preserve explicit completed-checkpoint guard before replay
- require terminal fields to exist before returning cached completion

### 10.3 Risk: approval flows accidentally expand into interrupt refactor

Mitigation:

- keep current approval control model
- treat interrupt migration as a later derived task only

### 10.4 Risk: migration leaves dead compatibility code

Mitigation:

- explicitly remove fallback runner and `used_langgraph` plumbing
- add tests that exercise only the real compiled-graph path

## 11. Open Questions

These are implementation questions, not design blockers:

- whether `state_json` should remain populated for a transition period or be deprecated immediately
- whether LangGraph saver should be wrapped in a tiny local factory helper or created directly in runtime
- whether ingest / digest approval helpers should write business metadata before or after saver-backed graph invocation finalizes

None of these change the main design choice.

## 12. Recommended Approach

Use a dual-layer checkpoint model:

- LangGraph `SqliteSaver` for actual graph state persistence
- `workflow_checkpoint` for business metadata and resume policy

Do not keep the current linear checkpoint runner.
Do not expand this task into interrupt refactors.
Do not change outer API contracts.

That gives the repo the smallest architecture change that still makes `TASK-044` true in both code and interview narrative.
