# TASK-058 Ask Retrieval Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone ask retrieval benchmark runner that compares `fts_only`, `vector_only`, and `hybrid_rrf` on the approved `TASK-057` dataset and emits only `Recall@5`, `Recall@10`, and `NDCG@10` headline metrics.

**Architecture:** Keep the benchmark entrypoint under `eval/benchmark/`, but put the implementation logic in small backend `benchmark` modules so it can reuse the existing dataset models and retrieval stack without coupling itself to `eval/run_eval.py`. Split the work into four concerns: strict metric helpers, retrieval mode adapters, orchestration/result writing, and a thin CLI plus README update.

**Tech Stack:** Python 3.12, existing Pydantic dataset models in `backend/app/benchmark/ask_dataset.py`, existing retrieval modules in `backend/app/retrieval/`, JSON result files, `unittest`.

---

## Scope Check

Keep this as one implementation plan. The metric helpers, mode adapters,
orchestration, and CLI are all one retrieval-only benchmark slice from the
approved `TASK-058` spec. Do not split it into separate plans unless the spec
changes.

This plan intentionally does **not** include:

- `TASK-059` answer benchmarking
- `MRR`, latency, cost, or token metrics
- `abstain_or_no_hit` diagnostics
- `tool_allowed` diagnostics
- governance doc sync for `TASK_QUEUE` / `CURRENT_STATE` / `SESSION_LOG`

## File Structure

### Create

- `backend/app/benchmark/ask_retrieval_metrics.py`
  - Pure helpers for strict locator matching, case-level hit extraction, and
    aggregate `Recall@5`, `Recall@10`, `NDCG@10`.
- `backend/app/benchmark/ask_retrieval_modes.py`
  - Thin adapters that run `fts_only`, `vector_only`, and `hybrid_rrf` with one
    fixed `top_k=10` contract and normalize the returned candidates.
- `backend/app/benchmark/ask_retrieval_benchmark.py`
  - Benchmark orchestration: dataset selection, fail-closed mode execution,
    result shaping, and JSON writing.
- `backend/tests/test_ask_retrieval_metrics.py`
  - Contract tests for strict matching and metric formulas.
- `backend/tests/test_ask_retrieval_modes.py`
  - Adapter tests for correct retrieval entrypoints, fixed `top_k=10`, and
    disabled/failure behavior.
- `backend/tests/test_ask_retrieval_benchmark.py`
  - Orchestration tests for dataset selection, result schema, and fail-closed
    behavior.
- `backend/tests/test_ask_retrieval_cli.py`
  - Thin CLI tests that lock argument parsing, output writing, and non-zero exit
    on benchmark failure.
- `eval/benchmark/run_retrieval_benchmark.py`
  - Thin operator entrypoint for the new retrieval benchmark.

### Modify

- `backend/app/benchmark/__init__.py`
  - Export the new retrieval benchmark helpers used by tests and the CLI.
- `eval/README.md`
  - Add the exact benchmark command and explain that `TASK-058` is a
    retrieval-only benchmark separate from `eval/run_eval.py`.

### No Changes Expected

- `eval/run_eval.py`
  - This remains the regression/contract runner and should not absorb
    `TASK-058`.
- `eval/benchmark/ask_benchmark_cases.json`
  - Use the existing formal dataset without changing its schema.
- `backend/app/retrieval/sqlite_fts.py`
- `backend/app/retrieval/sqlite_vector.py`
- `backend/app/retrieval/hybrid.py`
  - Reuse these retrieval backends; do not redesign their core behavior.
- `docs/TASK_QUEUE.md`
- `docs/CURRENT_STATE.md`
- `docs/SESSION_LOG.md`
  - Governance sync is a later closeout task, not part of this implementation.

### Skills To Use During Execution

- `@using-git-worktrees` before Task 1 so implementation happens outside the
  dirty main worktree.
- `@test-driven-development` before every production edit.
- `@verification-before-completion` before any done claim or commit.
- `@requesting-code-review` after implementation and verification stabilize.

## Implementation Tasks

### Task 1: Add strict retrieval metric helpers

**Files:**
- Create: `backend/app/benchmark/ask_retrieval_metrics.py`
- Test: `backend/tests/test_ask_retrieval_metrics.py`

- [ ] **Step 1: Write the failing metric tests**

Lock the three spec-critical rules:

- locator matching requires exact `note_path`, exact `heading_path`, and an
  exact substring match for `excerpt_anchor` inside `candidate.text`
