# TASK-058 Local Benchmark Preflight Design

**Task:** `TASK-058`

**Session:** `SES-20260420-01`

**Problem**

`TASK-058` has already landed the retrieval-only benchmark runner, the fixed
`50`-case formal dataset is now committed, and the benchmark can select the
expected `38` headline cases. The remaining blocker is operational rather than
metric-related: `vector_only` currently fails with
`no_available_embedding_provider`, so the benchmark stops before it can produce
headline retrieval numbers.

The current codebase already contains a dual-provider embedding abstraction in
[backend/app/retrieval/embeddings.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/embeddings.py)
and environment-driven configuration in
[backend/app/config.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/config.py).
What is missing is a benchmark-facing startup contract that can answer the
practical questions before a run starts:

- is a local embedding provider configured?
- is the local embedding provider reachable?
- is the local embedding model usable?
- is the vector index ready for that exact local provider/model?

Without that preflight layer, the benchmark fails late and opaquely after
already beginning execution. That is the wrong operator experience for the
local-baseline phase of `TASK-058`.

**Goal**

Add a local-only benchmark preflight path for `TASK-058` that:

- treats the benchmark as a strict local-provider run
- checks local embedding readiness before benchmark execution starts
- fails early with explicit, actionable messages
- refuses to auto-pull models or auto-build vector indexes
- keeps the existing retrieval metric contract unchanged

**Non-Goals**

- Do not change the `TASK-058` metric panel or dataset subset.
- Do not add README or operator-doc changes in this follow-up.
- Do not add a separate standalone preflight command.
- Do not auto-run ingest, auto-build embeddings, or auto-pull Ollama models.
- Do not allow silent fallback from local to cloud during this benchmark mode.
- Do not broaden this work into `TASK-059` real-provider answer benchmarking.

**Approaches Considered**

1. Reuse the current environment-driven provider configuration and add an
   integrated benchmark preflight.
   Recommended because it keeps the operator surface small and consistent with
   the rest of the retrieval stack.
2. Add a new benchmark-only provider CLI interface.
   Rejected because it expands the runtime contract more than needed for the
   current goal.
3. Add a provider-specific bootstrap workflow that knows about Ollama model
   management.
   Rejected because it turns `TASK-058` into a local tooling task instead of a
   benchmark task.

**Recommended Approach**

Keep the existing environment-driven settings model, but make
[eval/benchmark/run_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_retrieval_benchmark.py)
run a local-only readiness check before it calls the benchmark runner.

That readiness check should:

1. resolve a strict local embedding target
2. probe that exact local target with a minimal embedding request
3. verify that the benchmark database already contains chunk embeddings for that
   exact provider/model pair
4. stop immediately with a clear error if any step fails

If preflight passes, the benchmark should then execute `vector_only` and
`hybrid_rrf` under the same local-only provider pin. No cloud fallback is
allowed anywhere in this benchmark path.

## 1. Scope And Boundary

This design is a follow-up to the already approved
[2026-04-19-task-058-ask-retrieval-benchmark-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-19-task-058-ask-retrieval-benchmark-design.md).
It does not replace that document. It narrows one operational gap that was
exposed after the runner and dataset were integrated on `main`.

The scope of this follow-up is limited to:

- local-only embedding readiness checks for the retrieval benchmark CLI
- local-only provider pinning for benchmark vector retrieval
- explicit preflight failure semantics
- focused tests around preflight and CLI gating

This follow-up does not change:

- the headline case subset
- strict locator matching
- `Recall@5`, `Recall@10`, `NDCG@10`
- result artifact shape for successful runs
- fail-closed semantics for mode failures after benchmark execution begins

The new behavior should stop bad runs earlier. It should not redefine what a
successful benchmark means.

## 2. Local-Only Provider Semantics

For this phase, the benchmark must be treated as a strict local-baseline run.

That means:

- preflight checks only the local embedding provider
- `vector_only` retrieval only uses the local embedding provider
- `hybrid_rrf` only uses the local embedding provider for its vector branch
- local failure ends the run immediately
- cloud is never used as a fallback for this benchmark mode

This requirement is important because the current embedding routing semantics are
not strict enough on their own. Today, a plain
`provider_preference="local"` still preserves ordered fallback behavior. That is
acceptable for general product runtime resilience, but it is not acceptable for
benchmarking because it would make the resulting numbers ambiguous.

The benchmark needs a clean statement:

- these numbers were produced with the local embedding baseline

That statement becomes invalid if the benchmark can silently fall through to
cloud.

## 3. Component Layout

### 3.1 Preflight Module

Add a dedicated module:

- `backend/app/benchmark/ask_retrieval_preflight.py`

This module should be responsible only for benchmark startup readiness checks.

It should:

- resolve the local embedding target
- issue a minimal embedding probe against that target
- inspect the benchmark DB for matching chunk embeddings
- return a small structured preflight result

It should not:

- write artifacts
- execute benchmark modes
- mutate the dataset
- run ingest
- pull models

### 3.2 Strict Local Target Resolution

The current public retrieval surface does not expose a clean way to guarantee
`local-only` embedding use without reusing fallback-prone routing. This follow-up
should therefore add a small, non-breaking hook in the retrieval layer so the
benchmark can request a strict local target without duplicating vector-search
internals.

The exact implementation can vary, but the public shape should support this
behavior:

- resolve exactly one embedding target by provider key
- return `None` when that exact target is not configured
- allow `embed_texts(...)` or vector retrieval to run against that explicit
  target list instead of the default fallback order

The benchmark path should use that strict target selection. General ask/runtime
behavior should remain unchanged.

### 3.3 Vector Retrieval Pinning

[backend/app/benchmark/ask_retrieval_modes.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_retrieval_modes.py)
should be updated so `vector_only` and `hybrid_rrf` explicitly run with the
strict local embedding target.

