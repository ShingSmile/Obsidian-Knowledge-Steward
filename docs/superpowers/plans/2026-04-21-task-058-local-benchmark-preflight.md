# TASK-058 Local Benchmark Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-only preflight and provider pinning path so the `TASK-058` retrieval benchmark either runs against the local embedding baseline or fails before execution with an explicit operator-facing reason.

**Architecture:** Keep the benchmark runner contract intact, but insert a new local preflight module in front of the CLI and thread a strict local embedding target through the existing vector retrieval path. Split the work into four slices: strict local target plumbing, vector/hybrid pinning, preflight coverage checks, and thin CLI gating with regression verification.

**Tech Stack:** Python 3.12, existing retrieval helpers in `backend/app/retrieval/`, benchmark modules in `backend/app/benchmark/`, SQLite via `sqlite3`, temporary vault/DB fixtures, `unittest`, importlib-based CLI tests.

---

## Scope Check

Keep this as one implementation plan. The retrieval-layer hook, benchmark mode
pinning, preflight service, and CLI gating are all part of one local-only
benchmark readiness slice from the approved follow-up spec. Do not split it
further unless the spec changes.

This plan intentionally does **not** include:

- `TASK-059` answer-level provider benchmarking
- README or operator-doc updates
- automatic `ollama pull`
- automatic ingest or vector index repair
- cloud fallback during local benchmark runs
- governance doc sync in `docs/TASK_QUEUE.md`, `docs/CURRENT_STATE.md`, or
  `docs/SESSION_LOG.md`

## File Structure

### Create

- `backend/app/benchmark/ask_retrieval_preflight.py`
  - Structured local-only benchmark readiness checks and operator-facing status
    messages.
- `backend/tests/test_ask_retrieval_preflight.py`
  - Preflight status tests for missing local config, probe failure, partial
    coverage, and full coverage.
- `backend/tests/test_retrieval_embeddings.py`
  - Focused tests for exact local target resolution without fallback routing.

### Modify

- `backend/app/retrieval/embeddings.py`
  - Add one exact-target helper for strict provider selection without changing
    default runtime fallback order.
- `backend/app/retrieval/sqlite_vector.py`
  - Accept an explicit embedding target list and pass it to `embed_texts(...)`
    so benchmark callers can pin the vector path to local-only.
- `backend/app/benchmark/ask_retrieval_modes.py`
  - Resolve the strict local embedding target and pass it into `vector_only`
    and `hybrid_rrf`.
- `backend/tests/test_retrieval_vector.py`
  - Lock the new explicit-target forwarding behavior.
- `backend/tests/test_ask_retrieval_modes.py`
  - Lock local-target pinning and no-fallback behavior in benchmark adapters.
- `backend/tests/test_ask_retrieval_cli.py`
  - Lock CLI preflight failure behavior and “no artifact on preflight failure”.
- `eval/benchmark/run_retrieval_benchmark.py`
  - Run preflight before benchmark execution and print preflight failures to
    stderr.

### No Changes Expected

- `backend/app/benchmark/ask_retrieval_benchmark.py`
  - Keep the benchmark runner focused on dataset selection, mode execution, and
    artifact writing.
- `backend/app/benchmark/ask_retrieval_metrics.py`
  - Metrics stay unchanged.
- `eval/benchmark/ask_benchmark_cases.json`
  - Use the committed formal dataset without further schema or content changes.
- `eval/README.md`
  - Out of scope for this follow-up.

### Skills To Use During Execution

- `@using-git-worktrees` before Task 1 so implementation stays isolated from the
  dirty main worktree.
- `@test-driven-development` before every production edit.
- `@verification-before-completion` before any “done” claim or commit.
- `@requesting-code-review` after the implementation and verification stabilize.

## Implementation Tasks

### Task 1: Add strict local embedding target resolution

**Files:**
- Create: `backend/tests/test_retrieval_embeddings.py`
- Modify: `backend/app/retrieval/embeddings.py`