- `Recall@5` / `Recall@10` are **case-level** hit rates, not locator-level
  recall
- `NDCG@10` uses binary gain with standard `log2` discount

Use concrete tests like:

```python
import unittest

from app.benchmark.ask_dataset import AskBenchmarkLocator
from app.benchmark.ask_retrieval_metrics import (
    candidate_matches_locator,
    compute_case_mode_metrics,
    compute_mode_summary,
)
from app.contracts.workflow import RetrievedChunkCandidate


def _candidate(*, path="Roadmap.md", heading="Summary", text="Ship the benchmark now.", score=1.0):
    return RetrievedChunkCandidate(
        retrieval_source="sqlite_fts",
        chunk_id="chunk-1",
        note_id="note-1",
        path=path,
        title="Roadmap",
        heading_path=heading,
        note_type="note",
        template_family="",
        daily_note_date=None,
        source_mtime_ns=1,
        start_line=1,
        end_line=3,
        score=score,
        snippet="Ship the benchmark now.",
        text=text,
    )


class AskRetrievalMetricTests(unittest.TestCase):
    def test_candidate_matches_locator_requires_exact_triplet(self) -> None:
        locator = AskBenchmarkLocator(
            note_path="Roadmap.md",
            heading_path="Summary",
            excerpt_anchor="Ship the benchmark",
        )
        self.assertTrue(candidate_matches_locator(_candidate(), locator))
        self.assertFalse(candidate_matches_locator(_candidate(heading="Other"), locator))
        self.assertFalse(candidate_matches_locator(_candidate(text="Different text"), locator))
```

- [ ] **Step 2: Run the metric tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_retrieval_metrics -v
```

Expected: FAIL because `ask_retrieval_metrics.py` does not exist yet.

- [ ] **Step 3: Implement the minimal metric module**

Add `backend/app/benchmark/ask_retrieval_metrics.py` with focused functions:

- `candidate_matches_locator(candidate, locator) -> bool`
- `first_matching_rank(candidates, locator) -> int | None`
- `compute_case_mode_metrics(expected_locators, candidates) -> dict`
- `compute_mode_summary(case_metrics) -> dict`

Implementation rules to hard-code:

- normalize line endings to `\n`
- trim leading/trailing whitespace on `excerpt_anchor` before substring matching
- no case folding, no punctuation normalization, no snippet fallback
- one candidate can satisfy only one new locator gain contribution for
  `NDCG@10`
- `Recall@5` and `Recall@10` count a case as `1` when **any** expected locator
  is recovered inside the cutoff

Use a standard DCG helper:

```python
import math


def discounted_gain(rank: int, relevance: int) -> float:
    return (2**relevance - 1) / math.log2(rank + 1)
```

- [ ] **Step 4: Re-run the metric tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_retrieval_metrics -v
```

Expected: PASS with strict matching and all three metrics locked.

- [ ] **Step 5: Commit the metric slice**

```bash
git add backend/app/benchmark/ask_retrieval_metrics.py \
  backend/tests/test_ask_retrieval_metrics.py
git commit -m "feat: add ask retrieval benchmark metrics"
```

### Task 2: Add retrieval mode adapters with fixed top-k and explicit failure semantics

**Files:**
- Create: `backend/app/benchmark/ask_retrieval_modes.py`
- Test: `backend/tests/test_ask_retrieval_modes.py`

- [ ] **Step 1: Write the failing adapter tests**

Lock these adapter rules:

- `fts_only` uses `search_chunks(...)`
- `vector_only` uses `search_chunk_vectors(...)`
- `hybrid_rrf` uses `search_hybrid_chunks(...)`
- every mode uses the same fixed `limit=10`
- disabled or failing modes become explicit benchmark errors, not silent skips

Use patched retrieval functions so the tests do not depend on a real index:

```python
import sqlite3
import unittest
from unittest.mock import patch

from app.benchmark.ask_retrieval_modes import (
    RetrievalBenchmarkModeError,
    run_retrieval_mode,
)
from app.contracts.workflow import RetrievalSearchResponse


class AskRetrievalModeTests(unittest.TestCase):
    @patch("app.benchmark.ask_retrieval_modes.search_chunks")
    def test_fts_mode_uses_fixed_top_k(self, search_chunks_mock) -> None:
        search_chunks_mock.return_value = RetrievalSearchResponse(candidates=[])
        run_retrieval_mode(
            mode="fts_only",
            connection=sqlite3.connect(":memory:"),
            query="roadmap",
            settings=self.settings,
        )
        self.assertEqual(search_chunks_mock.call_args.kwargs["limit"], 10)
```

