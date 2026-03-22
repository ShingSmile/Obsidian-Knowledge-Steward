# Context Assembly And Tool Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit context assembly, bounded read-only tool calling for `ASK_QA`, and shared context assembly reuse in `INGEST_STEWARD` / `DAILY_DIGEST` without changing the repo's workflow-first control flow.

**Architecture:** Introduce focused `app.context`, `app.tools`, and `app.guardrails` packages around the current retrieval-backed services. `run_minimal_ask()` becomes a two-pass path (`retrieve -> assemble -> optional tool -> re-assemble -> answer -> guardrail`), while ingest and digest adopt the same context assembly helpers for deterministic evidence ordering, token budgeting, and safety flag propagation without opening free-form tool loops.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, LangGraph state graphs, sqlite-backed retrieval, existing chat-completions provider adapter, `unittest`, existing `eval/run_eval.py`.

---

## File Structure

Follow the current backend layout: keep API-facing Pydantic models in `backend/app/contracts/workflow.py`, keep orchestration in `backend/app/services/` and `backend/app/graphs/`, and add small focused packages for the new feature.

### Create

- `backend/app/context/__init__.py`
  - Export context assembly helpers.
- `backend/app/context/assembly.py`
  - Build normalized `ContextBundle` objects for ask / ingest / digest.
- `backend/app/context/render.py`
  - Render structured bundles into model-ready prompt blocks and tool-selection prompts.
- `backend/app/context/safety.py`
  - Detect suspicious evidence text, annotate safety flags, and enforce token-budget trimming.
- `backend/app/tools/__init__.py`
  - Export tool registry helpers.
- `backend/app/tools/registry.py`
  - Define allowed read-only tools, workflow permission checks, and execution wrapper.
- `backend/app/tools/ask_tools.py`
  - Implement `search_notes`, `load_note_excerpt`, and `list_pending_approvals`.
- `backend/app/guardrails/__init__.py`
  - Export ask guardrail helpers.
- `backend/app/guardrails/ask.py`
  - Evaluate tool requests, tool results, and final answer release decisions.
- `backend/tests/test_context_assembly.py`
  - Unit coverage for context bundle building, safety flags, and prompt rendering.
- `backend/tests/test_tool_registry.py`
  - Unit coverage for tool permission checks and tool execution.
- `backend/tests/test_ask_guardrails.py`
  - Unit coverage for ask guardrail decisions.

### Modify

- `backend/app/contracts/workflow.py`
  - Add new enums / models shared across context assembly, tools, and guardrails.
- `backend/app/services/ask.py`
  - Replace the current single-pass ask path with the bounded two-pass flow.
- `backend/app/graphs/ask_graph.py`
  - Record tool / guardrail metadata in trace events and graph state.
- `backend/app/services/ingest_proposal.py`
  - Reuse context assembly when building retrieval-backed ingest evidence and review markdown.
- `backend/app/services/digest.py`
  - Reuse context assembly when building digest source-note summaries.
- `backend/tests/test_ask_workflow.py`
  - Expand integration coverage for tool calling, downgrade paths, and new ask result fields.
- `backend/tests/test_ingest_workflow.py`
  - Add regression coverage proving ingest reuses context assembly without changing approval behavior.
- `backend/tests/test_digest_workflow.py`
  - Add regression coverage proving digest reuses context assembly without changing fallback semantics.
- `backend/tests/test_eval_runner.py`
  - Validate new eval cases and benchmark metrics.
- `eval/run_eval.py`
  - Add ask cases for tool success, invalid tool request, and guardrail downgrade.

### No Changes Expected

- `plugin/`
  - No plugin UI or runtime changes in this plan.
- approval / rollback / writeback control-plane modules
  - Keep existing writeback boundaries intact; only expose extra ask metadata if needed.

### Skills To Use During Execution

- `@test-driven-development` before each code change.
- `@verification-before-completion` before claiming the feature is complete.
- `@requesting-code-review` after implementation is stable.

## Implementation Tasks

### Task 1: Add shared contracts and package scaffolding

**Files:**
- Create: `backend/app/context/__init__.py`
- Create: `backend/app/tools/__init__.py`
- Create: `backend/app/guardrails/__init__.py`
- Modify: `backend/app/contracts/workflow.py`
- Test: `backend/tests/test_context_assembly.py`
- Test: `backend/tests/test_tool_registry.py`
- Test: `backend/tests/test_ask_guardrails.py`

- [ ] **Step 1: Write the failing contract tests**