- [ ] **Step 1: Write the failing strict-target tests**

Add focused tests for the new exact-target helper instead of overloading vector
search tests with routing behavior.

Use concrete cases like:

```python
import unittest
from dataclasses import replace

from app.config import get_settings
from app.retrieval.embeddings import resolve_exact_embedding_provider_target


class RetrievalEmbeddingsTests(unittest.TestCase):
    def test_resolve_exact_local_target_ignores_default_provider_preference(self) -> None:
        settings = replace(
            get_settings(),
            default_model_provider="cloud",
            cloud_base_url="https://example.com",
            cloud_embedding_model="cloud-embed",
            local_base_url="http://127.0.0.1:11434",
            local_embedding_model="nomic-embed-text",
        )

        target = resolve_exact_embedding_provider_target(
            settings=settings,
            provider_key="local",
        )

        self.assertIsNotNone(target)
        self.assertEqual(target.provider_key, "local")
        self.assertEqual(target.model_name, "nomic-embed-text")

    def test_resolve_exact_local_target_returns_none_when_local_is_incomplete(self) -> None:
        settings = replace(
            get_settings(),
            local_base_url="http://127.0.0.1:11434",
            local_embedding_model="",
        )

        target = resolve_exact_embedding_provider_target(
            settings=settings,
            provider_key="local",
        )

        self.assertIsNone(target)
```

- [ ] **Step 2: Run the new routing tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_retrieval_embeddings -v
```

Expected: FAIL because `resolve_exact_embedding_provider_target(...)` does not
exist yet.

- [ ] **Step 3: Implement the exact-target helper in `embeddings.py`**

Add one small helper with no behavior change to default routing:

```python
def resolve_exact_embedding_provider_target(
    *,
    settings: Settings,
    provider_key: str,
) -> EmbeddingProviderTarget | None:
    normalized_provider_key = provider_key.strip().casefold()
    for target in resolve_embedding_provider_targets(
        settings=settings,
        provider_preference=provider_key,
    ):
        if target.provider_key == normalized_provider_key:
            return target
    return None
```

Then tighten it so it resolves from the concrete cloud/local config branches
without depending on `settings.default_model_provider`. The final version must:

- return the exact configured `local` target when local config is complete
- return the exact configured `cloud` target when cloud config is complete
- return `None` when that exact branch is incomplete
- preserve `resolve_embedding_provider_targets(...)` as-is for normal fallback
  routing

- [ ] **Step 4: Re-run the strict-target tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_retrieval_embeddings -v
```

Expected: PASS with exact local target resolution locked in.

- [ ] **Step 5: Commit the strict-target helper**

```bash
git add backend/app/retrieval/embeddings.py \
  backend/tests/test_retrieval_embeddings.py
git commit -m "feat: add strict embedding target resolution"
```

### Task 2: Thread the strict local target through vector and hybrid benchmark modes

**Files:**
- Modify: `backend/app/retrieval/sqlite_vector.py`
- Modify: `backend/app/benchmark/ask_retrieval_modes.py`
- Modify: `backend/tests/test_retrieval_vector.py`
- Modify: `backend/tests/test_ask_retrieval_modes.py`

- [ ] **Step 1: Write the failing vector-target forwarding tests**

Extend `backend/tests/test_retrieval_vector.py` with one test that proves
`search_chunk_vectors(...)` can accept an explicit target list and forwards it
to `embed_texts(...)`.

Use a tight mock-based test like:

```python
from unittest.mock import patch, sentinel

from app.config import get_settings
from app.retrieval.embeddings import EmbeddingBatchResult, EmbeddingProviderTarget
from app.retrieval.sqlite_vector import search_chunk_vectors


def test_search_chunk_vectors_forwards_explicit_provider_targets(self) -> None:
    connection = sentinel.connection
    settings = get_settings()
    target = EmbeddingProviderTarget(
        provider_key="local",
        provider_name="ollama",
        base_url="http://127.0.0.1:11434",
        model_name="nomic-embed-text",
    )
    with patch("app.retrieval.sqlite_vector.embed_texts") as mocked_embed:
        mocked_embed.return_value = EmbeddingBatchResult(
            embeddings=[[1.0, 0.0]],
            provider_key="local",
            provider_name="ollama",
            model_name="nomic-embed-text",
        )
        with patch(
            "app.retrieval.sqlite_vector._count_matching_embeddings",
            return_value=0,
        ):
            response = search_chunk_vectors(
                connection=connection,
                query="alpha question",
                settings=settings,
                provider_targets=[target],
            )
    self.assertTrue(response.disabled)
    self.assertEqual(mocked_embed.call_args.kwargs["provider_targets"], [target])
```

Extend `backend/tests/test_ask_retrieval_modes.py` with adapter tests that:

- patch `resolve_exact_embedding_provider_target(...)` to return a strict local
  target
- assert `vector_only` forwards `provider_targets=[local_target]`
- assert `hybrid_rrf` forwards `provider_targets=[local_target]` on its vector
  branch
- assert missing local target raises a benchmark error instead of falling back
  to cloud

- [ ] **Step 2: Run the targeted vector/adapter tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_retrieval_vector \
  backend.tests.test_ask_retrieval_modes -v
```

Expected: FAIL because `search_chunk_vectors(...)` does not accept explicit
provider targets and benchmark modes do not pin to local yet.

- [ ] **Step 3: Add the explicit-target plumbing**

Modify `backend/app/retrieval/sqlite_vector.py` so both
`search_chunk_vectors(...)` and `search_chunk_vectors_in_db(...)` accept a new
optional argument:

```python
provider_targets: Sequence[EmbeddingProviderTarget] | None = None
```

and forward it here:

```python
query_embedding_result = embed_texts(
    [normalized_query],
    settings=settings,
    provider_preference=provider_preference,
    provider_targets=provider_targets,
)
```

Then update `backend/app/benchmark/ask_retrieval_modes.py` to resolve the exact
local target once per mode dispatch:

```python
local_target = resolve_exact_embedding_provider_target(
    settings=settings,
    provider_key="local",
)
if local_target is None:
    raise RetrievalBenchmarkModeError(
        f"Retrieval mode {mode.value} is disabled: local_embedding_provider_not_configured"
    )
```

and pass `provider_targets=[local_target]` into every benchmark vector call.

Do **not** change the public behavior of non-benchmark callers.

- [ ] **Step 4: Re-run the vector/adapter tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_retrieval_vector \
  backend.tests.test_ask_retrieval_modes -v
```

Expected: PASS with local pinning locked in and no fallback-prone call path
remaining in benchmark adapters.

- [ ] **Step 5: Commit the local pinning slice**

```bash
git add backend/app/retrieval/sqlite_vector.py \
  backend/app/benchmark/ask_retrieval_modes.py \
  backend/tests/test_retrieval_vector.py \
  backend/tests/test_ask_retrieval_modes.py
git commit -m "feat: pin retrieval benchmark vector paths to local"
```

### Task 3: Add the benchmark preflight module with full-coverage index checks

**Files:**
- Create: `backend/app/benchmark/ask_retrieval_preflight.py`
- Create: `backend/tests/test_ask_retrieval_preflight.py`

- [ ] **Step 1: Write the failing preflight tests**

Create a dedicated test file that locks the four status outcomes from the spec:

- `provider_not_configured`
- `provider_unreachable_or_model_unavailable`
- `vector_index_not_ready`
- `ok`

Use temporary DB fixtures and one explicit partial-coverage case. A good pattern
is:

```python
with tempfile.TemporaryDirectory() as temp_dir:
    temp_root = Path(temp_dir)
    vault_path = temp_root / "vault"
    vault_path.mkdir()
    db_path = temp_root / "knowledge_steward.sqlite3"

    (vault_path / "Alpha.md").write_text(
        "# Alpha\n\nbody\n\n## Detail\n\nmore detail\n",
        encoding="utf-8",
    )
    fixture_settings = replace(
        get_settings(),
        cloud_base_url="",
        cloud_embedding_model="",
        local_base_url="",
        local_embedding_model="",
    )
    ingest_vault(
        vault_path=vault_path,
        db_path=db_path,
        settings=fixture_settings,
    )
```

