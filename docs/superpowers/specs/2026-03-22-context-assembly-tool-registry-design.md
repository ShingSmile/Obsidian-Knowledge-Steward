# Context Assembly And Tool Registry Design

- Status: approved in conversation
- Date: 2026-03-22
- Scope: design only, no implementation
- Target repo: `Obsidian Knowledge Steward`

## 1. Background

The current project is already strong on workflow orchestration and control-plane engineering:

- explicit `ASK_QA`, `INGEST_STEWARD`, `DAILY_DIGEST` workflows
- `thread_id + checkpoint + resume`
- approval gating and local writeback
- append-only audit and rollback accounting
- offline eval and runtime tracing

For interview positioning, the main gap is not core engineering rigor. The gap is that the project does not yet expose two mainstream LLM application layers as first-class design elements:

1. explicit context assembly
2. explicit, bounded tool calling

This design adds those layers without changing the project's workflow-first architecture.

## 2. Problem Statement

Today, the repo can already retrieve evidence and run workflow steps, but the following capabilities are not explicit enough:

- how retrieved evidence is selected, compressed, budgeted, and rendered for the model
- what tools the model is allowed to use
- how tool outputs are reintroduced into context
- where runtime guardrails decide whether a model output can be released

Without these layers, the project is still defensible as a workflow-first agent application, but it is weaker in interview conversations around:

- context engineering
- tool calling
- runtime guardrails
- prompt injection and evidence-bound answer control

## 3. Goals

This design has two primary goals.

### 3.1 Functional goals

- Add a shared context assembly layer before model generation.
- Add a lightweight tool registry with strictly bounded read-only tools.
- Add explicit runtime guardrail outcomes before returning final answers.
- Reuse the context assembly layer across `ASK_QA`, `INGEST_STEWARD`, and `DAILY_DIGEST`.

### 3.2 Interview goals

- Upgrade the project narrative from "workflow + approval + checkpoint" to:
  - workflow orchestration
  - context assembly
  - bounded tool calling
  - runtime guardrails
- Preserve the current "safe governance system" story rather than replacing it with an open-ended ReAct story.

## 4. Non-Goals

This design explicitly does not do the following:

- no MCP layer
- no multi-agent or supervisor architecture
- no generic memory framework
- no open-ended ReAct loop
- no direct model access to write-capable tools
- no rewrite of the current ask / ingest / digest control flow

## 5. Proposed Architecture

Three new backend modules are introduced.

### 5.1 `backend/app/context/`

Purpose:

- transform retrieval outputs, proposal evidence, and tool outputs into a structured model-ready context bundle

Responsibilities:

- evidence selection
- deduplication
- token budgeting
- source attribution
- conflict and ambiguity annotation
- suspicious-context downranking or filtering

Non-responsibilities:

- workflow routing
- tool execution
- final writeback control

### 5.2 `backend/app/tools/`

Purpose:

- expose a small, explicit registry of allowed tools

Responsibilities:

- tool declaration
- workflow-level permission checks
- schema validation
- execution wrapper
- normalized execution result objects

Non-responsibilities:

- arbitrary function discovery
- write-capable local side effects
- open-ended agent loops

### 5.3 `backend/app/guardrails/`

Purpose:

- make model release decisions explicit and testable

Responsibilities:

- enforce token-budget fallback
- reject invalid tool requests
- downgrade on insufficient evidence
- gate strong claims when evidence is weak
- handle suspicious prompt injection content conservatively

Non-responsibilities:

- complex external judging
- full policy engine platformization
- replacing existing citation and groundedness checks

## 6. Integration Strategy

### 6.1 `ASK_QA`

`ASK_QA` is the first and only workflow that receives explicit tool calling in phase 1.

Reason:

- it is the lowest-risk path
- it is already retrieval-centric
- it benefits most from context refinement and controlled evidence expansion
- it avoids introducing free-form tool choice into high-risk governance flows

### 6.2 `INGEST_STEWARD`

`INGEST_STEWARD` only adopts shared context assembly in the first version.

Reason:

- its main value is evidence organization and proposal quality
- it already contains high-risk proposal and approval semantics
- allowing free tool choice here would expand risk and complexity too early

### 6.3 `DAILY_DIGEST`

`DAILY_DIGEST` also adopts shared context assembly only.

Reason:

- digest quality depends more on source-note organization and token budgeting than on tool freedom
- this keeps the workflow deterministic and easier to validate

### 6.4 Likely touch points in the current repo

The design is intentionally constrained to a small set of existing files and new backend folders.

Primary integration points:

- `backend/app/services/ask.py`
- `backend/app/graphs/ask_graph.py`
- `backend/app/services/ingest_proposal.py`
- `backend/app/graphs/ingest_graph.py`
- `backend/app/services/digest.py`
- `backend/app/graphs/digest_graph.py`
- `backend/app/contracts/workflow.py`
- `eval/run_eval.py`

New modules:

- `backend/app/context/`
- `backend/app/tools/`
- `backend/app/guardrails/`

Expected non-goal for phase 1:

- no mandatory plugin UI redesign
- no change to approval, rollback, or writeback control-plane contracts unless a new guardrail reason needs to be surfaced in existing response fields

## 7. Data Flow

### 7.1 New `ASK_QA` data flow

The current high-level flow:

`query -> retrieval -> answer generation`

The proposed flow:

`query`
-> `retrieval`
-> `context assembly`
-> `tool selection`
-> `tool execution (optional)`
-> `re-assembly`
-> `model generation`
-> `guardrail check`
-> `response`

Key idea:

- the model does not immediately generate the final answer after retrieval
- it first receives a structured context plus a bounded tool surface
- if a tool is requested, the tool result becomes additional evidence, not automatic truth

### 7.2 `INGEST_STEWARD` and `DAILY_DIGEST`

Their first-stage flow becomes:

- retrieval or source collection
- context assembly
- model or proposal generation
- existing workflow logic continues unchanged

No free-form tool calling is introduced for these workflows in the first version.

## 8. Core Contracts

### 8.1 `ContextBundle`

`ContextBundle` is the normalized output of the context assembly layer.

Required fields:

- `user_intent`
- `workflow_action`
- `evidence_items`
- `tool_results`
- `token_budget`
- `safety_flags`
- `assembly_notes`

Why it exists:

- keeps model input explainable
- separates evidence organization from prompt rendering
- makes context tests deterministic

### 8.2 `ToolSpec`

Each registered tool must declare:

- `name`
- `purpose`
- `allowed_workflows`
- `input_schema`
- `output_schema`
- `risk_level`
- `read_only`

Phase 1 tool set:

- `search_notes`
- `load_note_excerpt`
- `list_pending_approvals`

Constraints:

- all tools are read-only
- no direct write tool may be exposed to the model

### 8.3 `ToolCallDecision`

Represents whether the model is requesting a tool and why.

Required fields:

- `requested`
- `tool_name`
- `tool_args`
- `reason`

Why it exists:

- separates decision quality from execution quality
- keeps tool request validation explicit

### 8.4 `ToolExecutionResult`

Represents what actually happened when a tool was executed.

Required fields:

- `success`
- `tool_name`
- `result`
- `error`
- `allowed_to_reenter_context`

Why it exists:

- tool failures must not silently contaminate the answer path
- execution is observable independently from model planning

### 8.5 `GuardrailOutcome`

Represents final release semantics for model output.

Allowed outcomes:

- `allow`
- `downgrade_to_retrieval_only`
- `refuse_strong_claim`
- `tool_result_insufficient`
- `possible_injection_detected`

Why it exists:

- turns guardrails into an explicit control layer instead of scattered conditionals

## 9. Error Handling And Degradation

The governing principle is:

New layers may make the system more conservative, but must not make the system more fragile.

### 9.1 Context assembly failure

- do not hard-fail the whole ask path by default
- fall back to the current minimal retrieval-first answer path or retrieval-only path

### 9.2 Invalid tool request

- reject the tool request
- do not execute any fallback "best guess" tool
- continue with a no-tool answer path if possible

### 9.3 Tool execution failure

