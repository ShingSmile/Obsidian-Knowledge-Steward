# TASK-045 Controlled Writeback and Tooling Design

- Status: approved in conversation
- Date: 2026-03-27
- Scope: design only, no implementation
- Target repo: `Obsidian Knowledge Steward`
- Governed task: `TASK-045`
- Planned session: `SES-20260327-02`

## 1. Background

The current repository already has the minimum governed writeback loop in place:

- ask can use a small read-only tool registry
- ingest / digest can generate approval-gated proposals
- plugin writeback can apply `merge_frontmatter` and `insert_under_heading`
- proposal persistence and resume validation already rely on `before_hash`, `max_changed_lines`, and append-only audit records

That baseline is usable, but it is still too narrow for the next stage of the project:

- ask tools do not expose current document structure
- ask tools do not expose backlink relationships
- writeback patch types do not cover section replacement or link governance
- proposal persistence only enforces schema-level shape, not content-level safety

`TASK-045` extends those boundaries without expanding into a larger architecture rewrite.

## 2. Problem Statement

Three concrete gaps are still visible in the current implementation.

### 2.1 Ask-side context gap

The ask chain can currently search notes, load a bounded excerpt, and list pending approvals. That is enough for shallow retrieval, but not enough for structure-aware reasoning:

- the model cannot inspect a note outline before asking follow-up questions
- the model cannot ask for backlink facts when tracing references across notes

### 2.2 Writeback expressiveness gap

Current proposal generation and plugin writeback only support:

- `merge_frontmatter`
- `insert_under_heading`

That leaves two common governance actions unsupported:

- replace an existing section body in a bounded way
- add a missing wikilink under a known heading

### 2.3 Safety gap

Proposal payloads are persisted after schema-compatible serialization, but there is still no shared content-level validation for:

- oversized generated content
- target paths outside the vault boundary
- dangerous text patterns embedded in write payloads

Because proposals are persisted before approval and later resumed by `/workflows/resume`, this validation must not be left to the plugin UI or to model prompt wording.

## 3. Goals

### 3.1 Functional goals

- Add `get_note_outline(path)` as a read-only ask tool.
- Add `find_backlinks(path)` as a read-only ask tool.
- Add `replace_section` as a bounded writeback patch op.
- Add `add_wikilink` as a bounded writeback patch op.
- Add shared static validation before proposal persistence.
- Re-run the same static validation before approval resume accepts a stored proposal.

### 3.2 Safety goals

- Do not expose partially trusted backlink results to the model.
- Do not allow writeback targets outside the current vault.
- Do not allow arbitrary generated content to bypass static checks simply because it fits JSON schema.
- Keep all new write actions within the existing approval and audit model.

### 3.3 Narrative goals

- Strengthen the repo's "controlled writeback" story with concrete bounded ops and explicit validation layers.
- Preserve the interview-friendly architecture distinction between:
  - safe read tools for ask
  - approval-gated write proposals for ingest / digest
  - plugin-side constrained file mutation

## 4. Non-Goals

This design explicitly does not do the following:

- no `delete_note`, `full_rewrite`, or `move_note`
- no plugin UI redesign
- no ReAct loop implementation inside ask
- no plugin-side live backlink bridge into Obsidian metadata cache
- no broad markdown AST rewrite system
- no automatic re-ingest orchestration redesign
- no new conditional edges or graph topology changes

## 5. Design Summary

The design extends three layers at once:

1. ask read tools
2. proposal / writeback patch vocabulary
3. static validation before persistence and before resume

The key safety rule is:

> The model only sees verified facts. Any partially trusted or stale diagnostics stay in host-side metadata and trace output.

## 6. Ask Tool Design

## 6.1 `get_note_outline(path)`

### Data source

`get_note_outline` reads the current markdown file directly from disk instead of using the SQLite index.

Reasoning:

- it is a single-file read, so runtime cost is bounded
- it returns current structure rather than index-time structure
- it avoids unnecessary freshness ambiguity for note outlines

### Returned facts

Successful results contain only compact structural information:

- `note_path`
- `title`
- `has_frontmatter`
- `frontmatter_summary`
- `headings[]`, each item containing:
  - `level`
  - `text`
  - `line_no`
  - `heading_path`

It does not return full note content and does not replace `load_note_excerpt`.

### Failure semantics

Failures are hard failures:

- note outside vault
- note missing
- parse/read failure