Then patch the preflight probe:

```python
with patch(
    "app.benchmark.ask_retrieval_preflight.embed_texts",
    return_value=EmbeddingBatchResult(
        embeddings=[[1.0, 0.0]],
        provider_key="local",
        provider_name="ollama",
        model_name="nomic-embed-text",
    ),
):
    result = run_local_retrieval_preflight(settings=settings, db_path=db_path)
```

For the partial-coverage test, insert only one `chunk_embedding` row for a DB
that contains multiple `chunk` rows and assert `vector_index_not_ready`.

Use an explicit insert like:

```python
connection = sqlite3.connect(db_path)
connection.row_factory = sqlite3.Row
row = connection.execute(
    "SELECT chunk_id, note_id, content_hash FROM chunk ORDER BY ordinal ASC LIMIT 1;"
).fetchone()
connection.execute(
    """
    INSERT INTO chunk_embedding (
        chunk_id,
        note_id,
        provider_key,
        provider_name,
        model_name,
        embedding_dim,
        vector_norm,
        embedding_json,
        content_hash
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """,
    (
        row["chunk_id"],
        row["note_id"],
        "local",
        "ollama",
        "nomic-embed-text",
        2,
        1.0,
        "[1.0, 0.0]",
        row["content_hash"],
    ),
)
connection.commit()
connection.close()
```

- [ ] **Step 2: Run the preflight tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_retrieval_preflight -v
```

Expected: FAIL because the preflight module does not exist yet.

- [ ] **Step 3: Implement the preflight module**

Add a small structured result and one entrypoint:

```python
@dataclass(frozen=True)
class AskRetrievalPreflightResult:
    status: str
    provider_key: str | None
    provider_name: str | None
    model_name: str | None
    message: str


def run_local_retrieval_preflight(
    *,
    settings: Settings,
    db_path: Path | None = None,
) -> AskRetrievalPreflightResult:
    ...
```

Implementation rules:

- resolve the exact local target with
  `resolve_exact_embedding_provider_target(settings=settings, provider_key="local")`
- when `db_path` is `None`, default to `settings.index_db_path` so CLI and
  direct-call behavior inspect the same benchmark DB by default
- if target is missing, return `provider_not_configured`
- probe with:

```python
probe = embed_texts(
    ["task-058 benchmark preflight"],
    settings=settings,
    provider_targets=[local_target],
)
```

- if the probe is disabled, map it to
  `provider_unreachable_or_model_unavailable`
  and keep the message explicit enough to mention
  `<provider_name>/<model_name>`
- open the initialized DB with `initialize_index_db(...)` +
  `connect_sqlite(...)`
- compute:

```python
chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
embedding_count = connection.execute(
    \"\"\"
    SELECT COUNT(*)
    FROM chunk_embedding
    WHERE provider_key = ? AND model_name = ?;
    \"\"\",
    (local_target.provider_key, local_target.model_name),
).fetchone()[0]
```

- return `vector_index_not_ready` unless:
  - `chunk_count > 0`
  - `embedding_count == chunk_count`
- make the `vector_index_not_ready` message explicitly mention
  `<provider_name>/<model_name>` and instruct the operator to run ingest before
  benchmarking
- return `ok` only when full exact-provider/model coverage exists

Add explicit tests for both operator-facing messages:

- the probe-failure status should assert the message includes the resolved
  `provider_name/model_name`
- the partial-coverage status should assert the message includes the resolved
  `provider_name/model_name` and the ingest instruction

Keep the user-facing message formatting in this module so the CLI stays thin.

- [ ] **Step 4: Re-run the preflight tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_retrieval_preflight -v
```

Expected: PASS with the partial-coverage rule explicitly locked in.