- [ ] **Step 2: Run the adapter tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_retrieval_modes -v
```

Expected: FAIL because the adapter module and error type do not exist yet.

- [ ] **Step 3: Implement the adapter module**

Add `backend/app/benchmark/ask_retrieval_modes.py` with:

- one literal mode enum or string constants for:
  - `fts_only`
  - `vector_only`
  - `hybrid_rrf`
- one `RetrievalBenchmarkModeError(RuntimeError)` for disabled/failed modes
- one `run_retrieval_mode(...)` helper that:
  - accepts `connection`, `query`, `settings`
  - dispatches to the correct retrieval function
  - always passes `limit=10`
  - returns the raw `RetrievedChunkCandidate` list
  - raises `RetrievalBenchmarkModeError` if the response is disabled or if the
    backend raises

Prefer fail-fast behavior here so the orchestration layer can implement the
spec’s fail-closed run contract without extra ambiguity.

- [ ] **Step 4: Re-run the adapter tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_retrieval_modes -v
```

Expected: PASS with all three modes pinned to one execution contract.

- [ ] **Step 5: Commit the adapter slice**

```bash
git add backend/app/benchmark/ask_retrieval_modes.py \
  backend/tests/test_ask_retrieval_modes.py
git commit -m "feat: add ask retrieval benchmark mode adapters"
```

### Task 3: Add benchmark orchestration and result writing

**Files:**
- Create: `backend/app/benchmark/ask_retrieval_benchmark.py`
- Modify: `backend/app/benchmark/__init__.py`
- Test: `backend/tests/test_ask_retrieval_benchmark.py`

- [ ] **Step 1: Write the failing orchestration tests**

Lock the benchmark-specific behavior:

- selected cases include only `single_hop`, `multi_hop`, `metadata_filter`
- cases with `allow_tool=true` are excluded even if their bucket is otherwise
  eligible
- the top-level result payload includes:
  - `schema_version`
  - `benchmark_kind`
  - `run_status`
  - `dataset_schema_version`
  - `selected_case_count`
  - `selected_case_ids`
  - `excluded_cases`
  - `modes`
  - `cases`
- `excluded_cases` records `case_id`, `bucket`, and `exclusion_reason`
- each emitted case record uses the output field name `expected_locators`, even
  though the dataset model field is `expected_relevant_locators`
- each emitted case record preserves:
  - `case_id`
  - `bucket`
  - `user_query`
  - `expected_locators`
  - `mode_results`
- each emitted `mode_result` includes:
  - `mode`
  - `top_k`
  - `retrieved_candidates`
  - `matched_locator_ranks`
  - `hit_at_5`
  - `hit_at_10`
  - `ndcg_at_10`
- each top-level `modes[mode_name]` entry includes:
  - `status`
  - `selected_case_count`
  - `summary_metrics` on success
  - `failure_reason` on failure
- a mode failure marks the whole run `failed`
- failed runs do **not** emit headline summary metrics
- successful runs emit only:
  - `Recall@5`
  - `Recall@10`
  - `NDCG@10`

Use a patched dataset loader and patched adapter function so tests stay
deterministic:

```python
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.benchmark.ask_dataset import AskBenchmarkCase, AskBenchmarkDataset, AskBenchmarkLocator
from app.benchmark.ask_retrieval_benchmark import run_ask_retrieval_benchmark


class AskRetrievalBenchmarkTests(unittest.TestCase):
    @patch("app.benchmark.ask_retrieval_benchmark.run_retrieval_mode")
    @patch("app.benchmark.ask_retrieval_benchmark.load_ask_benchmark_dataset")
    def test_run_benchmark_excludes_tool_and_negative_cases(self, load_dataset_mock, run_mode_mock) -> None:
        load_dataset_mock.return_value = AskBenchmarkDataset(schema_version=1, cases=[...])
        run_mode_mock.return_value = []
        result = run_ask_retrieval_benchmark(settings=self.settings)
        self.assertEqual(result["selected_case_count"], 1)
        self.assertEqual(result["excluded_cases"][0]["exclusion_reason"], "allow_tool")

    @patch("app.benchmark.ask_retrieval_benchmark.run_retrieval_mode")
    @patch("app.benchmark.ask_retrieval_benchmark.load_ask_benchmark_dataset")
    def test_run_benchmark_emits_full_result_contract(self, load_dataset_mock, run_mode_mock) -> None:
        load_dataset_mock.return_value = AskBenchmarkDataset(schema_version=1, cases=[...])
        run_mode_mock.return_value = [self._matching_candidate()]
        result = run_ask_retrieval_benchmark(settings=self.settings)
        self.assertEqual(result["benchmark_kind"], "ask_retrieval")
        self.assertEqual(result["run_status"], "passed")
        self.assertIn("fts_only", result["modes"])
        self.assertEqual(result["modes"]["fts_only"]["status"], "passed")
        self.assertEqual(result["modes"]["fts_only"]["selected_case_count"], 1)
        self.assertIn("expected_locators", result["cases"][0])
        self.assertEqual(result["cases"][0]["case_id"], "ask_case_001")
        self.assertEqual(result["cases"][0]["bucket"], "single_hop")
        self.assertEqual(result["cases"][0]["user_query"], "What shipped?")
        self.assertIn("mode_results", result["cases"][0])
        self.assertEqual(result["cases"][0]["mode_results"][0]["top_k"], 10)
```

- [ ] **Step 2: Run the orchestration tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_retrieval_benchmark -v
```

Expected: FAIL because the orchestration module does not exist yet.

- [ ] **Step 3: Implement the orchestration module**

Add `backend/app/benchmark/ask_retrieval_benchmark.py` with focused helpers:

- `select_task_058_v1_cases(dataset) -> tuple[selected_cases, excluded_cases]`
- `build_default_output_path(results_dir) -> Path`
- `run_ask_retrieval_benchmark(settings, dataset_path=None, output_path=None) -> dict`
- `write_retrieval_benchmark_result(result, output_path) -> Path`

Implementation rules to hard-code:

- initialize and open the index database with:
  - `initialize_index_db(settings.index_db_path, settings=settings)`
  - `connect_sqlite(initialized_db_path)`
- when `output_path` is omitted, write the artifact under
  `/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/results/` using
  the timestamped filename shape from the spec
- hold one shared SQLite connection for the full benchmark run
- close the connection in `finally`, even when a mode fails
- the v1 selector keeps only `single_hop`, `multi_hop`, `metadata_filter`
- any `allow_tool=true` case is excluded
- `abstain_or_no_hit` is excluded
- the benchmark runs all three modes for every selected case
- if any mode raises `RetrievalBenchmarkModeError`, mark the run `failed`,
  record explicit mode failure details, omit summary metrics, and stop the run
- successful mode summaries must include only the three headline metrics

Keep the in-memory result contract as plain dict/list structures. Do **not**
introduce a second Pydantic model layer for the result artifact.

Be explicit about the output-field rename during serialization:

- dataset input field: `expected_relevant_locators`
- result artifact field: `expected_locators`

Also make the top-level `modes` object and per-case output shape explicit during
serialization:

- `modes[mode_name]`
  - `status`
  - `selected_case_count`
  - `summary_metrics` or `failure_reason`
- `cases[*]`
  - `case_id`
  - `bucket`
  - `user_query`
  - `expected_locators`
  - `mode_results`

- [ ] **Step 4: Re-run the orchestration tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_retrieval_benchmark -v
```

Expected: PASS with selection, fail-closed semantics, and output schema locked.

- [ ] **Step 5: Export the benchmark entrypoint**

Update `backend/app/benchmark/__init__.py` so tests and the CLI can import:

- `run_ask_retrieval_benchmark`
- `write_retrieval_benchmark_result`

Keep the export list small; do not re-export every internal helper.

- [ ] **Step 6: Run the combined benchmark unit suite**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_retrieval_metrics \
  tests.test_ask_retrieval_modes \
  tests.test_ask_retrieval_benchmark -v
```

Expected: PASS with the entire retrieval benchmark core stable.

- [ ] **Step 7: Commit the orchestration slice**

```bash
git add backend/app/benchmark/__init__.py \
  backend/app/benchmark/ask_retrieval_benchmark.py \
  backend/tests/test_ask_retrieval_benchmark.py