```python
class ContextContractTests(unittest.TestCase):
    def test_context_bundle_round_trips_with_tool_and_safety_metadata(self) -> None:
        bundle = ContextBundle(
            user_intent="find governance note",
            workflow_action=WorkflowAction.ASK_QA,
            evidence_items=[
                ContextEvidenceItem(
                    source_path="Alpha.md",
                    chunk_id="chunk-alpha",
                    heading_path="Alpha > Notes",
                    text="governance overview",
                    score=0.91,
                    source_kind="retrieval",
                )
            ],
            tool_results=[],
            allowed_tool_names=["search_notes"],
            token_budget=1200,
            safety_flags=["suspicious_instruction"],
            assembly_notes=["deduplicated:1"],
        )
        payload = bundle.model_dump(mode="json")
        self.assertEqual(payload["workflow_action"], "ASK_QA")
        self.assertEqual(payload["evidence_items"][0]["source_kind"], "retrieval")
        self.assertEqual(payload["safety_flags"], ["suspicious_instruction"])
```

```python
class ToolContractTests(unittest.TestCase):
    def test_tool_spec_defaults_to_read_only_and_requires_allowed_workflows(self) -> None:
        spec = ToolSpec(
            name="search_notes",
            purpose="search indexed notes",
            allowed_workflows=[WorkflowAction.ASK_QA],
            input_schema={"type": "object", "required": ["query"]},
            output_schema={"type": "object"},
            risk_level="low",
        )
        self.assertTrue(spec.read_only)
        self.assertEqual(spec.allowed_workflows, [WorkflowAction.ASK_QA])
```

- [ ] **Step 2: Run the targeted tests to confirm missing models fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly tests.test_tool_registry tests.test_ask_guardrails -v
```

Expected: FAIL with `ImportError` or `NameError` for `ContextBundle`, `ToolSpec`, or guardrail enums because the new contracts do not exist yet.

- [ ] **Step 3: Add minimal shared models and package exports**

Implement the new API-facing models in `backend/app/contracts/workflow.py` and keep them narrow:

```python
class ContextEvidenceItem(BaseModel):
    source_path: str
    chunk_id: str | None = None
    heading_path: str | None = None
    text: str
    score: float | None = None
    source_kind: Literal["retrieval", "tool", "proposal", "digest"]


class ContextBundle(BaseModel):
    user_intent: str
    workflow_action: WorkflowAction
    evidence_items: list[ContextEvidenceItem] = Field(default_factory=list)
    tool_results: list["ToolExecutionResult"] = Field(default_factory=list)
    allowed_tool_names: list[str] = Field(default_factory=list)
    token_budget: int
    safety_flags: list[str] = Field(default_factory=list)
    assembly_notes: list[str] = Field(default_factory=list)


class ToolSpec(BaseModel):
    name: str
    purpose: str
    allowed_workflows: list[WorkflowAction]
    input_schema: dict[str, object]
    output_schema: dict[str, object]
    risk_level: str
    read_only: bool = True


class ToolCallDecision(BaseModel):
    requested: bool
    tool_name: str | None = None
    arguments: dict[str, object] = Field(default_factory=dict)
    rationale: str | None = None


class ToolExecutionResult(BaseModel):
    tool_name: str
    ok: bool
    data: dict[str, object] = Field(default_factory=dict)
    error: str | None = None
    allow_context_reentry: bool = True


class GuardrailAction(str, Enum):
    ALLOW = "allow"
    DOWNGRADE_TO_RETRIEVAL_ONLY = "downgrade_to_retrieval_only"
    REFUSE_STRONG_CLAIM = "refuse_strong_claim"
    TOOL_RESULT_INSUFFICIENT = "tool_result_insufficient"
    POSSIBLE_INJECTION_DETECTED = "possible_injection_detected"


class GuardrailOutcome(BaseModel):
    action: GuardrailAction
    reasons: list[str] = Field(default_factory=list)
    applied: bool = False
```

Also export package-level symbols in the new `__init__.py` files so future imports stay short.

- [ ] **Step 4: Re-run the targeted tests and ensure the contracts pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly tests.test_tool_registry tests.test_ask_guardrails -v
```

Expected: PASS for contract-level tests, even if later behavior tests still fail.

- [ ] **Step 5: Commit the scaffolding**

```bash
git add backend/app/contracts/workflow.py backend/app/context/__init__.py backend/app/tools/__init__.py backend/app/guardrails/__init__.py backend/tests/test_context_assembly.py backend/tests/test_tool_registry.py backend/tests/test_ask_guardrails.py
git commit -m "feat: add context tool and guardrail contracts"
```