- record a failed `ToolExecutionResult`
- do not treat the failed tool output as evidence
- downgrade to a conservative answer or retrieval-only response

### 9.4 Guardrail hit

- do not release a strong answer
- downgrade to retrieval-only or an explicit insufficiency response

### 9.5 Governance workflows

- `INGEST_STEWARD` and `DAILY_DIGEST` continue to prioritize deterministic, controlled proposal generation
- phase 1 must not weaken existing approval and writeback boundaries

## 10. Security And Safety Boundaries

Three hard constraints apply.

### 10.1 Tools are read-only

No model-facing tool may directly modify the Vault.

### 10.2 Tool output is evidence, not truth

Tool outputs must re-enter the context assembly and guardrail path before they can influence final answers.

### 10.3 High-risk workflows stay controlled

`INGEST_STEWARD` and `DAILY_DIGEST` do not get free-form tool selection in phase 1.

## 11. Testing Strategy

Testing is split into three layers.

### 11.1 Unit tests

- `ContextBundle` assembly
- token-budget truncation
- evidence ordering and deduplication
- tool registry permission checks
- invalid tool request rejection
- guardrail outcomes

### 11.2 Integration tests

`ASK_QA` should cover:

- direct answer without tool call
- valid tool request and successful execution
- invalid tool request rejected safely
- tool timeout or error with conservative downgrade
- guardrail-driven downgrade to `retrieval_only`

`INGEST_STEWARD` and `DAILY_DIGEST` should cover:

- shared context assembly does not break current proposal or digest paths
- approval and writeback boundaries remain unchanged

### 11.3 Offline eval

Extend `eval/run_eval.py` with cases for:

- retrieval insufficient, excerpt tool required
- model selects the wrong tool
- tool result exists but remains insufficient for a strong claim
- suspicious injected content appears in evidence

## 12. Rollout Plan

### Phase 1: Context Assembly

- introduce `ContextBundle`
- integrate into `ASK_QA`
- reuse in `INGEST_STEWARD` and `DAILY_DIGEST`

Acceptance criteria:

- model input is no longer implicitly assembled inside workflow-specific logic
- context assembly is observable and testable

### Phase 2: Tool Registry

- introduce lightweight read-only tool registry
- enable tool calling only for `ASK_QA`

Acceptance criteria:

- at least 2 to 3 tools are explicitly registered
- invalid tool requests are safely rejected

### Phase 3: Guardrail Outcomes

- introduce `GuardrailOutcome`
- explicitly gate final ask answers

Acceptance criteria:

- weak-evidence answers downgrade deterministically
- tool errors do not leak as false certainty

## 13. Trade-Offs

Benefits:

- improves interview narrative with minimal architectural churn
- adds mainstream LLM application concepts without abandoning workflow control
- keeps high-risk governance flows conservative
- makes context engineering and tool use explicit and testable

Costs:

- introduces more contracts and intermediate objects
- adds some prompt and orchestration complexity to `ASK_QA`
- requires careful test coverage to avoid accidental regressions

Deliberate limitations:

- not a general-purpose agent framework
- not a multi-agent system
- not an MCP showcase
- not a generic memory architecture

## 14. Why This Design Instead Of Hotter Alternatives

### Why not MCP first

MCP would improve ecosystem story, but it is mostly a compatibility layer. It does not strengthen the core knowledge-governance path as directly as context assembly and bounded tool use.

### Why not memory first

The repo already has strong state and recovery semantics via workflow state and checkpoints. Adding generic memory first would risk creating a buzzword layer without enough new product value.

### Why this design is the best fit

This design keeps the current project identity intact:

- workflow-first
- governance-centric
- high-risk writeback remains controlled
- model capabilities become more explicit, but not more dangerous

## 15. Final Positioning

After this design is implemented, the preferred interview framing becomes:

`Obsidian Knowledge Steward` is a workflow-first knowledge-governance agent system. Its global control flow remains explicitly orchestrated by LangGraph, while model-facing capabilities are strengthened through structured context assembly, bounded read-only tool calling, and explicit runtime guardrails.