No partial outline is returned to the model.

## 6.2 `find_backlinks(path)`

### Data source

`find_backlinks` is implemented as a backend tool backed by the repository's own SQLite index.

It does not:

- scan the whole vault on each call
- depend on the plugin process
- call into Obsidian's live metadata cache

### Discovery model

Backlink discovery is a two-stage process:

1. discover candidate notes / chunks from indexed `out_links_json`
2. host-side verify that each candidate resolves uniquely and is still fresh enough to trust

### Link resolution rules

The current index stores raw wikilink text rather than canonical note-to-note edge IDs. Therefore the tool must resolve candidate links host-side before exposing them as facts.

Resolution steps:

- strip alias suffixes such as `|alias`
- strip heading suffixes such as `#Section`
- normalize relative path forms
- derive match keys for the target note:
  - normalized vault-relative path without `.md`
  - basename / stem, but only when unique in the vault

If basename uniqueness cannot be guaranteed, basename-only matching is disabled.

### Freshness and trust boundary

`find_backlinks` is fail-closed.

The tool only succeeds when it can return a verified complete result set. It must fail instead of returning "probably correct" backlink facts.

Hard failure conditions include:

- target note not indexed
- target note is stale relative to current file metadata
- any candidate source note is stale relative to current file metadata
- any backlink candidate resolves ambiguously

This means the tool has no "success with stale warning" mode for prompt re-entry.

### Returned facts

Successful results contain only verified backlinks:

- `target_path`
- `backlinks[]`, each item containing:
  - `source_path`
  - `chunk_id`
  - `heading_path`
  - `start_line`
  - `end_line`
  - `link_text`

Diagnostics about dropped or stale candidates are not prompt-visible facts.

## 6.3 Ask integration rule

The ask chain must not pass partially trusted tool diagnostics back into the grounded answer prompt.

For new tools, host-side handling is:

- success: pass verified prompt payload into the prompt
- failure: do not pass tool payload into the prompt
- tool failure after a tool request: downgrade ask behavior rather than letting the model answer as if the tool call had succeeded

This preserves the safety boundary for the current single-tool ask design and prepares for future ReAct control logic without relying on the model to interpret staleness correctly.

## 7. Patch Operation Design

## 7.1 Shared patch boundary

After `TASK-045`, the supported bounded patch op set becomes:

- `merge_frontmatter`
- `insert_under_heading`
- `replace_section`
- `add_wikilink`

No other write ops are added in this task.

## 7.2 `replace_section`

### Semantics

`replace_section` means:

- locate one heading exactly
- keep the matched heading line
- replace only that section body
- stop at the next heading of the same or higher level

### Constraints

- one target file only
- one matched heading only
- exact heading match required
- protected by the existing `before_hash`

This avoids unconstrained document rewrites while still covering the missing "rewrite this review section" scenario.

### Plugin execution

The plugin writeback layer should implement `replace_section` by reusing the same heading-boundary logic already needed for `insert_under_heading`, rather than introducing a second parsing model.

## 7.3 `add_wikilink`

### Semantics

`add_wikilink` is intentionally narrower than "insert arbitrary markdown containing a link".

Payload should contain:

- `heading`
- `linked_note_path`

The plugin executor generates the actual markdown line itself.

### Constraints

- the linked target note must already exist inside the vault
- the write occurs under one explicit heading in the current target note
- duplicate links in the same section are rejected or treated as no-op
- only the current note is edited; backlink visibility remains an emergent property of Obsidian / index traversal

This keeps link governance bounded and avoids treating the model as a free-form markdown author for this operation.

## 8. Static Validation Design

## 8.1 Primary enforcement point

Static validation should run before `save_proposal_record()` persists a proposal.

Reasoning:

- both ingest and digest approval paths already persist through this shared function
- persistence-time rejection prevents invalid proposals from entering waiting inboxes
- this keeps the protection independent of plugin UX

## 8.2 Secondary enforcement point

The same validator should run again inside `resume_workflow()` after loading the stored proposal from the database and before accepting approval/writeback.

Reasoning:

- old persisted data may predate the validator
- DB state may be manually altered
- defense-in-depth is appropriate because resume is the last gate before side effects

## 8.3 Validation rules

The validator enforces at least the following rules:

### Target path boundary

- proposal target path must remain inside the configured vault root
- every `patch_op.target_path` must remain inside the configured vault root
- cross-file patch sets remain unsupported