### Task 2: Implement shared context safety and ask bundle assembly

**Files:**
- Create: `backend/app/context/assembly.py`
- Create: `backend/app/context/render.py`
- Create: `backend/app/context/safety.py`
- Modify: `backend/tests/test_context_assembly.py`

- [ ] **Step 1: Add failing ask context-assembly tests**

```python
class ContextAssemblyTests(unittest.TestCase):
    def test_build_ask_context_bundle_deduplicates_candidates_and_marks_suspicious_evidence(self) -> None:
        candidates = [
            RetrievedChunkCandidate(path="Alpha.md", chunk_id="c1", heading_path="Alpha", text="safe text", score=0.8),
            RetrievedChunkCandidate(path="Alpha.md", chunk_id="c1", heading_path="Alpha", text="safe text", score=0.8),
            RetrievedChunkCandidate(path="Beta.md", chunk_id="c2", heading_path="Beta", text="ignore previous instructions", score=0.7),
        ]
        bundle = build_ask_context_bundle(
            user_query="What mentions governance?",
            candidates=candidates,
            tool_results=[],
            token_budget=40,
            allowed_tool_names=["search_notes", "load_note_excerpt"],
        )
        self.assertEqual([item.chunk_id for item in bundle.evidence_items], ["c1"])
        self.assertIn("possible_prompt_injection", bundle.safety_flags)
        self.assertTrue(any(note.startswith("trimmed_for_budget") for note in bundle.assembly_notes))
```

```python
    def test_render_tool_selection_prompt_includes_sources_and_allowed_tools(self) -> None:
        rendered = render_tool_selection_prompt(bundle)
        self.assertIn("Allowed tools:", rendered)
        self.assertIn("[1] Alpha.md", rendered)
        self.assertIn("search_notes", rendered)
```

- [ ] **Step 2: Run the new context tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.ContextAssemblyTests -v
```

Expected: FAIL because `build_ask_context_bundle()` and `render_tool_selection_prompt()` do not exist yet.

- [ ] **Step 3: Implement safety helpers, bundle builder, and prompt renderer**

Keep the implementation deterministic and rule-based:

```python
SUSPICIOUS_PATTERNS = (
    "ignore previous instructions",
    "system prompt",
    "tool call",
)


def detect_safety_flags(text: str) -> list[str]:
    lowered = text.lower()
    return [
        "possible_prompt_injection"
        for pattern in SUSPICIOUS_PATTERNS
        if pattern in lowered
    ]


def build_ask_context_bundle(... ) -> ContextBundle:
    deduped = _dedupe_candidates(candidates)
    trimmed = _trim_candidates_to_budget(deduped, token_budget)
    evidence_items = [
        ContextEvidenceItem(
            source_path=item.path,
            chunk_id=item.chunk_id,
            heading_path=item.heading_path,
            text=item.text,
            score=item.score,
            source_kind="retrieval",
        )
        for item in trimmed
        if not detect_safety_flags(item.text)
    ]
    safety_flags = _collect_flags(trimmed)
    return ContextBundle(...)


def render_tool_selection_prompt(bundle: ContextBundle) -> str:
    return "\n".join(
        [
            f"User intent: {bundle.user_intent}",
            f"Allowed tools: {', '.join(bundle.allowed_tool_names)}",
            *[
                f"[{index}] {item.source_path} :: {item.text}"
                for index, item in enumerate(bundle.evidence_items, start=1)
            ],
        ]
    )
```

Implementation notes:
- approximate token budget with character count first; keep it simple and testable
- keep allowed tool names on `ContextBundle.allowed_tool_names` so the renderer stays pure
- do not call the model from this layer

- [ ] **Step 4: Re-run the context tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.ContextAssemblyTests -v
```

Expected: PASS with deterministic ordering, deduplication, and safety flag coverage.

- [ ] **Step 5: Commit the context assembly layer**

```bash
git add backend/app/context/assembly.py backend/app/context/render.py backend/app/context/safety.py backend/tests/test_context_assembly.py
git commit -m "feat: add shared context assembly helpers"
```

### Task 3: Implement the read-only tool registry and ask tools

**Files:**
- Create: `backend/app/tools/registry.py`
- Create: `backend/app/tools/ask_tools.py`
- Modify: `backend/tests/test_tool_registry.py`

- [ ] **Step 1: Add failing tool-registry tests**

