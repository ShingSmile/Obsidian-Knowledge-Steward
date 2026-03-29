# TASK-045 Controlled Writeback And Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add verified-only ask tools for note outlines and backlinks, bounded `replace_section` / `add_wikilink` writeback ops, and shared static proposal validation without widening the repo's writeback risk surface.

**Architecture:** Keep the ask-side extension inside the existing backend tool registry and ask controller: `get_note_outline` reads the current file directly, while `find_backlinks` discovers candidates from SQLite and only emits prompt-visible facts after host-side resolution and freshness checks. Keep writeback bounded by adding two new plugin helpers, and centralize static proposal validation in a dedicated backend service that runs both before proposal persistence and before `/workflows/resume` accepts a stored proposal.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLite, LangGraph workflow wrappers, TypeScript, Obsidian plugin APIs, `unittest`, Node built-in test runner, esbuild.

---

## File Structure

Follow the existing backend / plugin split. Keep API-facing schema changes in contracts, keep proposal safety in a dedicated backend service, keep ask-specific tool execution in `backend/app/tools/`, and keep markdown mutation logic centralized in `plugin/src/writeback/helpers.ts`.

### Create

- `backend/app/services/proposal_validation.py`
  - Shared static validation for proposal target paths, payload size, dangerous patterns, and bounded patch-op shapes.
- `backend/app/tools/backlinks.py`
  - Helper functions for backlink candidate discovery, raw wikilink normalization, uniqueness checks, and freshness verification.
- `backend/tests/test_proposal_validation.py`
  - Focused unit coverage for persistence-time and resume-time static validation.

### Modify

- `backend/app/contracts/workflow.py`
  - Extend tool result metadata and keep patch-op / safety contracts aligned with the new ops.
- `backend/app/tools/registry.py`
  - Register `get_note_outline` and `find_backlinks` and validate their input schemas.
- `backend/app/tools/ask_tools.py`
  - Implement `get_note_outline` and wire `find_backlinks` execution through the new helper module.
- `backend/app/services/ask.py`
  - Treat successful tool `data` as verified prompt payload only; downgrade when a requested tool fails.
- `backend/app/indexing/store.py`
  - Reuse the shared proposal validator before proposal persistence.
- `backend/app/services/resume_workflow.py`
  - Re-run the shared validator on stored proposals before approval/writeback.
- `backend/tests/test_tool_registry.py`
  - Add coverage for new tool registration, current-file outline reads, and fail-closed backlinks.
- `backend/tests/test_ask_workflow.py`
  - Add regression coverage for tool failure downgrade and verified tool payload re-entry.
- `backend/tests/test_ingest_workflow.py`
  - Cover proposal persistence rejection on invalid write payloads for ingest.
- `backend/tests/test_digest_workflow.py`
  - Cover proposal persistence rejection on invalid write payloads for digest.
- `backend/tests/test_resume_workflow.py`
  - Cover resume-time rejection when stored proposals violate the new validator.
- `plugin/src/contracts.ts`
  - Extend the patch-op vocabulary shared with the plugin runtime.
- `plugin/src/writeback/helpers.ts`
  - Add bounded helpers for `replace_section` and `add_wikilink`.
- `plugin/src/writeback/applyProposalWriteback.ts`
  - Validate and execute the new patch ops while preserving `before_hash` and rollback guarantees.
- `plugin/src/writeback/writeback.test.ts`
  - Add regression coverage for the two new writeback ops and duplicate-link behavior.

### No Changes Expected

- `plugin/src/views/KnowledgeStewardView.ts`
  - No UI changes are required for this task.
- graph topology files
  - `backend/app/graphs/*.py` should only need test-adjacent behavior coverage; no graph-structure changes are planned.

### Skills To Use During Execution

- `@test-driven-development` before each code change.
- `@verification-before-completion` before claiming the feature is complete.
- `@requesting-code-review` after implementation stabilizes.

## Implementation Tasks

### Task 1: Add the new tool contracts, schemas, and registry coverage

**Files:**
- Create: `backend/app/tools/backlinks.py`
- Modify: `backend/app/contracts/workflow.py`
- Modify: `backend/app/tools/registry.py`
- Modify: `backend/app/tools/ask_tools.py`
- Test: `backend/tests/test_tool_registry.py`

- [ ] **Step 1: Write the failing backend tool tests**

