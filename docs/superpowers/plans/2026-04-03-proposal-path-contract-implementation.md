# Proposal Path Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Canonicalize all proposal, retrieval, evidence, checkpoint, and plugin writeback note paths to vault-relative strings while still accepting absolute in-vault input and migrating historical `/vault/...` data exactly once.

**Architecture:** Add one shared backend path-semantics helper and one matching plugin adapter, then move persistence boundaries to normalize into vault-relative strings before saving or returning payloads. Treat filesystem absolute paths as runtime-only data, add a schema-backed migration hook for legacy rows and checkpoint JSON, and update retrieval/tool/writeback consumers so every frontend-visible path is canonical.

**Tech Stack:** Python 3.12, Pydantic, SQLite, FastAPI, Obsidian TypeScript plugin, Node test runner, `unittest`, `npm test`.

---

## Scope Check

Keep this as one implementation plan. Backend persistence, retrieval output, checkpoint migration, and plugin writeback are not independent subsystems here; they are all enforcing the same path contract, and splitting them would create partial states that still leak mixed semantics.

## File Structure

### Create

- `backend/app/path_semantics.py`
  - Shared backend normalization and resolution helpers for vault-relative contract paths.
- `backend/tests/test_path_semantics.py`
  - Focused unit tests for relative, absolute-in-vault, traversal, and legacy `/vault/...` handling.
- `plugin/src/writeback/pathSemantics.ts`
  - Plugin-side path normalization and resolution logic aligned with the backend helper.
- `backend/tests/test_path_contract_migration.py`
  - Migration-specific coverage for legacy absolute and `/vault/...` rows, including checkpoint JSON payloads.

### Modify

- `backend/app/services/proposal_validation.py`
  - Normalize proposal, patch-op, and add-wikilink payload paths before validation and persistence.
- `backend/app/indexing/store.py`
  - Persist canonical values, migrate stored rows, and thread settings-aware migration hooks.
- `backend/app/indexing/ingest.py`
  - Store note index paths as vault-relative and accept absolute-in-vault scoped ingest inputs.
- `backend/app/retrieval/sqlite_fts.py`
  - Filter and return canonical note paths from FTS retrieval.
- `backend/app/retrieval/sqlite_vector.py`
  - Filter and return canonical note paths from vector retrieval.
- `backend/app/retrieval/hybrid.py`
  - Keep fused candidate ordering stable under canonical relative paths.
- `backend/app/tools/backlinks.py`
  - Resolve stored canonical note paths back to real files for freshness checks while returning canonical API payloads.
- `backend/app/tools/ask_tools.py`
  - Normalize tool inputs and guarantee frontend-visible path outputs stay vault-relative.
- `backend/app/services/ingest_proposal.py`
  - Emit canonical `target_note_path`, `patch_ops[].target_path`, `evidence[].source_path`, and analysis metadata paths.
- `backend/app/services/digest.py`
  - Keep digest proposal, evidence, and source note references canonical while resolving files only for hashing.
- `backend/app/services/ask.py`
  - Preserve canonical retrieval/citation paths across ask results and tool reentry checks.
- `backend/app/context/assembly.py`
  - Build evidence items from canonical retrieval and proposal paths.
- `backend/app/graphs/ingest_graph.py`
  - Persist scoped note lists and note metadata using canonical relative paths.
- `backend/app/graphs/checkpoint.py`
  - Support migrated checkpoint state and settings-aware DB initialization where needed.
- `backend/app/services/resume_workflow.py`
  - Accept absolute-in-vault writeback payloads, normalize them immediately, and persist canonical results.
- `backend/app/services/rollback_workflow.py`
  - Apply the same normalization rule to rollback payloads.
- `backend/app/main.py`
  - Keep pending-approval API payloads canonical after backend normalization.
- `backend/tests/test_proposal_validation.py`
  - Update validator expectations to canonical outputs and normal-mode rejection of `/vault/...`.
- `backend/tests/test_indexing_store.py`
  - Rewrite normal fixtures to vault-relative and verify persisted rows are canonical.
- `backend/tests/test_indexing_ingest.py`
  - Update note-row expectations from absolute to vault-relative.