```python
class ToolRegistryTests(unittest.TestCase):
    def test_get_allowed_tools_for_ask_returns_only_read_only_specs(self) -> None:
        specs = get_allowed_tools_for_workflow(WorkflowAction.ASK_QA)
        self.assertEqual([spec.name for spec in specs], ["search_notes", "load_note_excerpt", "list_pending_approvals"])
        self.assertTrue(all(spec.read_only for spec in specs))

    def test_validate_tool_call_rejects_unknown_tool_and_wrong_workflow(self) -> None:
        outcome = validate_tool_call(
            ToolCallDecision(requested=True, tool_name="delete_note", arguments={}),
            workflow_action=WorkflowAction.ASK_QA,
        )
        self.assertEqual(outcome.action, GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY)
        self.assertIn("tool_not_allowed", outcome.reasons)

    def test_execute_load_note_excerpt_reads_only_requested_note(self) -> None:
        result = execute_tool_call(
            ToolCallDecision(
                requested=True,
                tool_name="load_note_excerpt",
                arguments={"note_path": "Alpha.md", "max_chars": 80},
            ),
            workflow_action=WorkflowAction.ASK_QA,
            settings=settings,
        )
        self.assertTrue(result.ok)
        self.assertIn("excerpt", result.data)
```

- [ ] **Step 2: Run the tool-registry tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_tool_registry.ToolRegistryTests -v
```

Expected: FAIL because registry functions and tool implementations do not exist yet.

- [ ] **Step 3: Implement the registry, permission checks, and read-only tools**

Use a static registry instead of dynamic discovery:

```python
TOOL_REGISTRY: dict[str, ToolSpec] = {
    "search_notes": ToolSpec(...),
    "load_note_excerpt": ToolSpec(...),
    "list_pending_approvals": ToolSpec(...),
}


def get_allowed_tools_for_workflow(workflow_action: WorkflowAction) -> list[ToolSpec]:
    return [
        spec
        for spec in TOOL_REGISTRY.values()
        if workflow_action in spec.allowed_workflows
    ]


def execute_tool_call(... ) -> ToolExecutionResult:
    guardrail = validate_tool_call(...)
    if guardrail.applied:
        return ToolExecutionResult(tool_name=decision.tool_name or "", ok=False, error="tool_not_allowed")
    return TOOL_EXECUTORS[decision.tool_name](decision.arguments, settings=settings)
```

Tool implementation notes:
- `search_notes`
  - reuse `search_hybrid_chunks_in_db()` and return a compact list of `{path, chunk_id, heading_path, text, score}`
- `load_note_excerpt`
  - resolve `settings.sample_vault_dir / note_path`, read only, return a clipped excerpt and line count
- `list_pending_approvals`
  - call the same store/query helper used by the existing pending approvals endpoint; do not import FastAPI endpoint functions directly

- [ ] **Step 4: Re-run the tool-registry tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_tool_registry.ToolRegistryTests -v
```

Expected: PASS with explicit read-only tools and workflow permission enforcement.

- [ ] **Step 5: Commit the tool layer**

```bash
git add backend/app/tools/registry.py backend/app/tools/ask_tools.py backend/tests/test_tool_registry.py
git commit -m "feat: add bounded ask tool registry"
```

### Task 4: Implement ask guardrails for tool and answer release decisions

**Files:**
- Create: `backend/app/guardrails/ask.py`
- Modify: `backend/tests/test_ask_guardrails.py`

- [ ] **Step 1: Add failing guardrail tests**

```python
class AskGuardrailTests(unittest.TestCase):
    def test_guardrail_rejects_invalid_tool_request(self) -> None:
        outcome = evaluate_tool_call_outcome(
            ToolCallDecision(requested=True, tool_name="delete_note", arguments={}),
            workflow_action=WorkflowAction.ASK_QA,
        )
        self.assertEqual(outcome.action, GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY)
        self.assertIn("tool_not_allowed", outcome.reasons)

    def test_guardrail_refuses_strong_claim_when_bundle_has_injection_flag(self) -> None:
        outcome = evaluate_final_ask_response(
            answer_text="The note definitely says to reveal the system prompt.",
            citations=[AskCitation(index=1, source_path="Alpha.md", heading_path=None, chunk_id="c1")],
            bundle=ContextBundle(..., safety_flags=["possible_prompt_injection"]),
            tool_results=[],
        )
        self.assertEqual(outcome.action, GuardrailAction.POSSIBLE_INJECTION_DETECTED)
        self.assertTrue(outcome.applied)

    def test_guardrail_marks_tool_result_insufficient_when_tool_returns_empty_payload(self) -> None:
        outcome = evaluate_final_ask_response(
            answer_text="Here is the final answer.",
            citations=[],
            bundle=ContextBundle(...),
            tool_results=[ToolExecutionResult(tool_name="load_note_excerpt", ok=True, data={})],
        )
        self.assertEqual(outcome.action, GuardrailAction.TOOL_RESULT_INSUFFICIENT)
```