```python
class ToolRegistryTests(unittest.TestCase):
    def test_get_allowed_tools_for_ask_includes_outline_and_backlinks(self) -> None:
        specs = get_allowed_tools_for_workflow(WorkflowAction.ASK_QA)
        self.assertEqual(
            [spec.name for spec in specs],
            [
                "search_notes",
                "load_note_excerpt",
                "list_pending_approvals",
                "get_note_outline",
                "find_backlinks",
            ],
        )

    def test_execute_get_note_outline_reads_current_heading_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            vault.mkdir()
            (vault / "Alpha.md").write_text(
                "---\nkind: note\n---\n# Alpha\n\n## Next\nText\n",
                encoding="utf-8",
            )
            settings = replace(get_settings(), sample_vault_dir=vault)
            result = execute_tool_call(
                ToolCallDecision(
                    requested=True,
                    tool_name="get_note_outline",
                    arguments={"note_path": "Alpha.md"},
                ),
                workflow_action=WorkflowAction.ASK_QA,
                settings=settings,
            )
            self.assertTrue(result.ok)
            self.assertEqual(result.data["headings"][1]["heading_path"], "Alpha > Next")

    def test_execute_find_backlinks_fails_closed_when_candidate_note_is_stale(self) -> None:
        ...
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "index_stale")
        self.assertEqual(result.data, {})
        self.assertEqual(result.diagnostics["failure_code"], "index_stale")
```

- [ ] **Step 2: Run the targeted backend tests to confirm they fail for the expected reason**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_tool_registry -v
```

Expected: FAIL because the new tools, `diagnostics` field, and backlink helper logic do not exist yet.

- [ ] **Step 3: Implement the minimal contract and registry changes**

Add the new tool metadata without over-expanding the existing contract surface:

```python
class ToolExecutionResult(BaseModel):
    tool_name: str
    ok: bool
    data: dict[str, object] = Field(default_factory=dict)
    error: str | None = None
    diagnostics: dict[str, object] = Field(default_factory=dict)
    allow_context_reentry: bool = True
```

Register the two new read-only tools in `backend/app/tools/registry.py`:

```python
"get_note_outline": ToolSpec(
    name="get_note_outline",
    purpose="Return frontmatter summary and heading tree for one note.",
    allowed_workflows=[WorkflowAction.ASK_QA],
    input_schema={
        "type": "object",
        "properties": {"note_path": {"type": "string"}},
        "required": ["note_path"],
        "additionalProperties": False,
    },
    output_schema={"type": "object"},
    risk_level="low",
    read_only=True,
),
```

Implement `get_note_outline` in `backend/app/tools/ask_tools.py` by parsing the current file directly, and move backlink-specific normalization / freshness helpers into `backend/app/tools/backlinks.py`.

- [ ] **Step 4: Re-run the targeted backend tool tests and make them pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_tool_registry -v
```

Expected: PASS, proving the tool registry exposes the new tools and `find_backlinks` fails closed instead of leaking partial facts.

- [ ] **Step 5: Commit the tool and contract changes**

```bash
git add backend/app/contracts/workflow.py backend/app/tools/registry.py backend/app/tools/ask_tools.py backend/app/tools/backlinks.py backend/tests/test_tool_registry.py
git commit -m "feat: add verified outline and backlink tools"
```

### Task 2: Make ask treat tool payloads as verified-only facts

**Files:**
- Modify: `backend/app/services/ask.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write the failing ask workflow tests**

```python
class AskWorkflowTests(unittest.TestCase):
    def test_run_minimal_ask_downgrades_when_requested_tool_fails(self) -> None:
        with patch(
            "app.services.ask._request_tool_call_decision",
            return_value=ToolCallDecision(
                requested=True,
                tool_name="find_backlinks",
                arguments={"note_path": "Roadmap.md"},
            ),
        ), patch(
            "app.services.ask.execute_tool_call",
            return_value=ToolExecutionResult(
                tool_name="find_backlinks",
                ok=False,
                error="index_stale",
                diagnostics={"failure_code": "index_stale", "retryable": False},
            ),
        ), patch("app.services.ask._request_grounded_answer") as mocked_answer:
            result = run_minimal_ask(...)
        self.assertEqual(result.mode, AskResultMode.RETRIEVAL_ONLY)
        mocked_answer.assert_not_called()

    def test_run_minimal_ask_includes_verified_outline_payload_in_prompt(self) -> None:
        ...
        self.assertIn('"headings"', captured_messages["messages"][1]["content"])
```

- [ ] **Step 2: Run the targeted ask workflow tests and watch them fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_downgrades_when_requested_tool_fails tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_includes_verified_outline_payload_in_prompt -v
```

Expected: FAIL because `run_minimal_ask()` still treats any successful tool path as prompt-reenterable and does not short-circuit on tool failure.

- [ ] **Step 3: Implement the minimal ask-controller changes**

Keep the prompt-visible boundary narrow in `backend/app/services/ask.py`:

```python
if tool_decision.requested:
    tool_result = execute_tool_call(...)
    tool_results.append(tool_result)
    if not tool_result.ok:
        return _build_retrieval_only_result(
            query=query,
            citations=citations,
            candidates=prompt_candidates,
            retrieval_fallback_used=retrieval_response.fallback_used,
            retrieval_fallback_reason=retrieval_response.fallback_reason,
            tool_decision=tool_decision,
            guardrail_outcome=GuardrailOutcome(
                action=GuardrailAction.TOOL_RESULT_INSUFFICIENT,
                applied=True,
                reasons=[tool_result.error or "tool_failed"],
            ),
        )
```

Do not pass `diagnostics` into the grounded answer prompt. Only `result.data` from successful tools remains prompt-visible.

- [ ] **Step 4: Re-run the targeted ask workflow tests and make them pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_downgrades_when_requested_tool_fails tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_includes_verified_outline_payload_in_prompt -v
```

Expected: PASS, confirming the ask controller does not let failed tool calls silently turn into model guesses.

- [ ] **Step 5: Commit the ask-controller update**

```bash
git add backend/app/services/ask.py backend/tests/test_ask_workflow.py
git commit -m "feat: enforce verified-only ask tool reentry"
```

### Task 3: Add shared static proposal validation before persistence and before resume

**Files:**
- Create: `backend/app/services/proposal_validation.py`
- Modify: `backend/app/indexing/store.py`
- Modify: `backend/app/services/resume_workflow.py`
- Test: `backend/tests/test_proposal_validation.py`
- Test: `backend/tests/test_resume_workflow.py`

- [ ] **Step 1: Write the failing proposal-validation tests**

```python
class ProposalValidationTests(unittest.TestCase):
    def test_validate_rejects_insert_content_over_default_limit(self) -> None:
        proposal = Proposal(
            action_type=WorkflowAction.DAILY_DIGEST,
            target_note_path="Daily.md",
            summary="digest",
            risk_level=RiskLevel.HIGH,
            patch_ops=[
                PatchOp(
                    op="insert_under_heading",
                    target_path="Daily.md",
                    payload={"heading": "## Digest", "content": "X" * 2001},
                )
            ],
        )
        with self.assertRaisesRegex(ValueError, "content_length_exceeded"):
            validate_proposal_for_persistence(proposal, settings=settings)

    def test_validate_rejects_target_path_outside_vault(self) -> None:
        ...

    def test_validate_rejects_dangerous_script_tag(self) -> None:
        ...
```

Add one failing resume regression:

```python
def test_resume_workflow_rejects_stored_proposal_that_now_fails_static_validation(self) -> None:
    ...
    with self.assertRaises(ResumeWorkflowValidationError):
        resume_workflow(request, settings=settings, run_id="run_resume")
```

- [ ] **Step 2: Run the targeted validation tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_proposal_validation tests.test_resume_workflow -v
```

Expected: FAIL because there is no shared validator and resume currently trusts any stored proposal shape that matches the existing contract.

- [ ] **Step 3: Implement the minimal shared validator and wire it into both gates**

Create `backend/app/services/proposal_validation.py` with one narrow entrypoint:

```python
def validate_proposal_for_persistence(
    proposal: Proposal,
    *,
    settings: Settings,
    content_limit: int = 2000,
) -> None:
    _validate_target_path_inside_vault(proposal.target_note_path, settings=settings)
    for patch_op in proposal.patch_ops:
        _validate_patch_op_shape(patch_op, proposal=proposal, settings=settings)
        _validate_patch_op_target_path(patch_op, settings=settings)
        _validate_patch_op_text_payloads(patch_op, content_limit=content_limit)
        _validate_patch_op_dangerous_patterns(patch_op)
```

Wire it into:

- `backend/app/indexing/store.py` before `save_proposal_record(...)` writes anything
- `backend/app/services/resume_workflow.py` immediately after loading the stored proposal

- [ ] **Step 4: Re-run the targeted validation tests and make them pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_proposal_validation tests.test_resume_workflow -v
```

Expected: PASS, showing that invalid proposals are rejected both before persistence and before resume-side effects.

- [ ] **Step 5: Commit the validation layer**

```bash
git add backend/app/services/proposal_validation.py backend/app/indexing/store.py backend/app/services/resume_workflow.py backend/tests/test_proposal_validation.py backend/tests/test_resume_workflow.py
git commit -m "feat: add static proposal validation"
```

### Task 4: Add bounded plugin support for `replace_section` and `add_wikilink`

**Files:**
- Modify: `plugin/src/contracts.ts`
- Modify: `plugin/src/writeback/helpers.ts`
- Modify: `plugin/src/writeback/applyProposalWriteback.ts`
- Test: `plugin/src/writeback/writeback.test.ts`

- [ ] **Step 1: Write the failing plugin writeback tests**

```typescript
test("replaceSection rewrites only the matched heading body", () => {
  const markdown = [
    "# Root",
    "",
    "## Review",
    "- old line",
    "",
    "## Next",
    "- keep me"
  ].join("\n");

  assert.match(
    applyReplaceSection(markdown, {
      heading: "## Review",
      content: "- new line"
    }),
    /## Review\n- new line\n\n## Next\n- keep me/
  );
});