- `backend/tests/test_retrieval_fts.py`
  - Update path-prefix filters and retrieval assertions to vault-relative values.
- `backend/tests/test_ingest_workflow.py`
  - Assert ingest proposal, evidence, related candidates, inbox items, and analysis metadata use canonical paths.
- `backend/tests/test_digest_workflow.py`
  - Assert digest proposals and waiting-approval payloads use canonical paths.
- `backend/tests/test_ask_workflow.py`
  - Replace `/vault/...` candidate fixtures with canonical paths and keep citation ordering intact.
- `backend/tests/test_tool_registry.py`
  - Assert `find_backlinks` and other tool outputs return canonical paths.
- `backend/tests/test_resume_workflow.py`
  - Keep scoped sync and audit behavior correct under canonical stored note paths.
- `plugin/src/writeback/applyProposalWriteback.ts`
  - Resolve canonical contract paths for target notes and compatibility absolute inputs.
- `plugin/src/writeback/writeback.test.ts`
  - Add path normalization coverage and reject `/vault/...` on the normal execution path.

### No Changes Expected

- `backend/app/contracts/workflow.py`
  - Path field names stay the same; only semantics and normalization behavior change.
- `plugin/src/views/KnowledgeStewardView.ts`
  - Existing rendering should work once backend/plugin inputs are canonical.

### Skills To Use During Execution

- `@test-driven-development` before every production edit.
- `@verification-before-completion` before any “done” claim or commit.
- `@requesting-code-review` after implementation and verification stabilize.

## Implementation Tasks

### Task 1: Add the shared backend path-semantics foundation

**Files:**
- Create: `backend/app/path_semantics.py`
- Create: `backend/tests/test_path_semantics.py`

- [ ] **Step 1: Write the failing backend path-semantics tests**

```python
import tempfile
import unittest
from pathlib import Path

from app.path_semantics import (
    PathContractError,
    is_vault_relative,
    normalize_to_vault_relative,
    resolve_vault_relative,
)


class VaultPathSemanticsTests(unittest.TestCase):
    def test_normalize_to_vault_relative_accepts_relative_and_absolute_in_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()
            note_path = vault_root / "Daily" / "2026-03-14.md"
            note_path.parent.mkdir()
            note_path.write_text("# Daily\n", encoding="utf-8")

            self.assertEqual(
                normalize_to_vault_relative("Daily/2026-03-14.md", vault_root=vault_root),
                "Daily/2026-03-14.md",
            )
            self.assertEqual(
                normalize_to_vault_relative(str(note_path.resolve()), vault_root=vault_root),
                "Daily/2026-03-14.md",
            )

    def test_normal_mode_rejects_legacy_vault_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()
            with self.assertRaises(PathContractError):
                normalize_to_vault_relative("/vault/Daily/2026-03-14.md", vault_root=vault_root)

    def test_migration_mode_accepts_legacy_vault_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()
            self.assertEqual(
                normalize_to_vault_relative(
                    "/vault/Daily/2026-03-14.md",
                    vault_root=vault_root,
                    legacy_mode=True,
                ),
                "Daily/2026-03-14.md",
            )
```

- [ ] **Step 2: Run the new path-semantics tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_path_semantics -v
```

Expected: FAIL with `ModuleNotFoundError` or missing symbol errors because `app.path_semantics` does not exist yet.

- [ ] **Step 3: Implement the minimal backend helper**

Create `backend/app/path_semantics.py` with one focused error type and four public helpers:

```python
class PathContractError(ValueError):
    pass


def normalize_to_vault_relative(
    raw_path: str | Path,
    *,
    vault_root: Path,
    legacy_mode: bool = False,
) -> str: ...


def resolve_vault_relative(raw_path: str, *, vault_root: Path) -> Path: ...


def is_vault_relative(raw_path: str) -> bool: ...


def normalize_path_separators(raw_path: str) -> str: ...
```

Implementation rules:

- normalize separators to `/`
- reject empty values
- reject `.` / `..` escape attempts after normalization
- accept real absolute paths only when they resolve inside `vault_root`
- accept `/vault/...` only when `legacy_mode=True`
- always return canonical strings without a leading slash

- [ ] **Step 4: Re-run the backend path-semantics tests and make them pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_path_semantics -v
```