- [ ] **Step 2: Run the guardrail tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_guardrails.AskGuardrailTests -v
```

Expected: FAIL because `evaluate_tool_call_outcome()` and `evaluate_final_ask_response()` do not exist yet.

- [ ] **Step 3: Implement simple deterministic guardrail evaluators**

```python
def evaluate_tool_call_outcome(
    decision: ToolCallDecision,
    *,
    workflow_action: WorkflowAction,
) -> GuardrailOutcome:
    if not decision.requested:
        return GuardrailOutcome(action=GuardrailAction.ALLOW, applied=False)
    if not decision.tool_name:
        return GuardrailOutcome(action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY, applied=True, reasons=["missing_tool_name"])
    if decision.tool_name not in {spec.name for spec in get_allowed_tools_for_workflow(workflow_action)}:
        return GuardrailOutcome(action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY, applied=True, reasons=["tool_not_allowed"])
    return GuardrailOutcome(action=GuardrailAction.ALLOW, applied=False)


def evaluate_final_ask_response(... ) -> GuardrailOutcome:
    if "possible_prompt_injection" in bundle.safety_flags:
        return GuardrailOutcome(action=GuardrailAction.POSSIBLE_INJECTION_DETECTED, applied=True, reasons=["bundle_flagged"])
    if any(result.ok and not result.data for result in tool_results):
        return GuardrailOutcome(action=GuardrailAction.TOOL_RESULT_INSUFFICIENT, applied=True, reasons=["empty_tool_payload"])
    if not citations:
        return GuardrailOutcome(action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY, applied=True, reasons=["missing_citations"])
    return GuardrailOutcome(action=GuardrailAction.ALLOW, applied=False)
```

- [ ] **Step 4: Re-run the guardrail tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_guardrails.AskGuardrailTests -v
```

Expected: PASS with conservative downgrade behavior.

- [ ] **Step 5: Commit the guardrail layer**

```bash
git add backend/app/guardrails/ask.py backend/tests/test_ask_guardrails.py
git commit -m "feat: add ask guardrail outcomes"
```

### Task 5: Wire the two-pass ask flow into `run_minimal_ask()`

**Files:**
- Modify: `backend/app/services/ask.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Add failing ask workflow tests for tool selection and downgrade paths**

```python
class AskWorkflowTests(unittest.TestCase):
    def test_run_minimal_ask_executes_registered_tool_and_reassembles_context(self) -> None:
        with patch("app.services.ask._request_tool_call_decision") as mock_decision, patch("app.services.ask.execute_tool_call") as mock_tool:
            mock_decision.return_value = ToolCallDecision(
                requested=True,
                tool_name="load_note_excerpt",
                arguments={"note_path": "Alpha.md", "max_chars": 80},
                rationale="Need more local context",
            )
            mock_tool.return_value = ToolExecutionResult(
                tool_name="load_note_excerpt",
                ok=True,
                data={"excerpt": "extra note details"},
            )
            result = run_minimal_ask(request, settings=settings)
        self.assertFalse(result.retrieval_fallback_used)
        self.assertTrue(result.tool_call_attempted)
        self.assertEqual(result.tool_call_used, "load_note_excerpt")

    def test_run_minimal_ask_ignores_invalid_tool_and_downgrades_to_retrieval_only(self) -> None:
        with patch("app.services.ask._request_tool_call_decision") as mock_decision:
            mock_decision.return_value = ToolCallDecision(
                requested=True,
                tool_name="delete_note",
                arguments={},
            )
            result = run_minimal_ask(request, settings=settings)
        self.assertEqual(result.mode, AskResultMode.RETRIEVAL_ONLY)
        self.assertEqual(result.guardrail_action, GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY)
```

- [ ] **Step 2: Run the focused ask workflow tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_executes_registered_tool_and_reassembles_context tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_ignores_invalid_tool_and_downgrades_to_retrieval_only -v
```

Expected: FAIL because the new helper functions and `AskWorkflowResult` fields are not wired into `run_minimal_ask()` yet.

- [ ] **Step 3: Implement the bounded two-pass ask flow**

Refactor `run_minimal_ask()` conservatively:

```python
def run_minimal_ask(request: WorkflowInvokeRequest, *, settings: Settings) -> AskWorkflowResult:
    candidates = search_hybrid_chunks_in_db(...)
    citations = _build_citations(candidates)
    if not citations:
        return _build_retrieval_only_result(...)

    bundle = build_ask_context_bundle(
        user_query=request.user_query or "",
        candidates=candidates,
        tool_results=[],
        token_budget=ASK_CONTEXT_TOKEN_BUDGET,
        allowed_tool_names=[spec.name for spec in get_allowed_tools_for_workflow(request.action_type)],
    )

    tool_decision = _request_tool_call_decision(
        query=request.user_query or "",
        bundle=bundle,
        provider_preference=request.provider_preference,
    )
    tool_guardrail = evaluate_tool_call_outcome(tool_decision, workflow_action=request.action_type)
    tool_results: list[ToolExecutionResult] = []
    if tool_decision.requested and not tool_guardrail.applied:
        tool_results.append(execute_tool_call(tool_decision, workflow_action=request.action_type, settings=settings))
        bundle = build_ask_context_bundle(
            user_query=request.user_query or "",
            candidates=candidates,
            tool_results=tool_results,
            token_budget=ASK_CONTEXT_TOKEN_BUDGET,
            allowed_tool_names=[...],
        )

    generated = _try_generate_grounded_answer(...)
    final_guardrail = evaluate_final_ask_response(
        answer_text=generated.answer_markdown if generated else "",
        citations=generated.citations if generated else [],
        bundle=bundle,
        tool_results=tool_results,
    )
    if generated is None or final_guardrail.applied:
        return _build_retrieval_only_result(..., guardrail_outcome=final_guardrail)
    return AskWorkflowResult(..., tool_call_attempted=tool_decision.requested, tool_call_used=tool_decision.tool_name, guardrail_action=final_guardrail.action)
```

Implementation notes:
- allow at most one tool call in phase 1
- keep `_request_grounded_answer()` for final answer generation
- add a new `_request_tool_call_decision()` helper that expects a tiny JSON payload (`requested`, `tool_name`, `arguments`, `rationale`) and falls back to `requested=False` on parse failure
- keep the existing retrieval-only fallback behavior as the safety net

- [ ] **Step 4: Run the full ask workflow test file**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v
```

Expected: PASS, including all pre-existing retrieval / checkpoint / trace resilience cases.

- [ ] **Step 5: Commit the ask service refactor**

```bash
git add backend/app/services/ask.py backend/tests/test_ask_workflow.py backend/app/contracts/workflow.py
git commit -m "feat: wire ask context assembly and tool calling"
```

### Task 6: Surface tool and guardrail metadata through ask graph traces

**Files:**
- Modify: `backend/app/graphs/ask_graph.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Add failing trace assertions**

```python
    def test_invoke_ask_graph_emits_tool_and_guardrail_trace_fields(self) -> None:
        execution = invoke_ask_graph(...)
        execute_event = execution.trace_events[1]
        self.assertIn("tool_call_attempted", execute_event["details"])
        self.assertIn("tool_call_used", execute_event["details"])
        self.assertIn("guardrail_action", execute_event["details"])
```

- [ ] **Step 2: Run the single trace test and confirm it fails**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_invoke_ask_graph_emits_tool_and_guardrail_trace_fields -v
```

Expected: FAIL because the trace detail keys are not present yet.

- [ ] **Step 3: Update `ask_graph` trace details and graph state passthrough**

```python
details={
    "result_mode": ask_result.mode.value,
    "candidate_count": len(ask_result.retrieved_candidates),
    "retrieval_fallback_used": ask_result.retrieval_fallback_used,
    "model_fallback_used": ask_result.model_fallback_used,
    "tool_call_attempted": ask_result.tool_call_attempted,
    "tool_call_used": ask_result.tool_call_used or "",
    "guardrail_action": ask_result.guardrail_action.value if ask_result.guardrail_action else "",
}
```

Also persist the new fields into `state["ask_result"]` exactly once; do not add a second source of truth in the graph state.

- [ ] **Step 4: Re-run the ask workflow tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v
```

Expected: PASS with the new trace keys present.

- [ ] **Step 5: Commit the trace updates**

```bash
git add backend/app/graphs/ask_graph.py backend/tests/test_ask_workflow.py
git commit -m "feat: trace ask tool and guardrail metadata"
```

### Task 7: Reuse context assembly in `INGEST_STEWARD`