- [ ] **Step 5: Commit the preflight slice**

```bash
git add backend/app/benchmark/ask_retrieval_preflight.py \
  backend/tests/test_ask_retrieval_preflight.py
git commit -m "feat: add local benchmark preflight"
```

### Task 4: Gate the CLI on preflight and re-run the benchmark regression suite

**Files:**
- Modify: `eval/benchmark/run_retrieval_benchmark.py`
- Modify: `backend/tests/test_ask_retrieval_cli.py`

- [ ] **Step 1: Write the failing CLI preflight tests**

Extend `backend/tests/test_ask_retrieval_cli.py` with two focused cases:

1. preflight failure:

```python
def test_main_returns_non_zero_and_skips_benchmark_when_preflight_fails(self) -> None:
    module = load_cli_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "retrieval-benchmark.json"
        with patch.object(
            module,
            "run_local_retrieval_preflight",
            return_value=AskRetrievalPreflightResult(
                status="provider_not_configured",
                provider_key=None,
                provider_name=None,
                model_name=None,
                message="Local embedding provider is not configured.",
            ),
        ):
            with patch.object(module, "run_ask_retrieval_benchmark") as mocked_runner:
                stderr_buffer = io.StringIO()
                with contextlib.redirect_stderr(stderr_buffer):
                    exit_code = module.main(["--output", str(output_path)])
        self.assertFalse(output_path.exists())
    self.assertEqual(exit_code, 1)
    mocked_runner.assert_not_called()
    self.assertIn("Local embedding provider is not configured.", stderr_buffer.getvalue())
```

2. preflight success:
   - assert the benchmark runner is called exactly as before

- [ ] **Step 2: Run the CLI tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_retrieval_cli -v
```

Expected: FAIL because the CLI does not import or call preflight yet.

- [ ] **Step 3: Integrate preflight into the CLI**

Modify `eval/benchmark/run_retrieval_benchmark.py` so `main(...)` does:

```python
settings = get_settings()
preflight = run_local_retrieval_preflight(
    settings=settings,
)
if preflight.status != "ok":
    print(f"ERROR: {preflight.message}", file=sys.stderr)
    return 1
```

Then keep the existing benchmark call unchanged:

```python
result = run_ask_retrieval_benchmark(
    settings=settings,
    dataset_path=args.dataset,
    output_path=args.output,
)
```

Do not write any artifact on preflight failure. Do not absorb preflight into the
benchmark runner.

- [ ] **Step 4: Re-run the CLI tests and then the full regression slice**

First run the CLI tests:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_retrieval_cli -v
```

Expected: PASS.

Then run the full targeted regression suite for this follow-up:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_retrieval_embeddings \
  backend.tests.test_retrieval_vector \
  backend.tests.test_ask_retrieval_modes \
  backend.tests.test_ask_retrieval_preflight \
  backend.tests.test_ask_retrieval_cli \
  backend.tests.test_ask_retrieval_metrics \
  backend.tests.test_ask_retrieval_benchmark -v
```

Expected: PASS with the local-only preflight layer added and no regression in
successful benchmark behavior.

- [ ] **Step 5: Commit the CLI gating slice**

```bash
git add eval/benchmark/run_retrieval_benchmark.py \
  backend/tests/test_ask_retrieval_cli.py
git commit -m "feat: gate retrieval benchmark on local preflight"
```

## Final Verification Checklist

- [ ] Run the full targeted regression suite from Task 4, Step 4 and confirm it
  passes on the implementation branch.
- [ ] Run the real CLI once on the current machine:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
./.conda/knowledge-steward/bin/python eval/benchmark/run_retrieval_benchmark.py \
  --output /tmp/task-058-local-benchmark.json
```

Expected:

- if local Ollama/model/index are not ready, exit `1` with one explicit
  preflight message and no output artifact
- if local Ollama/model/index are ready, benchmark proceeds into the existing
  retrieval runner and writes the artifact

- [ ] Use `@requesting-code-review` before declaring implementation complete.