Expected: PASS for relative, absolute-in-vault, traversal rejection, and legacy-mode-only handling.

- [ ] **Step 5: Commit the backend foundation**

```bash
git add backend/app/path_semantics.py backend/tests/test_path_semantics.py
git commit -m "feat: add vault-relative path semantics"
```

### Task 2: Canonicalize proposal persistence and workflow writeback payloads

**Files:**
- Modify: `backend/app/services/proposal_validation.py`
- Modify: `backend/app/indexing/store.py`
- Modify: `backend/app/services/resume_workflow.py`
- Modify: `backend/app/services/rollback_workflow.py`
- Modify: `backend/tests/test_proposal_validation.py`
- Modify: `backend/tests/test_indexing_store.py`
- Modify: `backend/tests/test_resume_workflow.py`

- [ ] **Step 1: Write the failing proposal canonicalization tests**

Add targeted cases such as:

```python
def test_save_proposal_canonicalizes_absolute_paths_before_insert(self) -> None:
    proposal = self._build_proposal(
        target_note_path=(vault_path / "Digest" / "2026-03-14.md").resolve(),
        patch_ops=[
            PatchOp(
                op="add_wikilink",
                target_path=str((vault_path / "Digest" / "2026-03-14.md").resolve()),
                payload={
                    "heading": "## Links",
                    "linked_note_path": str((vault_path / "Notes" / "Alpha.md").resolve()),
                },
            )
        ],
    )

    save_proposal(connection, thread_id="thread", proposal=proposal, approval_required=True)
    persisted = load_proposal(connection, proposal_id=proposal.proposal_id)

    self.assertEqual(persisted.proposal.target_note_path, "Digest/2026-03-14.md")
    self.assertEqual(persisted.proposal.patch_ops[0].target_path, "Digest/2026-03-14.md")
    self.assertEqual(
        persisted.proposal.patch_ops[0].payload["linked_note_path"],
        "Notes/Alpha.md",
    )


def test_validate_proposal_for_persistence_rejects_legacy_vault_prefix_in_normal_mode(self) -> None:
    proposal = self._build_proposal(target_note_path="/vault/Digest/2026-03-14.md")
    with self.assertRaisesRegex(ProposalValidationError, "proposal.target_note_path"):
        validate_proposal_for_persistence(proposal, settings=settings)
```

Also add resume/rollback coverage proving absolute-in-vault `writeback_result.target_note_path` is accepted but stored and compared as the proposal’s canonical relative path.

- [ ] **Step 2: Run the targeted proposal and persistence tests to confirm failure**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_proposal_validation \
  tests.test_indexing_store \
  tests.test_resume_workflow \
  -v
```

Expected: FAIL because validator only checks strings against the vault root and `save_proposal_record()` still persists caller-supplied raw paths.

- [ ] **Step 3: Implement minimal normalization at the persistence boundary**

In `backend/app/services/proposal_validation.py`, introduce a proposal-normalization entry point:

```python
def normalize_proposal_for_persistence(
    proposal: Proposal,
    *,
    settings: Settings,
    content_limit: int = 2000,
) -> Proposal:
    normalized_target = normalize_to_vault_relative(...)
    normalized_evidence = [...]
    normalized_patch_ops = [...]
    return proposal.model_copy(
        update={
            "target_note_path": normalized_target,
            "evidence": normalized_evidence,
            "patch_ops": normalized_patch_ops,
        }
    )
```

Requirements:

- normalize `proposal.target_note_path`
- normalize every `patch_ops[].target_path`
- normalize `add_wikilink.payload.linked_note_path`
- normalize `evidence[].source_path`
- keep `validate_proposal_for_persistence()` as the thin validator wrapper around the normalized copy

Then update `backend/app/indexing/store.py`:

```python
normalized_proposal = normalize_proposal_for_persistence(proposal, settings=effective_settings)
proposal_params["target_note_path"] = normalized_proposal.target_note_path
```

Use the normalized proposal object for proposal rows, evidence rows, and patch-op rows.

Update `resume_workflow.py` and `rollback_workflow.py` so any incoming `WritebackResult.target_note_path` is normalized immediately and then compared to `proposal.target_note_path`.

- [ ] **Step 4: Re-run the targeted proposal and persistence tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_proposal_validation \
  tests.test_indexing_store \
  tests.test_resume_workflow \
  -v
```