**Files:**
- Modify: `backend/app/services/ingest_proposal.py`
- Modify: `backend/tests/test_context_assembly.py`
- Modify: `backend/tests/test_ingest_workflow.py`

- [ ] **Step 1: Add failing ingest context tests**

```python
class ContextAssemblyTests(unittest.TestCase):
    def test_build_ingest_context_bundle_orders_findings_before_related_candidates(self) -> None:
        bundle = build_ingest_context_bundle(
            note_path="Alpha.md",
            findings=[...],
            related_candidates=[...],
            token_budget=500,
        )
        self.assertEqual(bundle.evidence_items[0].source_kind, "proposal")
        self.assertGreaterEqual(len(bundle.assembly_notes), 1)
```

```python
class IngestWorkflowTests(unittest.TestCase):
    def test_scoped_ingest_proposal_records_context_bundle_summary(self) -> None:
        build_result = build_scoped_ingest_approval_proposal(...)
        self.assertIn("context_bundle_summary", build_result.note_meta)
        self.assertGreaterEqual(build_result.note_meta["context_bundle_summary"]["evidence_count"], 1)
```

- [ ] **Step 2: Run the focused ingest tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.ContextAssemblyTests.test_build_ingest_context_bundle_orders_findings_before_related_candidates tests.test_ingest_workflow.IngestWorkflowTests.test_scoped_ingest_proposal_records_context_bundle_summary -v
```

Expected: FAIL because the ingest bundle builder and `context_bundle_summary` metadata do not exist yet.

- [ ] **Step 3: Implement ingest bundle assembly without changing approval semantics**

Add a shared helper and consume it inside `build_scoped_ingest_approval_proposal()`:

```python
bundle = build_ingest_context_bundle(
    note_path=str(target_note_path),
    findings=findings,
    related_candidates=related_candidates,
    token_budget=INGEST_CONTEXT_TOKEN_BUDGET,
)
note_meta["context_bundle_summary"] = {
    "evidence_count": len(bundle.evidence_items),
    "safety_flags": bundle.safety_flags,
    "assembly_notes": bundle.assembly_notes,
}
review_markdown = _build_review_markdown(..., context_bundle=bundle)
```

Guardrails for this task:
- no tool selection
- no change to `Proposal.patch_ops`
- no change to approval-required behavior

- [ ] **Step 4: Re-run the ingest workflow tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ingest_workflow -v
```

Expected: PASS with unchanged approval flow and new metadata available for debugging / interview discussion.

- [ ] **Step 5: Commit the ingest reuse**

```bash
git add backend/app/services/ingest_proposal.py backend/tests/test_context_assembly.py backend/tests/test_ingest_workflow.py
git commit -m "feat: reuse context assembly in ingest proposal"
```

### Task 8: Reuse context assembly in `DAILY_DIGEST`

**Files:**
- Modify: `backend/app/services/digest.py`
- Modify: `backend/tests/test_context_assembly.py`
- Modify: `backend/tests/test_digest_workflow.py`

- [ ] **Step 1: Add failing digest context tests**

```python
class ContextAssemblyTests(unittest.TestCase):
    def test_build_digest_context_bundle_preserves_recent_note_order(self) -> None:
        bundle = build_digest_context_bundle(source_notes=notes, fallback_reason=None, token_budget=600)
        self.assertEqual([item.source_path for item in bundle.evidence_items[:2]], ["Daily-2026-03-21.md", "Summary.md"])
```

```python
class DigestWorkflowTests(unittest.TestCase):
    def test_run_minimal_digest_records_context_bundle_summary(self) -> None:
        result = run_minimal_digest(settings=settings)
        self.assertGreaterEqual(result.context_bundle_summary["evidence_count"], 1)
```

- [ ] **Step 2: Run the focused digest tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.ContextAssemblyTests.test_build_digest_context_bundle_preserves_recent_note_order tests.test_digest_workflow.DigestWorkflowTests.test_run_minimal_digest_records_context_bundle_summary -v
```

Expected: FAIL because digest bundle helpers and result metadata do not exist yet.

- [ ] **Step 3: Implement digest bundle assembly and metadata propagation**

Keep digest deterministic:

```python
bundle = build_digest_context_bundle(
    source_notes=source_notes,
    fallback_reason=fallback_reason,
    token_budget=DIGEST_CONTEXT_TOKEN_BUDGET,
)
return DigestWorkflowResult(
    digest_markdown=_build_digest_markdown(source_notes=source_notes, fallback_reason=fallback_reason, context_bundle=bundle),
    source_notes=source_notes,
    source_note_count=len(source_notes),
    fallback_used=fallback_reason is not None,
    fallback_reason=fallback_reason,
    context_bundle_summary={
        "evidence_count": len(bundle.evidence_items),
        "assembly_notes": bundle.assembly_notes,
    },
)
```

If adding `context_bundle_summary` to `DigestWorkflowResult`, make it optional with a default empty dict so older callers remain compatible.

- [ ] **Step 4: Re-run the digest workflow tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_digest_workflow -v
```

