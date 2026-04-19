# TASK-058 Ask Retrieval Benchmark Design

**Task:** `TASK-058`

**Session:** `SES-20260419-02`

**Problem**

`TASK-057` already produced a fixed `50`-case ask benchmark dataset, but the
project still lacks a retrieval-only benchmark layer that can answer a narrower
question with defensible numbers: given a stable ask query set, how well do
`fts_only`, `vector_only`, and `hybrid_rrf` retrieve the correct evidence
before answer generation starts?

The current offline eval entrypoint in [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
is still a regression-and-contract runner. It mixes fixture checks, sample vault
cases, retrieval-only fallbacks, generated-answer paths, and governance/digest
scenarios. That is useful for catching regressions, but it is not the right
layer for headline retrieval numbers that can later be cited in interview or
resume narratives.

`TASK-058` exists to create that retrieval layer first, without leaking into the
real-provider answer benchmark that belongs to `TASK-059`.

**Goal**

Create an independent retrieval benchmark runner for ask that:

- consumes the formal `TASK-057` dataset
- compares `fts_only`, `vector_only`, and `hybrid_rrf`
- uses strict locator-level relevance matching
- reports only three headline metrics:
  - `Recall@5`
  - `Recall@10`
  - `NDCG@10`
- stays retrieval-only and does not enter answer generation, context assembly,
  or runtime faithfulness gating

**Non-Goals**

- Do not extend [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
  into a second mixed-purpose benchmark runner.
- Do not benchmark real provider answer quality; that belongs to `TASK-059`.
- Do not change the formal dataset schema for `TASK-057`.
- Do not add `abstain_or_no_hit` diagnostics in `TASK-058` v1.
- Do not add `tool_allowed` diagnostics in `TASK-058` v1.
- Do not include `MRR`, latency, cost, or token metrics in the v1 headline
  contract.

**Approaches Considered**

1. Extend the existing regression runner.
   Rejected because it would keep regression and retrieval benchmarking coupled,
   which weakens the clarity of the resulting headline numbers.
2. Add a dedicated retrieval benchmark runner that reuses retrieval primitives
   and selected benchmark helpers.
   Recommended because it keeps the benchmark boundary clean while preserving
   code reuse.
3. Add a minimal one-off script with an ad hoc JSON shape.
   Rejected because it would be fast to start but would likely need a second
   redesign before `TASK-059`.

**Recommended Approach**

Create a dedicated retrieval benchmark path under `eval/benchmark/` and keep the
runtime responsibilities separate:

1. select a fixed v1 headline subset from the formal ask benchmark dataset
2. run that subset against `fts_only`, `vector_only`, and `hybrid_rrf`
3. evaluate each mode with strict locator-level matching over a fixed top-10
   cutoff
4. aggregate only `Recall@5`, `Recall@10`, and `NDCG@10`
5. write results into a dedicated retrieval benchmark artifact under
   `eval/results/`

This keeps `TASK-058` focused on retrieval quality numbers that can be defended
independently, while leaving full ask-path answer benchmarking to `TASK-059`.

## 1. Scope And Benchmark Boundary

`TASK-058` v1 is intentionally narrow. It measures retrieval quality only.

The runner will consume the formal dataset in
[eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json)
through [backend/app/benchmark/ask_dataset.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/benchmark/ask_dataset.py).
It will not call the ask graph, run tool selection, build an answer, or enter
runtime gate logic.

The v1 headline subset is:

- `single_hop`
- `multi_hop`
- `metadata_filter`

The v1 exclusions are:

- `abstain_or_no_hit`
- any case with `allow_tool=true`

That means `tool_allowed` cases and negative/no-hit cases are not part of the
first retrieval headline. They remain in the dataset, but are outside the
`TASK-058` v1 contract.

`metadata_filter` cases are included, but only as natural-language queries with
filter-like intent. The current dataset contract does not carry a structured
`retrieval_filter` field, so `TASK-058` v1 does not attempt to infer or invent
one.

## 2. Relevance Contract

The retrieval benchmark must judge relevance at strict locator level rather than
at note level.

A returned candidate counts as relevant only when it matches one expected
locator on all three fields:

- `note_path`
- `heading_path`
- `excerpt_anchor`

This is intentionally stricter than note-level matching. The benchmark is meant
to support statements about retrieving the correct evidence span, not merely the
correct note. No fuzzy fallback, same-note relaxation, or near-match heuristic
is part of `TASK-058` v1.

This strict contract also keeps the benchmark aligned with later answer-level
evaluation: if retrieval does not surface the correct evidence region, answer
quality numbers cannot honestly claim that retrieval succeeded.

Because the current retrieval candidate contract does not carry an explicit
`excerpt_anchor` field, `TASK-058` v1 must compare anchors against the full
retrieved candidate text, not against snippets or a derived projection.

The exact v1 matching rule is:

- `note_path` must equal `candidate.path`
- `heading_path` must equal `candidate.heading_path`
- `excerpt_anchor` must appear as an exact substring inside `candidate.text`

Allowed normalization is intentionally minimal:

- normalize line endings to `\n`
- trim leading and trailing whitespace on the stored anchor before substring
  comparison

No additional fuzzy matching, case folding, punctuation normalization, or
snippet-based fallback is allowed.

## 3. Component Layout

The implementation should be split into focused pieces.

### 3.1 CLI Entry

Add a thin entrypoint:

- `eval/benchmark/run_retrieval_benchmark.py`

Its responsibilities are limited to:

- parsing runtime arguments
- invoking the benchmark service
- choosing output location
- returning process exit status

This keeps the CLI style consistent with
[eval/benchmark/manage_ask_benchmark.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/manage_ask_benchmark.py).

### 3.2 Benchmark Orchestration

Add a benchmark service module:

- `backend/app/benchmark/ask_retrieval_benchmark.py`

It is responsible for:

- loading the formal dataset
- selecting the v1 headline subset
- running each case against each retrieval mode
- collecting case-level outputs
- aggregating final headline metrics

### 3.3 Retrieval Mode Adapters

Add a thin adapter module:

- `backend/app/benchmark/ask_retrieval_modes.py`

It should wrap the existing retrieval implementations behind one uniform
interface:

- [backend/app/retrieval/sqlite_fts.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_fts.py)
- [backend/app/retrieval/sqlite_vector.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/sqlite_vector.py)
- [backend/app/retrieval/hybrid.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/retrieval/hybrid.py)

The adapter layer exists to keep retrieval execution separate from metric logic.

### 3.4 Metric Logic

Add a dedicated metric module:

- `backend/app/benchmark/ask_retrieval_metrics.py`

It should implement:

- strict locator matching
- per-case hit extraction
- aggregate `Recall@5`
- aggregate `Recall@10`
- aggregate `NDCG@10`

The metric layer should remain pure and independent from filesystem or CLI
concerns.

## 4. Data Flow

The benchmark run should be linear and explicit:

1. load the formal ask benchmark dataset
2. select v1 headline cases
3. for each selected case, run:
   - `fts_only`
   - `vector_only`
   - `hybrid_rrf`
4. for each mode result, compare returned candidates against expected locators
5. compute per-case ranks and hit signals
6. aggregate the three headline metrics per mode
7. write a dedicated result artifact

The benchmark does not modify the dataset, backlog, or existing regression
artifacts.

For v1, all three modes must be executed with a fixed `top_k=10` retrieval
cutoff. `Recall@5` is computed from the top-5 prefix of that same returned
ranking. No per-mode custom cutoff, overfetch rule, or dynamic top-k policy is
allowed in `TASK-058` v1, because the benchmark needs one stable comparison
surface.

## 5. Result Contract

The retrieval benchmark should write a dedicated result file under
`eval/results/`, for example:

- `retrieval-benchmark-YYYYMMDD-HHMMSS.json`

The top-level result payload should include at least:

- `schema_version`
- `benchmark_kind`
- `run_status`
- `dataset_schema_version`
- `selected_case_count`
- `selected_case_ids`
- `excluded_cases`
- `modes`
- `cases`

The v1 result shape should stay concrete enough for one implementation path:

- `excluded_cases`
  - array of objects with at least:
    - `case_id`
    - `bucket`
    - `exclusion_reason`
- `modes`
  - object keyed by mode name (`fts_only`, `vector_only`, `hybrid_rrf`)
  - each value contains:
    - `status`
    - `selected_case_count`
    - `summary_metrics` when `status="passed"`
    - `failure_reason` when `status!="passed"`
- `cases`
  - array of per-case objects
  - each case object includes:
    - `case_id`
    - `bucket`
    - `user_query`
    - `expected_locators`
    - `mode_results`

The per-mode summary should contain only the v1 headline metrics:

- `Recall@5`
- `Recall@10`
- `NDCG@10`

For `TASK-058` v1, these metrics are defined as follows:

- `Recall@5`
  - case-level hit rate: a case counts as recovered at 5 when at least one
    expected locator appears in ranks `1..5`
- `Recall@10`
  - case-level hit rate: a case counts as recovered at 10 when at least one
    expected locator appears in ranks `1..10`
- `NDCG@10`
  - binary-gain ranking quality computed over ranks `1..10`
  - each retrieved candidate contributes gain `1` only if its
    `note_path + heading_path + excerpt_anchor` triple matches an expected
    locator not already counted earlier in the same ranked list
  - `DCG@10 = sum((2^rel_i - 1) / log2(i + 1))` for `i = 1..10`, where
    `rel_i` is binary and rank is 1-based
  - `IDCG@10` uses the same formula on the ideal ranking of distinct expected
    locators, capped at `10`
  - `NDCG@10 = DCG@10 / IDCG@10`, and equals `0` when `IDCG@10 = 0`
  - ideal DCG is computed from a perfect ranking of the case's expected
    locators, capped at `10`

Each case result should keep enough structure to explain those aggregates:

- `case_id`
- `bucket`
- `user_query`
- `expected_locators`
- `mode_results`

Each `mode_result` should include at least:

- `mode`
- `top_k`
- `retrieved_candidates`
- `matched_locator_ranks`
- `hit_at_5`
- `hit_at_10`
- `ndcg_at_10`

The file should not include `MRR`, latency aggregates, or no-hit/tool
diagnostics in v1.

## 6. Error Handling

The runner should fail closed on dataset contract problems and stay explicit on
mode failures.

### 6.1 Hard Failures

The run should terminate immediately when:

- the formal dataset cannot be loaded
- a selected case is missing required locator fields
- filtering leaves zero selected cases

These are benchmark contract failures, not recoverable runtime noise.

### 6.2 Mode-Level Failures

If one retrieval mode fails during execution, the result should stay explicit.

Examples:

- vector mode disabled because the embedding index is not ready
- a retrieval backend raises an exception

`TASK-058` v1 should use a single fail-closed policy:

- if any required mode is unavailable or fails for any selected case, the run is
  marked failed
- the CLI exits non-zero
- the artifact, if written, must carry `run_status="failed"` and explicit mode
  failure details
- no headline summary metrics are emitted for a failed run

This keeps the benchmark from producing incomplete three-way comparisons that
look like valid resume-grade numbers.

### 6.3 No Fuzzy Relevance Recovery

When locator matching fails, the candidate is simply non-relevant. The benchmark
must not add fuzzy text matching, same-note fallback, or heuristic “close
enough” recovery.

## 7. Testing Strategy

`TASK-058` v1 needs focused tests, not broad integration sprawl.

### 7.1 Dataset Selection Tests

Verify that v1 selection keeps only:

- `single_hop`
- `multi_hop`
- `metadata_filter`

and excludes:

- `abstain_or_no_hit`
- `allow_tool=true`

### 7.2 Locator Matching Tests

Verify that a hit is counted only when all three locator fields match:

- `note_path`
- `heading_path`
- `excerpt_anchor`

Wrong heading, wrong anchor, or same-note-nearby content must not count as a
hit.

### 7.3 Metric Tests

Use small hand-constructed samples to verify:

- `Recall@5`
- `Recall@10`
- `NDCG@10`

These tests should not depend on full sample vault behavior.

### 7.4 Runner Contract Tests

Verify that the result artifact:

- contains the three headline metrics only
- preserves case-level rank details needed to explain those metrics
- uses fixed `top_k=10` semantics for every mode
- handles mode failures with the fail-closed contract rather than silently
  omitting them

## 8. Risks And Mitigations

### Risks

- Strict locator matching may initially make the numbers look worse than
  note-level matching.
- `metadata_filter` cases may still blur “natural-language filter intent” and
  “true structured filter evaluation.”
- A mode failure, especially in vector retrieval, could block the benchmark from
  producing comparable three-way numbers.

### Mitigations

- Keep the strict contract anyway, because resume-grade numbers need to be
  defensible under questioning.
- State clearly in the result contract and later planning that `metadata_filter`
  is still a natural-language query subset in v1.
- Make failure behavior explicit so missing vector readiness cannot be mistaken
  for valid benchmark output.

## 9. Governance Sync Note

The current `TASK-058` acceptance text in
[docs/TASK_QUEUE.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/TASK_QUEUE.md)
still mentions `MRR` and latency outputs.

This design intentionally narrows `TASK-058` v1 to three headline metrics only:

- `Recall@5`
- `Recall@10`
- `NDCG@10`

That acceptance alignment should be synchronized into governance documents when
the user chooses to run the corresponding documentation update. Until then, this
spec is the approved design source for the implementation and planning phase of
`TASK-058`.