Expected: PASS, including the previously failing `test_indexing_store` cases once their normal-mode fixtures are converted to canonical relative paths.

- [ ] **Step 5: Commit proposal persistence normalization**

```bash
git add \
  backend/app/services/proposal_validation.py \
  backend/app/indexing/store.py \
  backend/app/services/resume_workflow.py \
  backend/app/services/rollback_workflow.py \
  backend/tests/test_proposal_validation.py \
  backend/tests/test_indexing_store.py \
  backend/tests/test_resume_workflow.py
git commit -m "feat: canonicalize proposal persistence paths"
```

### Task 3: Move note indexing and retrieval to canonical vault-relative storage

**Files:**
- Modify: `backend/app/indexing/store.py`
- Modify: `backend/app/indexing/ingest.py`
- Modify: `backend/app/retrieval/sqlite_fts.py`
- Modify: `backend/app/retrieval/sqlite_vector.py`
- Modify: `backend/app/retrieval/hybrid.py`
- Modify: `backend/app/tools/backlinks.py`
- Modify: `backend/tests/test_indexing_ingest.py`
- Modify: `backend/tests/test_retrieval_fts.py`
- Modify: `backend/tests/test_tool_registry.py`

- [ ] **Step 1: Write the failing note-index and retrieval contract tests**

Add or update tests like:

```python
def test_build_note_record_stores_vault_relative_path(self) -> None:
    note_record = build_note_record(alpha_path, parsed_note, vault_root=vault_path)
    self.assertEqual(note_record.path, "Alpha.md")


def test_search_chunks_supports_vault_relative_path_prefix_filter(self) -> None:
    response = search_chunks_in_db(
        db_path,
        "Plan",
        metadata_filter=RetrievalMetadataFilter(path_prefixes=["Alpha/"]),
    )
    self.assertEqual(response.candidates[0].path, "Alpha/Alpha.md")


def test_find_backlinks_returns_vault_relative_paths(self) -> None:
    self.assertEqual(result.data["target_path"], "Target.md")
    self.assertEqual(result.data["backlinks"][0]["source_path"], "Source.md")
```

- [ ] **Step 2: Run the indexing, retrieval, and tool tests and confirm failure**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_indexing_ingest \
  tests.test_retrieval_fts \
  tests.test_tool_registry \
  -v
```

Expected: FAIL because `build_note_record()` still stores absolute paths, retrieval filters still expect absolute prefixes, and backlinks still return absolute filesystem strings.

- [ ] **Step 3: Implement minimal canonical note-path storage**

Update `backend/app/indexing/store.py` and `backend/app/indexing/ingest.py`:

```python
def normalize_note_path(note_path: Path, *, vault_root: Path) -> str:
    return normalize_to_vault_relative(note_path, vault_root=vault_root)


def build_note_record(
    note_path: Path,
    parsed_note: ParsedNote,
    *,
    vault_root: Path,
) -> NoteRecord: ...
```

Then thread `vault_root` from `ingest_vault()` into `build_note_record()`.

Update scoped ingest resolution in `backend/app/indexing/ingest.py` to:

- accept canonical relative input
- accept absolute-in-vault input
- reject `/vault/...` in normal mode
- resolve back to a real `Path` only after canonicalization

Update retrieval and backlinks:

- keep `note.path` stored as vault-relative in `note` rows
- keep SQL filtering on `note.path`, but now with canonical prefixes
- when freshness checks need a real file path, call `resolve_vault_relative(...)`
- return `RetrievedChunkCandidate.path`, tool `target_path`, and backlink `source_path` as canonical relative values

- [ ] **Step 4: Re-run the indexing, retrieval, and tool tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_indexing_ingest \
  tests.test_retrieval_fts \
  tests.test_tool_registry \
  -v
```

Expected: PASS, with note rows, path-prefix filters, and backlink payloads all using vault-relative values.

- [ ] **Step 5: Commit canonical note index storage**