test("addWikilink appends a normalized link and rejects duplicates", () => {
  const markdown = ["# Root", "", "## Links", "- [[Alpha]]"].join("\n");
  assert.throws(
    () => applyAddWikilink(markdown, { heading: "## Links", linked_note_path: "Alpha.md" }),
    /already exists/
  );
});
```

- [ ] **Step 2: Run the plugin writeback tests and confirm they fail**

Run from `plugin/`:

```bash
node --experimental-specifier-resolution=node --test src/writeback/writeback.test.ts
```

Expected: FAIL because the new helper functions and supported patch-op names do not exist yet.

- [ ] **Step 3: Implement the minimal bounded helper logic**

Extend the shared writeback helper vocabulary:

```typescript
export type SupportedPatchOpName =
  | "merge_frontmatter"
  | "insert_under_heading"
  | "replace_section"
  | "add_wikilink";
```

Implement:

- `extractReplaceSectionPayload()`
- `applyReplaceSection()`
- `extractAddWikilinkPayload()`
- `applyAddWikilink()`

Then wire them into `applyProposalWriteback()` and `validatePatchPlan()` without weakening the existing single-note / `before_hash` checks.

- [ ] **Step 4: Re-run plugin tests and build output**

Run from `plugin/`:

```bash
node --experimental-specifier-resolution=node --test src/writeback/writeback.test.ts
npm run build
```

Expected: PASS for tests and a clean plugin bundle build.

- [ ] **Step 5: Commit the plugin writeback changes**

```bash
git add plugin/src/contracts.ts plugin/src/writeback/helpers.ts plugin/src/writeback/applyProposalWriteback.ts plugin/src/writeback/writeback.test.ts
git commit -m "feat: add bounded section replace and wikilink writeback"
```

### Task 5: Add proposal-path regressions and run the final verification sweep

**Files:**
- Modify: `backend/tests/test_ingest_workflow.py`
- Modify: `backend/tests/test_digest_workflow.py`
- Review: `backend/tests/test_tool_registry.py`
- Review: `backend/tests/test_ask_workflow.py`
- Review: `backend/tests/test_resume_workflow.py`
- Review: `plugin/src/writeback/writeback.test.ts`

- [ ] **Step 1: Write the failing ingest and digest persistence regressions**

```python
class IngestWorkflowTests(unittest.TestCase):
    def test_ingest_waiting_proposal_rejects_invalid_replace_section_payload_before_persist(self) -> None:
        ...
        with self.assertRaisesRegex(ValueError, "dangerous_pattern_detected"):
            invoke_workflow(request, Response())


class DigestWorkflowTests(unittest.TestCase):
    def test_digest_waiting_proposal_rejects_out_of_vault_patch_target(self) -> None:
        ...
        with self.assertRaisesRegex(ValueError, "target_path_outside_vault"):
            invoke_workflow(request, Response())
```

- [ ] **Step 2: Run the focused integration tests and confirm they fail first**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ingest_workflow tests.test_digest_workflow -v
```

Expected: FAIL until the new validator is actually hit by proposal persistence in both approval-producing paths.

- [ ] **Step 3: Make the smallest integration fixes needed and keep the earlier units green**

Do only the minimum wiring needed so:

- ingest approval generation hits the shared validator before persistence
- digest approval generation hits the shared validator before persistence
- no existing `merge_frontmatter` / `insert_under_heading` behavior regresses

- [ ] **Step 4: Run the full verification sweep**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_tool_registry tests.test_ask_workflow tests.test_proposal_validation tests.test_resume_workflow tests.test_ingest_workflow tests.test_digest_workflow -v
PYTHONPYCACHEPREFIX=/tmp/ks-pycache ../.conda/knowledge-steward/bin/python -m compileall app tests
```

Run from `plugin/`:

```bash
npm test
npm run build
```

Expected:

- all targeted backend tests PASS
- `compileall` PASS
- plugin tests PASS
- plugin build PASS

- [ ] **Step 5: Commit the integration coverage and verification-ready state**

```bash
git add backend/tests/test_ingest_workflow.py backend/tests/test_digest_workflow.py
git commit -m "test: cover validated proposal persistence paths"
```
