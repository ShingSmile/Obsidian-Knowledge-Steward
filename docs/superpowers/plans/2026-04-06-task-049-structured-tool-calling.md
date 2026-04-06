# Structured Tool Calling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move ask tool selection from prompt-based JSON parsing to OpenAI-compatible structured tool calling while preserving the existing registry, guardrails, graph loop, and provider fallback behavior.

**Architecture:** Keep `ToolSpec`, `ToolCallDecision`, and `execute_tool_call()` unchanged at the domain layer. Add a thin structured transport adapter in `backend/app/services/ask.py` that maps registry specs into `tools`, parses `message.tool_calls`, and falls back to the legacy prompt-based path when structured calls are unsupported or unusable.

**Tech Stack:** Python 3.12, Pydantic, OpenAI-compatible chat completions payloads, `unittest`.

---

## Scope Check

Keep this as one plan. All required changes are part of the same transport
upgrade and share the same acceptance boundary.

## File Structure

### Create

- None expected.

### Modify

- `backend/app/services/ask.py`
  - Add tool descriptor mapping, structured response parsing, and structured-to-legacy fallback orchestration.
- `backend/tests/test_ask_workflow.py`
  - Add regression coverage for structured tool selection and fallback behavior.
- `backend/tests/test_tool_registry.py`
  - Add focused assertions for `ToolSpec -> tools` payload mapping if helper lives in `ask.py` or expand existing registry-adjacent coverage.

### No Changes Expected

- `backend/app/graphs/ask_graph.py`
  - Graph routing should stay unchanged because it already operates on `ToolCallDecision`.
- `backend/app/contracts/workflow.py`
  - Existing Pydantic contracts are sufficient.
- `backend/app/context/render.py`
  - Grounded-answer prompt stays as-is; only the legacy tool-selection fallback continues to use the tool-selection prompt.

### Skills To Use During Execution

- `@test-driven-development` before production edits.
- `@verification-before-completion` before any success claim.

## Implementation Tasks

### Task 1: Lock structured tool-calling behavior with failing tests

**Files:**
- Modify: `backend/tests/test_ask_workflow.py`
- Modify: `backend/tests/test_tool_registry.py`

- [ ] **Step 1: Add a failing test for structured tool-call parsing**

Add a test that feeds an OpenAI-compatible response payload containing one
`message.tool_calls` entry and asserts the resulting `ToolCallDecision` is:

- `requested=True`
- `tool_name` equals the function name
- `arguments` come from parsed JSON

- [ ] **Step 2: Add a failing test for structured-to-legacy fallback**

Add a test that makes the structured request path fail once, then asserts:

- the legacy prompt-based path is attempted
- the fallback result still returns the expected `ToolCallDecision`

- [ ] **Step 3: Add a failing test for tool descriptor mapping**

Add a focused test that maps an existing `ToolSpec` and asserts the descriptor
contains:

- `type == "function"`
- `function.name`
- `function.description`
- `function.parameters`

- [ ] **Step 4: Run the targeted tests and confirm they fail for the new cases**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.worktrees/task-049-structured-tool-calling/backend
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow tests.test_tool_registry -v
```

Expected: the newly added structured-calling tests fail because the production
helpers do not exist yet.

### Task 2: Implement the structured tool-calling transport

**Files:**
- Modify: `backend/app/services/ask.py`

- [ ] **Step 1: Add descriptor and parsing helpers**

Introduce minimal helpers for:

- building structured `tools` payloads from allowed `ToolSpec`s
- extracting the first usable `tool_call` from a chat completion response
- decoding function arguments JSON safely

- [ ] **Step 2: Split legacy and structured request paths**

Refactor the current tool-decision request flow into:

- `_request_structured_tool_call_decision(...)`
- `_request_prompt_tool_call_decision(...)`
- `_request_tool_call_decision(...)` as the orchestrator

Behavior:

- try structured path first
- if structured request errors or produces unusable output, try legacy prompt
- preserve existing provider iteration order

- [ ] **Step 3: Keep graph-facing behavior stable**

Ensure the returned object is still `ToolCallDecision`, so:

- `decide_ask_tool_call()` stays unchanged at the call site
- `ask_graph` routing remains untouched
- guardrail validation and tool execution continue to operate exactly as before

- [ ] **Step 4: Re-run the targeted tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.worktrees/task-049-structured-tool-calling/backend
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow tests.test_tool_registry -v
```

Expected: all targeted ask and tool-registry tests pass, including the new
structured/fallback coverage.

### Task 3: Run the broader verification set for TASK-049

**Files:**
- Modify: `backend/app/services/ask.py`
- Modify: `backend/tests/test_ask_workflow.py`
- Modify: `backend/tests/test_tool_registry.py`

- [ ] **Step 1: Run focused ask verification**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.worktrees/task-049-structured-tool-calling/backend
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow -v
```

- [ ] **Step 2: Run focused registry verification**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.worktrees/task-049-structured-tool-calling/backend
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python -m unittest tests.test_tool_registry -v
```

- [ ] **Step 3: Review diff against TASK-049 scope**

Confirm the diff only changes:

- structured transport helpers
- fallback orchestration
- task-specific tests

and does not drift into new tools, graph rewrites, or ingest/digest changes.