```bash
git add \
  backend/app/indexing/store.py \
  backend/app/indexing/ingest.py \
  backend/app/retrieval/sqlite_fts.py \
  backend/app/retrieval/sqlite_vector.py \
  backend/app/retrieval/hybrid.py \
  backend/app/tools/backlinks.py \
  backend/tests/test_indexing_ingest.py \
  backend/tests/test_retrieval_fts.py \
  backend/tests/test_tool_registry.py
git commit -m "feat: store indexed note paths as vault-relative"
```

### Task 4: Add the path-contract migration hook and checkpoint JSON rewrite

**Files:**
- Create: `backend/tests/test_path_contract_migration.py`
- Modify: `backend/app/indexing/store.py`
- Modify: `backend/app/graphs/checkpoint.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/resume_workflow.py`
- Modify: `backend/app/services/rollback_workflow.py`
- Modify: `backend/app/tools/ask_tools.py`

- [ ] **Step 1: Write the failing migration regression tests**

Create migration-specific coverage that inserts raw legacy rows directly and then initializes the DB:

```python
def test_initialize_index_db_migrates_legacy_absolute_and_pseudo_root_paths(self) -> None:
    settings = replace(get_settings(), sample_vault_dir=vault_path)
    _insert_raw_legacy_rows(
        connection,
        proposal_target="/vault/Daily/2026-03-14.md",
        note_path=str((vault_path / "Alpha.md").resolve()),
        checkpoint_state={
            "proposal": {"target_note_path": str((vault_path / "Digest.md").resolve())},
            "writeback_result": {"target_note_path": "/vault/Digest.md"},
        },
    )

    initialize_index_db(db_path, settings=settings)

    self.assertEqual(_load_proposal_target(connection), "Daily/2026-03-14.md")
    self.assertEqual(_load_note_path(connection), "Alpha.md")
    self.assertEqual(_load_checkpoint_target(connection), "Digest.md")
```

Also assert that ambiguous or outside-vault values fail closed instead of being silently rewritten.

- [ ] **Step 2: Run the migration tests and confirm failure**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_path_contract_migration -v
```

Expected: FAIL because there is no migration hook yet and `initialize_index_db()` cannot rewrite existing path-bearing rows or checkpoint JSON.

- [ ] **Step 3: Implement a settings-aware path migration hook**

In `backend/app/indexing/store.py`:

- bump `SCHEMA_VERSION` to `8`
- add `MIGRATIONS[8]` for any lightweight SQL scaffolding needed for the new version marker
- allow `initialize_index_db()` and `_apply_migrations()` to accept `settings: Settings | None = None`
- add a Python post-migration hook for version `8`

Suggested structure:

```python
POST_MIGRATION_HOOKS = {
    8: _migrate_path_contract_rows,
}


def initialize_index_db(db_path: Path, *, settings: Settings | None = None) -> Path: ...
```

Inside `_migrate_path_contract_rows(connection, settings)`:

- rewrite `note.path`
- rewrite `proposal.target_note_path`
- rewrite `proposal_evidence.source_path`
- rewrite `patch_op.target_path`
- rewrite `audit_log.target_note_path`
- rewrite embedded JSON in `writeback_result_json`, `applied_patch_ops_json`, and `state_json`
- rebuild `chunk_fts` after note-path rewrites
- emit deterministic counts for changed and rejected rows

Use `legacy_mode=True` only inside this migration hook.

Update `backend/app/graphs/checkpoint.py`, `backend/app/main.py`, and any service entry points that already have `settings` in scope so they pass `settings=settings` into `initialize_index_db(...)`.

- [ ] **Step 4: Re-run the migration tests and the persistence smoke tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_path_contract_migration \
  tests.test_indexing_store \
  tests.test_resume_workflow \
  -v
```

Expected: PASS, including migrated checkpoint state and rewritten audit/writeback JSON payloads.

- [ ] **Step 5: Commit the migration layer**

```bash
git add \
  backend/app/indexing/store.py \
  backend/app/graphs/checkpoint.py \
  backend/app/main.py \
  backend/app/services/resume_workflow.py \
  backend/app/services/rollback_workflow.py \
  backend/app/tools/ask_tools.py \
  backend/tests/test_path_contract_migration.py
git commit -m "feat: migrate stored workflow paths to vault-relative"
```

