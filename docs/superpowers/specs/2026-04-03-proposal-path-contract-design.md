# Proposal Path Contract Design

**Problem**

The repository currently uses three different path semantics for note-targeted
workflow state:

- canonical-looking vault-relative paths such as `Digest/2026-03-14.md`
- filesystem absolute paths such as
  `/Users/qi/.../sample_vault/Digest/2026-03-14.md`
- historical pseudo-root paths such as `/vault/digest/daily.md`

Those semantics are mixed across proposal generation, static validation,
persistence, plugin writeback, runtime resume state, audit records, retrieval
evidence, and tests. As a result, a path can be accepted by one layer, rewritten
by another, or rejected by a third. The current `test_indexing_store` failures
are one symptom of that mismatch, not the root problem.

**Goal**

Establish one stable path contract for all persisted and cross-boundary note
references: every business path becomes vault-relative, while runtime adapters
translate between vault-relative paths and real filesystem paths only when file
access is needed.

**Non-Goals**

- Do not redesign patch op semantics beyond path normalization.
- Do not add new writeback operations.
- Do not leave `/vault/...` as a permanent accepted contract format.
- Do not keep multiple canonical path formats in storage.

**Recommended Approach**

Make vault-relative path strings the only canonical representation for all
proposal, writeback, audit, checkpoint, retrieval, and frontend-facing payloads.
Add one shared normalization layer on the backend and one matching adapter layer
in the plugin. New writes always normalize into vault-relative form before
validation and persistence. Historical `/vault/...` and vault-contained absolute
paths are migrated once into the canonical representation and are no longer
treated as normal input after the migration window closes.

**Alternatives Considered**

1. Use absolute filesystem paths as the canonical format.
   Rejected because contracts would become machine-specific and brittle across
   vault relocation, plugin execution, and persisted workflow state.
2. Keep accepting all path formats indefinitely.
   Rejected because every consumer would need to guess path meaning forever,
   preserving exactly the ambiguity that caused the current mismatch.
3. Fix only the failing tests and keep current mixed semantics.
   Rejected because the tests are exposing a real contract drift rather than an
   isolated fixture bug.

## 1. Canonical Contract

All cross-boundary note path fields must be stored and returned as
vault-relative strings.

Examples:

- canonical: `Digest/2026-03-14.md`
- canonical: `日常/2026-03-14.md`
- not canonical: `/Users/qi/.../sample_vault/Digest/2026-03-14.md`
- not canonical: `/vault/digest/daily.md`

Rules for canonical vault-relative paths:

- use `/` as the separator on every platform
- do not start with `/`
- do not contain `.` or `..` segments after normalization
- do not contain the vault root itself
- preserve note name casing as stored by the producer

This canonical form applies to at least the following business fields:

- `Proposal.target_note_path`
- `PatchOp.target_path`
- `ProposalEvidence.source_path`
- `WritebackResult.target_note_path`
- proposal-related paths embedded in persisted checkpoint state
- audit-log target paths
- retrieval / context / evidence `source_path` values returned to frontend code

All API payloads returned to the frontend must use vault-relative paths for
direct display and for stable proposal replay.

## 2. Runtime Path Model

The system should explicitly separate business path identity from filesystem
access.

Business layer:

- sees only vault-relative strings
- persists only vault-relative strings
- compares and renders only vault-relative strings

Runtime adapter layer:

- converts acceptable input into vault-relative strings
- resolves vault-relative strings into real filesystem paths when needed
- enforces "must stay inside current vault root" checks

That means the backend and plugin both need a small, focused path semantics
module, but their public contract remains the same.

## 3. Normalization Rules

Introduce one backend helper and one plugin helper with matching behavior.

Required operations:

1. `normalize_to_vault_relative(input, vault_root, legacy_mode=False)`
2. `resolve_vault_relative(input, vault_root)`
3. `is_vault_relative(input)`
4. path separator normalization

Accepted input in normal mode:

- already vault-relative paths
- absolute filesystem paths that resolve inside the configured vault root

Accepted input only in migration mode:

- historical `/vault/...` pseudo-root paths

Rejected input:

- empty paths
- absolute paths outside the vault root
- paths escaping the vault with `..`
- `/vault/...` values in normal runtime validation after migration is complete

Normalization outcomes:

- `Digest/2026-03-14.md` -> `Digest/2026-03-14.md`
- `/Users/qi/.../sample_vault/Digest/2026-03-14.md` -> `Digest/2026-03-14.md`
- `/vault/digest/daily.md` -> `digest/daily.md` in migration mode only

## 4. Producer and Consumer Changes