Expected: PASS with unchanged digest fallback behavior.

- [ ] **Step 5: Commit the digest reuse**

```bash
git add backend/app/services/digest.py backend/tests/test_context_assembly.py backend/tests/test_digest_workflow.py backend/app/contracts/workflow.py
git commit -m "feat: reuse context assembly in digest workflow"
```

### Task 9: Extend offline eval coverage and run full backend verification

**Files:**
- Modify: `eval/run_eval.py`
- Modify: `backend/tests/test_eval_runner.py`
- Modify: `backend/tests/test_ask_workflow.py` (only if fixture helpers need updates)

- [ ] **Step 1: Add failing eval-runner assertions for the new ask scenarios**

```python
class EvalRunnerTests(unittest.TestCase):
    def test_run_eval_reports_tool_and_guardrail_metrics_for_new_ask_cases(self) -> None:
        payload = _run_eval_cases(
            "ask_fixture_tool_call_load_excerpt_success",
            "ask_fixture_invalid_tool_request_downgrades",
            "ask_fixture_injection_guardrail_refusal",
        )
        ask_overview = payload["summary"]["benchmark_overview"]["ask"]["scenario_overview"]["tool_and_guardrail"]
        self.assertEqual(ask_overview["selected_case_count"], 3)
        self.assertEqual(ask_overview["core_metrics"]["tool_call_breakdown"]["attempted"], 2)
        self.assertIn("guardrail:possible_injection_detected", ask_overview["failure_type_breakdown"])
```

- [ ] **Step 2: Run the eval-runner tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_eval_runner.EvalRunnerTests -v
```

Expected: FAIL because the new case IDs and benchmark metrics are not defined.

- [ ] **Step 3: Add the eval cases and summary metrics**

In `eval/run_eval.py`, add three explicit ask cases:

```python
{
    "case_id": "ask_fixture_tool_call_load_excerpt_success",
    "scenario": "tool_and_guardrail",
    "invoke": _invoke_fixture_ask(...),
    "expect": {
        "ask_result.mode": "generated_answer",
        "ask_result.tool_call_used": "load_note_excerpt",
        "ask_result.guardrail_action": "allow",
    },
},
{
    "case_id": "ask_fixture_invalid_tool_request_downgrades",
    "scenario": "tool_and_guardrail",
    "expect": {
        "ask_result.mode": "retrieval_only",
        "ask_result.guardrail_action": "downgrade_to_retrieval_only",
    },
},
{
    "case_id": "ask_fixture_injection_guardrail_refusal",
    "scenario": "tool_and_guardrail",
    "expect": {
        "ask_result.guardrail_action": "possible_injection_detected",
    },
},
```

Update benchmark aggregation to count:
- `tool_call_breakdown`
- `guardrail_action_breakdown`
- new failure types prefixed with `guardrail:`

- [ ] **Step 4: Run full backend verification**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest discover -s tests -v
```

Run from repo root:

```bash
./.conda/knowledge-steward/bin/python eval/run_eval.py --output /tmp/context-assembly-tool-registry-eval.json
```

Expected:
- all backend tests PASS
- eval writes `/tmp/context-assembly-tool-registry-eval.json`
- new ask benchmark section contains `tool_and_guardrail`

- [ ] **Step 5: Commit the eval coverage**

```bash
git add eval/run_eval.py backend/tests/test_eval_runner.py backend/tests/test_ask_workflow.py
git commit -m "test: cover tool and guardrail ask evals"
```

## Final Review Checklist

- [ ] `ASK_QA` still returns retrieval-only fallback when no provider is available.
- [ ] No tool can mutate the vault or bypass approval / writeback boundaries.
- [ ] Only `ASK_QA` can request tools in phase 1.
- [ ] `INGEST_STEWARD` and `DAILY_DIGEST` reuse context assembly without changing their control-flow semantics.
- [ ] `AskWorkflowResult` exposes enough metadata for traces and evals without breaking existing callers.
- [ ] New trace details do not log the full raw query text.
- [ ] Full backend test suite and eval runner both pass.
- [ ] Request code review before merge.