### Task 5: Normalize workflow producers, ask context, and frontend-visible API payloads

**Files:**
- Modify: `backend/app/services/ingest_proposal.py`
- Modify: `backend/app/services/digest.py`
- Modify: `backend/app/context/assembly.py`
- Modify: `backend/app/services/ask.py`
- Modify: `backend/app/graphs/ingest_graph.py`
- Modify: `backend/tests/test_ingest_workflow.py`
- Modify: `backend/tests/test_digest_workflow.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write the failing workflow contract tests**

Add or update targeted assertions like:

```python
def test_invoke_workflow_returns_vault_relative_ingest_proposal_paths(self) -> None:
    self.assertEqual(result.proposal.target_note_path, "Alpha.md")
    self.assertEqual(result.proposal.patch_ops[0].target_path, "Alpha.md")
    self.assertTrue(any(evidence.source_path == "Beta.md" for evidence in result.proposal.evidence))


def test_digest_waiting_proposal_uses_vault_relative_target_note_path(self) -> None:
    self.assertEqual(result.proposal.target_note_path, "2026-03-14.md")


def test_ask_workflow_emits_canonical_retrieval_and_citation_paths(self) -> None:
    self.assertEqual(result.retrieved_candidates[0].path, "roadmap/Roadmap.md")
    self.assertEqual(result.citations[0].path, "roadmap/Roadmap.md")
```

Replace existing `/vault/...` manual fixtures with canonical values like `alpha/Roadmap.md`, `second/Second.md`, and `Filtered.md`.

- [ ] **Step 2: Run the workflow-facing tests and confirm failure**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ingest_workflow \
  tests.test_digest_workflow \
  tests.test_ask_workflow \
  -v
```

Expected: FAIL because ingest proposal builders, digest evidence, graph state note-path lists, and several ask fixtures still assume absolute or `/vault/...` semantics.

- [ ] **Step 3: Implement canonical producer and API behavior**

Update `backend/app/services/ingest_proposal.py`:

- canonicalize incoming scoped note paths as early as possible
- resolve to real `Path` objects only when reading markdown or hashing files
- emit canonical `target_note_path`, `patch_ops[].target_path`, `evidence[].source_path`, and `analysis_result.source_paths`

Update `backend/app/services/digest.py`:

- keep `DigestSourceNote.path` and proposal evidence canonical
- use `resolve_vault_relative(target_note.path, vault_root=settings.sample_vault_dir)` when computing `before_hash`

Update `backend/app/graphs/ingest_graph.py`:

- persist canonical relative `note_paths` in graph state
- keep `note_meta["requested_note_paths"]`, `note_meta["target_note_path"]`, and `related_candidate_paths` canonical

Update `backend/app/context/assembly.py` and `backend/app/services/ask.py`:

- keep `ContextEvidenceItem.source_path`, `RetrievedChunkCandidate.path`, and `AskCitation.path` canonical
- preserve current prompt-order and duplicate-collision behavior after the contract change

- [ ] **Step 4: Re-run the workflow-facing tests**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ingest_workflow \
  tests.test_digest_workflow \
  tests.test_ask_workflow \
  -v
```

Expected: PASS, with all workflow and ask payloads using vault-relative paths.

- [ ] **Step 5: Commit the producer and API contract changes**

```bash
git add \
  backend/app/services/ingest_proposal.py \
  backend/app/services/digest.py \
  backend/app/context/assembly.py \
  backend/app/services/ask.py \
  backend/app/graphs/ingest_graph.py \
  backend/tests/test_ingest_workflow.py \
  backend/tests/test_digest_workflow.py \
  backend/tests/test_ask_workflow.py
git commit -m "feat: normalize workflow payload paths"
```

### Task 6: Add the plugin path adapter and finish legacy fixture cleanup

**Files:**
- Create: `plugin/src/writeback/pathSemantics.ts`
- Modify: `plugin/src/writeback/applyProposalWriteback.ts`
- Modify: `plugin/src/writeback/writeback.test.ts`
- Modify: `backend/tests/test_indexing_store.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write the failing plugin adapter tests**