This can be implemented as one of:

- extending [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py)
  with a non-breaking explicit target override
- or another similarly focused hook that avoids duplicating vector query logic

What is not acceptable is leaving benchmark execution on the fallback-prone
default provider order.

### 3.4 CLI Integration

[eval/benchmark/run_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/run_retrieval_benchmark.py)
should remain a thin CLI, but it should gain one startup step:

1. parse CLI args
2. load `Settings`
3. run local benchmark preflight
4. if preflight fails:
   - print the preflight message to stderr
   - return exit code `1`
   - do not call the benchmark runner
   - do not write a benchmark artifact
5. if preflight passes:
   - call the existing retrieval benchmark runner
   - preserve the existing success/failure exit semantics

The benchmark runner itself should stay focused on case selection, mode
execution, aggregation, and artifact writing.

## 4. Preflight Contract

Preflight should return a small structured result instead of scattering raw
exceptions through the CLI.

The result should include at least:

- `status`
- `provider_key`
- `provider_name`
- `model_name`
- `message`

Allowed `status` values:

- `ok`
- `provider_not_configured`
- `provider_unreachable_or_model_unavailable`
- `vector_index_not_ready`

The intended evaluation order is:

1. resolve the strict local embedding target
2. if no local target exists:
   - return `provider_not_configured`
3. if a local target exists:
   - send a minimal embedding probe against that exact target
4. if the probe fails:
   - return `provider_unreachable_or_model_unavailable`
5. if the probe succeeds:
   - inspect the benchmark DB for chunk embeddings matching
     `provider_key + model_name`
6. if no matching embeddings exist:
   - return `vector_index_not_ready`
7. otherwise:
   - return `ok`

The CLI should treat only `ok` as runnable.

## 5. Error Semantics

The preflight messages should be operator-facing and explicit.

### 5.1 Provider Not Configured

This means no exact local embedding target can be constructed.

Typical causes:

- `KS_DEFAULT_MODEL_PROVIDER` is not set to `local`
- `KS_LOCAL_BASE_URL` is blank
- `KS_LOCAL_EMBEDDING_MODEL` is blank

Expected message shape:

- `Local embedding provider is not configured for TASK-058 benchmark. Set KS_DEFAULT_MODEL_PROVIDER=local and provide KS_LOCAL_BASE_URL plus KS_LOCAL_EMBEDDING_MODEL.`

### 5.2 Provider Unreachable Or Model Unavailable

This means the local embedding target exists syntactically, but a minimal probe
did not succeed.

Typical causes:

- Ollama is not running
- the configured local base URL is wrong
- the embedding model is not available locally
- the provider returned an invalid embedding payload

Expected message shape:

- `Local embedding provider probe failed for ollama/<model>.`

If implementation can safely preserve a short underlying error detail without
destabilizing tests, that detail may be appended. It is advisory, not required
for the first implementation.

### 5.3 Vector Index Not Ready

This means the local embedding probe succeeded, but the benchmark DB does not
contain chunk embeddings for that exact provider/model pair.

Expected message shape:

- `Vector index is not ready for local provider ollama/<model>. Run ingest to build chunk embeddings before benchmarking.`

This path is intentionally read-only. It must not auto-run ingest.

### 5.4 Success

When preflight passes, the message can remain short:

- `Local embedding preflight passed for ollama/<model>.`

Success output is mainly useful for tests and optional terminal diagnostics.

## 6. Artifact Behavior

Preflight failures must not produce benchmark artifacts.

That means:

- no partial JSON result file
- no half-run mode output
- no `fts_only`-completed artifact followed by `vector_only` failure

The benchmark artifact contract from the main `TASK-058` spec only applies once
the benchmark actually starts. Preflight failure is a CLI-level stop condition,
not a benchmark-result condition.

## 7. Testing

Add focused coverage only for the new behavior.

### 7.1 Preflight Tests

Add:

- `backend/tests/test_ask_retrieval_preflight.py`

Cover:

- no strict local target -> `provider_not_configured`
- local probe failure -> `provider_unreachable_or_model_unavailable`
- local probe success but no matching embeddings -> `vector_index_not_ready`
- local probe success with matching embeddings -> `ok`

These tests should use mocks and temporary SQLite fixtures, not real Ollama.

### 7.2 CLI Gating Tests

Extend:

- `backend/tests/test_ask_retrieval_cli.py`

Cover:

- preflight failure returns exit code `1`
- preflight failure prints the preflight message to stderr
- preflight failure does not call `run_ask_retrieval_benchmark`
- preflight failure does not write an artifact
- preflight success continues into the benchmark runner

### 7.3 Benchmark Regression Coverage

Re-run the existing retrieval benchmark suite to confirm the new gating layer
does not alter successful benchmark behavior:

- [backend/tests/test_ask_retrieval_metrics.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_retrieval_metrics.py)
- [backend/tests/test_ask_retrieval_modes.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_retrieval_modes.py)
- [backend/tests/test_ask_retrieval_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_retrieval_benchmark.py)
- [backend/tests/test_ask_retrieval_cli.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/tests/test_ask_retrieval_cli.py)

## 8. Acceptance For This Follow-Up

This follow-up is complete when:

- the retrieval benchmark CLI runs a local-only preflight before benchmark
  execution
- local benchmark runs cannot silently fall back to cloud embeddings
- preflight failures clearly distinguish:
  - missing local config
  - unreachable local provider or missing model
  - missing local vector index
- preflight failure stops the command before artifact creation
- existing retrieval benchmark contract stays intact for successful runs

That is enough to unlock the next planning step: implementing a reproducible
local baseline for `TASK-058` without widening scope into operator docs,
automatic provisioning, or `TASK-059`.