git commit -m "feat: add ask retrieval benchmark runner core"
```

### Task 4: Add the CLI entrypoint and operator docs

**Files:**
- Create: `eval/benchmark/run_retrieval_benchmark.py`
- Modify: `eval/README.md`
- Test: `backend/tests/test_ask_retrieval_cli.py`

- [ ] **Step 1: Write the failing CLI tests**

Lock the operator-facing behavior:

- the CLI can accept an explicit `--output`
- the CLI can accept an optional `--dataset` override for smoke tests
- successful runs exit `0`
- failed benchmark runs exit non-zero

Prefer testing a `main(argv)` function directly rather than using subprocesses:

```python
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[2]
CLI_PATH = ROOT_DIR / "eval" / "benchmark" / "run_retrieval_benchmark.py"

spec = importlib.util.spec_from_file_location("run_retrieval_benchmark", CLI_PATH)
cli_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(cli_module)
main = cli_module.main


class AskRetrievalCliTests(unittest.TestCase):
    @patch.object(cli_module, "run_ask_retrieval_benchmark")
    def test_cli_returns_zero_for_successful_run(self, run_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "retrieval.json"
            run_mock.return_value = {"run_status": "passed"}
            exit_code = main(["--output", str(output_path)])
            self.assertEqual(exit_code, 0)
```

- [ ] **Step 2: Run the CLI tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_retrieval_cli -v
```

Expected: FAIL because the CLI module does not exist yet.

- [ ] **Step 3: Implement the thin CLI entrypoint**

Create `eval/benchmark/run_retrieval_benchmark.py` in the same style as
`manage_ask_benchmark.py`:

- add the project root and backend path to `sys.path`
- parse:
  - `--output`
  - `--dataset`
- call `run_ask_retrieval_benchmark(...)`
- when `--output` is omitted, rely on the benchmark helper’s default path under
  `eval/results/`
- return `0` only when `run_status == "passed"`

Keep the CLI thin. Do not reimplement selection, metric, or result-shaping
logic here.

- [ ] **Step 4: Update `eval/README.md` with the exact operator command**

Add a short section that explains:

- `eval/run_eval.py` remains the regression baseline runner
- `eval/benchmark/run_retrieval_benchmark.py` is the retrieval-only benchmark

Document a concrete command:

```bash
/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/.conda/knowledge-steward/bin/python \
  eval/benchmark/run_retrieval_benchmark.py \
  --output /tmp/retrieval-benchmark.json
```

- [ ] **Step 5: Re-run the CLI tests and the full retrieval benchmark suite**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_retrieval_metrics \
  tests.test_ask_retrieval_modes \
  tests.test_ask_retrieval_benchmark \
  tests.test_ask_retrieval_cli -v
```

Expected: PASS with the operator entrypoint and docs aligned to the new runner.

- [ ] **Step 6: Run one end-to-end benchmark smoke command**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
./.conda/knowledge-steward/bin/python eval/benchmark/run_retrieval_benchmark.py \
  --output /tmp/task-058-retrieval-benchmark.json
```

Expected: PASS with a JSON artifact written to `/tmp/task-058-retrieval-benchmark.json`.
If vector retrieval is unavailable, the command should fail non-zero with an
explicit mode failure rather than silently writing headline metrics.

- [ ] **Step 7: Commit the CLI/docs slice**

```bash
git add backend/tests/test_ask_retrieval_cli.py \
  eval/benchmark/run_retrieval_benchmark.py \
  eval/README.md
git commit -m "feat: add ask retrieval benchmark cli"
```

## Final Verification

- [ ] **Step 1: Re-run the full retrieval benchmark test suite**

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_retrieval_metrics \
  tests.test_ask_retrieval_modes \
  tests.test_ask_retrieval_benchmark \
  tests.test_ask_retrieval_cli -v
```

Expected: PASS with no skipped retrieval benchmark tests.

- [ ] **Step 2: Re-run the benchmark smoke command**

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
./.conda/knowledge-steward/bin/python eval/benchmark/run_retrieval_benchmark.py \
  --output /tmp/task-058-retrieval-benchmark.json
```

Expected:

- success path: artifact exists and the mode summaries contain only `Recall@5`,
  `Recall@10`, and `NDCG@10`
- failure path: non-zero exit with explicit mode failure details and no
  headline metrics

- [ ] **Step 3: Request code review before merge**

Use `@requesting-code-review` after the final verification passes. The review
should check:

- spec alignment with
  [2026-04-19-task-058-ask-retrieval-benchmark-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-19-task-058-ask-retrieval-benchmark-design.md)
- strict locator matching on `candidate.text`
- fixed `top_k=10`
- fail-closed mode handling
- absence of `MRR` / latency scope creep