Extend `plugin/src/writeback/writeback.test.ts` with cases like:

```ts
test("normalizeToVaultRelative keeps canonical relative targets unchanged", () => {
  assert.equal(
    normalizeToVaultRelative("Daily/2026-03-14.md", { vaultBasePath: "/tmp/vault" }),
    "Daily/2026-03-14.md"
  );
});

test("normalizeToVaultRelative accepts absolute paths inside the current vault", () => {
  assert.equal(
    normalizeToVaultRelative("/tmp/vault/Daily/2026-03-14.md", { vaultBasePath: "/tmp/vault" }),
    "Daily/2026-03-14.md"
  );
});

test("normalizeToVaultRelative rejects legacy pseudo-root paths on the main execution path", () => {
  assert.throws(
    () => normalizeToVaultRelative("/vault/Daily/2026-03-14.md", { vaultBasePath: "/tmp/vault" }),
    /legacy/i
  );
});
```

- [ ] **Step 2: Run the plugin tests and confirm failure**

Run from `plugin/`:

```bash
npm test
```

Expected: FAIL because no plugin path adapter exists yet and `applyProposalWriteback.ts` still resolves absolute paths inline.

- [ ] **Step 3: Implement the plugin-side path adapter and wire it into writeback**

Create `plugin/src/writeback/pathSemantics.ts` with helpers mirroring the backend rules:

```ts
export class PathContractError extends Error {}

export function normalizeToVaultRelative(
  rawPath: string,
  options: { vaultBasePath: string; legacyMode?: boolean }
): string { ... }

export function resolveContractPath(
  app: App,
  rawPath: string,
  options?: { legacyMode?: boolean }
): string { ... }
```

Then update `plugin/src/writeback/applyProposalWriteback.ts`:

- replace inline absolute-path logic with the new adapter
- canonicalize `proposal.target_note_path`
- canonicalize every `patchOp.target_path` before single-note enforcement
- canonicalize `linked_note_path` compatibility inputs before file lookup
- keep `/vault/...` rejected in normal execution

At the same time, finish the remaining normal-mode fixture rewrite in backend tests so `/vault/...` survives only in `test_path_contract_migration.py`.

- [ ] **Step 4: Re-run plugin tests and do a last legacy-fixture scan**

Run from `plugin/`:

```bash
npm test
```

Run from repo root:

```bash
rg -n "\"/vault/|'/vault/" backend/tests plugin/src
```

Expected:

- plugin tests PASS
- remaining `/vault/...` matches appear only in migration-specific backend tests or spec/docs text, not in normal runtime tests

- [ ] **Step 5: Commit plugin normalization and fixture cleanup**

```bash
git add \
  plugin/src/writeback/pathSemantics.ts \
  plugin/src/writeback/applyProposalWriteback.ts \
  plugin/src/writeback/writeback.test.ts \
  backend/tests/test_indexing_store.py \
  backend/tests/test_ask_workflow.py
git commit -m "feat: align plugin writeback with vault-relative paths"
```

## Verification Checklist

- [ ] Run the focused backend suites:

```bash
cd backend
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_path_semantics \
  tests.test_proposal_validation \
  tests.test_indexing_store \
  tests.test_indexing_ingest \
  tests.test_path_contract_migration \
  tests.test_retrieval_fts \
  tests.test_tool_registry \
  tests.test_ingest_workflow \
  tests.test_digest_workflow \
  tests.test_ask_workflow \
  tests.test_resume_workflow \
  -v
```

- [ ] Run the full backend suite:

```bash
cd backend
../.conda/knowledge-steward/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

- [ ] Run the plugin suite:

```bash
cd plugin
npm test
```

- [ ] Build the plugin bundle once after tests pass:

```bash
cd plugin
npm run build
```

- [ ] Sanity-check the repository for remaining runtime `/vault/...` fixtures:

```bash
rg -n "\"/vault/|'/vault/" backend plugin
```

Expected: runtime code has no normal-mode `/vault/...` acceptance path, and remaining hits are migration-only tests or documentation.

- [ ] Request code review before merge:

```text
Use @requesting-code-review after all verification commands pass.
```