### Patch vocabulary

- op name must be one of the bounded supported ops
- payload fields must match the bounded shape for that op

### Content length threshold

- any model-generated write text field is rejected when it exceeds the configured threshold
- default threshold: 2000 characters

Applicable fields include:

- `insert_under_heading.payload.content`
- `replace_section.payload.content`
- any future free-text write payloads added to the allowlist

### Dangerous pattern detection

Reject write payloads containing clearly unsafe content patterns, for example:

- `<script`
- explicit destructive deletion instructions
- raw HTML/JS payloads inconsistent with the markdown governance scope

This is a denylist safety layer, not the only safety layer.

## 9. Result Shape and Host Diagnostics

The current `ToolExecutionResult` shape is too loose for verified-only semantics. The preferred direction is to separate prompt-visible facts from host-only diagnostics.

Preferred structure:

- `prompt_payload`: verified facts that may enter the model prompt
- `diagnostics`: host-only metadata for trace, debugging, and downgrade decisions

If the repository keeps the existing `data` field for compatibility, the same semantic split must still be enforced:

- `data` only contains verified prompt-visible facts
- diagnostics live elsewhere and never become prompt context

For `find_backlinks`, diagnostics may include:

- `failure_code`
- `retryable`
- dropped candidate counts
- stale candidate counts

Those diagnostics are for host control logic, not model reasoning.

## 10. File Responsibilities

### 10.1 `backend/app/tools/registry.py`

- register the two new read-only tools
- extend schema validation for the new input shapes
- keep workflow scope limited to ask / ingest-compatible read paths as designed

### 10.2 `backend/app/tools/ask_tools.py`

- implement `get_note_outline`
- implement `find_backlinks`
- keep vault boundary enforcement local to tool execution

### 10.3 `backend/app/indexing/store.py`

- host the shared proposal persistence validator
- provide any helper queries needed for backlink discovery if not better placed elsewhere

### 10.4 `backend/app/services/resume_workflow.py`

- re-run static validation before accepting approval/writeback

### 10.5 `backend/app/contracts/workflow.py`

- extend patch op / tool result contract as needed
- keep backward compatibility as narrow as practical

### 10.6 `plugin/src/writeback/helpers.ts`

- add bounded helpers for `replace_section`
- add bounded helpers for `add_wikilink`
- keep shared heading-boundary logic centralized

### 10.7 `plugin/src/writeback/applyProposalWriteback.ts`

- validate and execute the new patch ops
- preserve existing `before_hash` and rollback guarantees

### 10.8 Tests

At minimum:

- `backend/tests/test_tool_registry.py`
- ask-tool execution tests
- proposal persistence validation tests
- ingest / digest proposal tests where patch plans are persisted
- `plugin/src/writeback/writeback.test.ts`

## 11. Testing Strategy

Implementation should follow TDD and progress in this order:

1. add failing tests for new tool registration and execution behavior
2. add failing tests for `replace_section`
3. add failing tests for `add_wikilink`
4. add failing tests for persistence-time static validation
5. add failing tests for resume-time revalidation

Critical assertions:

- `find_backlinks` never emits ambiguous or stale results as successful prompt facts
- `get_note_outline` returns current file structure
- existing patch ops keep working
- invalid proposals are rejected before inbox / approval
- resume rejects persisted proposals that violate the new validator

## 12. Acceptance Mapping

This design maps the task acceptance criteria as follows:

- `get_note_outline(path)`:
  satisfied by direct file parse + bounded structural return payload
- `find_backlinks(path)`:
  satisfied by indexed candidate discovery plus host-side verified-only success semantics
- `replace_section`:
  satisfied by exact heading-bounded section replacement with existing `before_hash` protection
- `add_wikilink`:
  satisfied by bounded heading-scoped link insertion to an existing note path
- static validation:
  satisfied by persistence-time and resume-time shared validation
- no regression:
  protected by explicit regression tests for existing tools and patch ops

## 13. Open Follow-Ups Outside This Task

The following remain intentionally outside `TASK-045`:

- plugin-side live backlink bridge into Obsidian metadata cache
- `max_changed_lines` becoming a strict per-op diff guard for `replace_section`
- config-driven threshold customization per vault
- multi-round ReAct control logic using structured tool diagnostics

Those can remain as later `small` follow-ups or future medium tasks.
