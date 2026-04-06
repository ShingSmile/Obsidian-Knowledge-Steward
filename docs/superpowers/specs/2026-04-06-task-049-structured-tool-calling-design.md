# Structured Tool Calling Design

**Problem**

The ask workflow already uses a graph-level ReAct loop, but its tool-selection
step still relies on prompt text that asks the model to emit strict JSON. The
runtime then parses that raw text with `json.loads()` and silently falls back to
no tool call when the JSON is malformed. This leaves the "tool calling" story
partly true at the workflow level but false at the transport level.

**Goal**

Upgrade ask tool selection to OpenAI-compatible structured tool calling while
preserving the existing tool registry, guardrails, ReAct loop shape, and
fallback behavior for providers that do not support structured `tool_calls`.

**Non-Goals**

- Do not redesign `ToolSpec`.
- Do not change the registered tools or their schemas.
- Do not change `ask_graph` routing or the existing `tool_node` execution path.
- Do not migrate ingest or digest workflows.
- Do not add parallel tool calls.

**Recommended Approach**

Add a thin transport layer in `backend/app/services/ask.py`:

1. map existing `ToolSpec` models into OpenAI-compatible `tools` payloads
2. send tool-selection requests with `tools` and a conservative `tool_choice`
3. parse `message.tool_calls` into the existing `ToolCallDecision`
4. if the provider errors, omits structured tool calls, or returns an unusable
   payload, fall back to the existing prompt-based JSON path

This keeps the rest of the system stable. The graph still consumes
`ToolCallDecision`, the registry still validates and executes tools, and the
prompt-based path remains available as compatibility fallback.

**Alternatives Considered**

1. Replace the entire ask provider layer with an SDK client.
   Rejected because `TASK-049` is about transport semantics, not a broad client
   refactor.
2. Add a second structured tool schema next to `ToolSpec`.
   Rejected because it would duplicate schema ownership and drift from the
   existing registry.
3. Keep raw JSON but strengthen the parser.
   Rejected because it still leaves format correctness outside the API contract.

## 1. Transport Boundary

The current ask flow has two model interactions:

- tool selection
- grounded answer generation

Only tool selection changes in this task. Grounded answer generation remains a
plain chat completion because the final answer is still free-form cited text.

The new transport boundary should expose:

- `ToolSpec -> OpenAI tool descriptor`
- response payload -> `ToolCallDecision`
- structured call failure -> prompt-based fallback

That means `ask_graph` and the rest of the workflow continue to see the same
domain object: `ToolCallDecision`.

## 2. Provider Strategy

Structured tool calling should be attempted only for providers that speak the
existing OpenAI-compatible `/v1/chat/completions` contract well enough to accept
`tools`.

The compatibility rule for this task is intentionally conservative:

- try structured tool calling first on the selected provider
- if the request errors or returns no usable structured tool payload, retry the
  same provider with the existing prompt-based JSON request
- if that still fails, continue to the next provider target using the same rule

This preserves the current cloud-first/local-fallback behavior while adding a
better primary path for capable providers.

## 3. Mapping Rules

`ToolSpec` already has the fields needed for OpenAI-compatible tool calling.

Required mapping:

- `ToolSpec.name -> tools[].function.name`
- `ToolSpec.purpose -> tools[].function.description`
- `ToolSpec.input_schema -> tools[].function.parameters`

No second schema should be introduced. The registry remains the only source of
truth for tool input validation.

## 4. Parsing Rules

Structured responses should be interpreted with the following behavior:

- no `tool_calls` => `ToolCallDecision(requested=False)`
- one valid `tool_call` => parse its function name and JSON arguments
- malformed arguments JSON => treat as unusable and fall back
- multiple tool calls => accept only the first one for now and ignore the rest

The single-tool restriction matches the current ReAct loop and avoids sneaking a
parallel-tool feature into this task.

## 5. Prompt Changes

When structured tool calling is used successfully, the old tool-selection prompt
contract is no longer needed. The prompt should stop listing:

- the "return strict JSON only" instruction
- the inline tool-name enumeration as the transport contract

However, the fallback path must keep the existing prompt-based tool-selection
messages so providers without structured support still behave as before.

## 6. Testing Strategy

Testing should cover three paths:

1. `ToolSpec` correctly maps into structured `tools` payloads
2. structured `tool_calls` responses produce the right `ToolCallDecision`
3. provider error or malformed structured response falls back to the current
   prompt-based JSON path without changing guardrail behavior

Regression coverage should stay concentrated in:

- `backend/tests/test_tool_registry.py`
- `backend/tests/test_ask_workflow.py`

## 7. Acceptance Check

This design satisfies `TASK-049` when:

- ask tool selection uses API-level structured tools on capable providers
- existing `ToolSpec` remains the schema source of truth
- `ToolCallDecision` remains the graph-facing contract
- malformed structured responses no longer silently become the only behavior
  path; they first trigger prompt-based fallback
- current ask/tool-registry regressions continue to pass