### 4.1 Backend producers

The following producers should emit canonical vault-relative values:

- `backend/app/services/digest.py`
- `backend/app/services/ingest_proposal.py`
- `backend/app/services/resume_workflow.py`
- any service composing retrieval/context/evidence objects

Services may still use real `Path` objects internally, but must normalize before
serializing into contracts.

### 4.2 Validation and persistence

`backend/app/services/proposal_validation.py` must stop behaving like a raw
string checker. It should:

1. normalize incoming paths
2. validate the normalized result
3. return or propagate canonical values for persistence

`backend/app/indexing/store.py` should persist normalized values rather than the
original caller-supplied string.

### 4.3 Plugin writeback

`plugin/src/writeback/applyProposalWriteback.ts` already supports both
vault-relative and absolute-in-vault inputs. After this refactor:

- vault-relative becomes the expected input
- absolute paths remain compatibility input
- `/vault/...` must not remain on the main execution path
- if legacy support is temporarily needed, it must be isolated in one migration
  or compatibility function, not spread through writeback logic

### 4.4 Retrieval and evidence paths

This refactor also normalizes retrieval-facing path fields so that:

- `ContextEvidenceItem.source_path`
- context bundle source note paths
- retrieval candidate paths exposed to frontend code

all use the same vault-relative semantics as proposal/writeback paths.

This avoids a split contract where proposal paths are canonical but evidence
paths remain absolute.

## 5. Data Migration

This design assumes a real migration, not read-time ambiguity forever.

Migration targets include persisted path-bearing records such as:

- proposal rows
- proposal evidence rows
- serialized patch op payloads where `target_path` appears
- audit log target paths
- serialized writeback results
- workflow checkpoint state blobs that embed proposal or writeback state
- any persisted retrieval/evidence payloads that surface path strings back to
  the UI

Migration rules:

- canonical vault-relative values remain unchanged apart from separator cleanup
- absolute paths inside the configured vault are rewritten to vault-relative
- `/vault/...` pseudo-root values are rewritten to vault-relative
- values that cannot be safely interpreted are reported and left fail-closed

The migration should produce an explicit report of changed rows and rejected
rows. Silent best-effort mutation is not acceptable for ambiguous values.

## 6. Testing Strategy

Testing should cover three layers.

Unit normalization tests:

- vault-relative input passes unchanged
- absolute-in-vault input normalizes correctly
- outside-vault absolute input is rejected
- `/vault/...` is accepted only in migration mode
- path traversal attempts are rejected

Contract and persistence tests:

- proposal persistence stores canonical vault-relative values even when given
  absolute-in-vault input
- validator rejects `/vault/...` in normal mode
- migration rewrites historical `/vault/...` and absolute path fixtures
- checkpoint and audit payloads round-trip with canonical paths

Integration tests:

- digest and ingest proposals emit vault-relative target paths
- plugin writeback executes canonical proposal paths successfully
- resume / rollback / pending inbox continue to work after migration
- retrieval/context/evidence payloads exposed to frontend code are canonical

Normal contract tests should stop using `/vault/...` fixtures. That format should
survive only in migration-specific tests.

## 7. Rollout Plan

Recommended rollout order:

1. add shared normalization helpers
2. update backend producers to emit canonical paths
3. update validation and persistence to normalize before storing
4. update plugin-side path handling to treat vault-relative as canonical
5. migrate historical persisted data
6. rewrite existing tests to canonical fixtures
7. add migration-specific regression tests
8. run full backend/plugin verification

The migration should happen before tightening validation to reject `/vault/...`
on normal runtime paths, otherwise old records will break resume flows.

## 8. Risks

- Partial rollout can create mixed canonical/non-canonical persisted data.
- Retrieval path normalization may affect tests and UI assumptions beyond
  proposal/writeback flows.
- Checkpoint state migration is easy to miss because paths may be nested inside
  serialized models.

## 9. Mitigations

- Centralize normalization in one helper per runtime instead of ad hoc callers.
- Add migration coverage for persisted checkpoint state, not just normalized SQL
  columns.
- Keep a temporary migration report and verification script until no `/vault/...`
  values remain.
- Treat vault-relative output to frontend as a hard contract and assert it in
  integration tests.

## 10. Expected End State

After the refactor:

- all new business payloads use vault-relative paths
- all frontend-visible path fields are vault-relative
- absolute filesystem paths are runtime-only implementation details
- `/vault/...` no longer appears in normal contracts
- historical `/vault/...` and absolute persisted values are migrated
- proposal, retrieval, context, audit, checkpoint, resume, and plugin writeback
  all agree on a single path meaning
