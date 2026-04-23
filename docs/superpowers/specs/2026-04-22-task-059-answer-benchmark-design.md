# TASK-059 Answer Benchmark Design

**Task:** `TASK-059`

**Session:** `SES-20260422-02`

**Problem**

`TASK-057` already produced a fixed `50`-case ask benchmark dataset, and
`TASK-058` already split out the retrieval layer with stable local baselines.
The remaining gap is the answer layer: the project still lacks a real-provider
benchmark that can answer a defensible question with explicit evidence:

- when ask runs against a fixed canonical cloud model, how often does it produce
  a correct grounded answer?
- how much benefit comes from context assembly?
- how much safety benefit comes from the runtime faithfulness gate?
- what trade-off do those layers impose on answer rate and latency?

The current regression runner in
[eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
is intentionally pinned to `provider_mode=none|mocked_cloud`. That is the right
contract for deterministic regression, but it is the wrong layer for a
resume-grade benchmark that must exercise the real ask path with a fixed cloud
provider and model.

`TASK-059` exists to create that answer benchmark layer without polluting the
existing regression contract and without collapsing retrieval, answer quality,
and reporting into one mixed-purpose runner.

**Goal**

Create an independent answer benchmark path that:

- uses the fixed `TASK-057` dataset
- runs the real ask path against canonical cloud model `qwen3.6-flash-2026-04-16`
- compares three explicit variants:
  - `hybrid`
  - `hybrid + context assembly`
  - `hybrid + context assembly + runtime faithfulness gate`
- introduces a fixed `10`-case smoke subset before full runs
- scores answers with deterministic rules derived from
  `expected_facts / forbidden_claims`
- records benchmark metadata and variant-level aggregates clearly enough for
  later interview or resume use

**Non-Goals**

- Do not extend [eval/run_eval.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/run_eval.py)
  into a second mixed-purpose benchmark runner.
- Do not add rerank, multi-provider comparison, or prompt experimentation.
- Do not add LLM judge scoring in v1.
- Do not push real-provider answer benchmark runs into CI.
- Do not fold `TASK-060` manual review, taxonomy, or report export into this
  task.
- Do not redefine the `TASK-057` formal dataset schema beyond benchmark-facing
  sidecar files needed for subset selection or result metadata.

**Approaches Considered**

1. Add a dedicated answer benchmark runner under `eval/benchmark/` and reuse the
   existing ask runtime.
   Recommended because it keeps regression and resume-grade benchmarking cleanly
   separated while preserving code reuse.
2. Extend the existing regression runner with a real-provider benchmark mode.
   Rejected because it would mix deterministic regression and cloud benchmark
   semantics in one entrypoint.
3. Add a thin orchestration script that shells out to the regression runner.
   Rejected because it would preserve the same boundary problem while adding a
   second layer of glue code.

**Recommended Approach**

Create a dedicated answer benchmark path under `eval/benchmark/` that reuses the
real ask workflow but owns its own benchmark contract:

1. select either the fixed `10`-case smoke subset or the full `50`-case dataset
2. execute the same selected cases across three explicit answer variants
3. score each case with deterministic rules based on expected facts and
   forbidden claims
4. aggregate benchmark metrics and execution metadata per variant
5. require a successful smoke run before the operator chooses to run full mode

This keeps `TASK-059` focused on the answer layer while preserving the existing
deterministic regression runner as a separate artifact.

## 1. Scope And Benchmark Boundary

`TASK-059` is an answer benchmark, not a replacement for regression and not a
retrieval benchmark follow-up.

The benchmark runner should consume the formal dataset in
[eval/benchmark/ask_benchmark_cases.json](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/eval/benchmark/ask_benchmark_cases.json)
through the existing benchmark dataset helpers. It should then execute the real
ask path in
[backend/app/services/ask.py](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend/app/services/ask.py)
with a benchmark-owned variant matrix.

The benchmark boundary is:

- benchmark owns case selection
- benchmark owns variant selection
- benchmark owns result scoring and aggregation
- ask runtime continues to own retrieval, answer generation, tool execution,
  guardrails, citations, and runtime faithfulness evaluation

The benchmark must not introduce a second answer-generation implementation. If
`generated_answer` quality is the thing being measured, the benchmark must go
through the same ask path the product itself uses.

The canonical benchmark target for v1 is fixed:

- provider class: cloud
- provider family: `qwen`
- model id: `qwen3.6-flash-2026-04-16`

This canonical target should be recorded in the result metadata and treated as a
required part of the benchmark identity.

## 2. Modes And Dataset Selection

The benchmark should support exactly two execution modes.

### 2.1 Smoke Mode

Smoke mode is the preflight benchmark surface. It exists to answer one
operational question before a full run starts: do the numbers and behaviors look
normal enough to justify the cost of running the whole matrix?

Smoke mode must use a fixed, committed subset with these properties:

- exactly `10` cases
- fixed membership, not dynamic sampling
- drawn only from the answerable main set
- excludes `tool_allowed=true`
- excludes negative / abstain-first cases

The fixed subset should be stored as a benchmark-owned sidecar so later runs are
directly comparable and do not depend on selection code drift.

### 2.2 Full Mode

Full mode is the formal answer benchmark run.

It should execute the full `50`-case dataset across the same variant matrix. It
keeps `tool_allowed` and abstain/no-hit cases inside the benchmark surface so
that aggregated rates such as `generated_answer_rate`,
`retrieval_only_rate`, and `unsupported_claim_rate` represent the actual full
dataset behavior.

Full mode is not automatically triggered by smoke. The operator explicitly
chooses to run it after reviewing the smoke result.

## 3. Variant Matrix

The answer benchmark must compare exactly three variants on the same selected
case set.

1. `hybrid`
2. `hybrid + context assembly`
3. `hybrid + context assembly + runtime faithfulness gate`

The point of this matrix is not raw feature coverage. It is attribution:

- how much answer quality improves when assembly is enabled
- how much unsupported-claim risk drops when the runtime gate is enabled
- what answer-rate and latency trade-off those gains impose

The benchmark therefore needs an explicit and observable configuration surface
for assembly and gate behavior. A named variant must not silently collapse to
another variant because a toggle was not actually wired through.

This requirement implies a benchmark-facing configuration hook. The exact
implementation can vary, but the public contract must make it possible to run
the same ask workflow under three known settings and to record which one was
used.

## 4. Component Layout

The implementation should be split into focused units rather than one large
script.

### 4.1 CLI Entry

Add a thin CLI entrypoint under `eval/benchmark/`, for example:

- `eval/benchmark/run_answer_benchmark.py`

Its responsibilities should be limited to:

- parsing benchmark mode and output arguments
- loading settings
- running benchmark preflight
- invoking the benchmark service
- writing or selecting the final artifact path
- returning process exit status

### 4.2 Benchmark Orchestration

Add a benchmark service module under `backend/app/benchmark/`.

Its responsibilities are:

- loading the formal dataset
- loading the fixed smoke subset definition
- selecting the mode-specific case list
- expanding the variant matrix
- executing each `case x variant`
- collecting case-level outputs
- aggregating per-variant metrics

This layer should not duplicate ask internals.

### 4.3 Variant Execution Layer

Add a focused variant execution layer under `backend/app/benchmark/`.

Its job is to invoke the real ask path with a benchmark-owned configuration for:

- canonical provider/model routing
- assembly on/off
- runtime gate on/off

That layer should return the raw ask outcome plus execution metadata needed for
scoring and aggregation.

### 4.4 Rule Scoring Layer

Add a pure scoring module under `backend/app/benchmark/`.

Its responsibilities are:

- compare the answer against `expected_facts`
- detect forbidden content through `forbidden_claims`
- derive a deterministic case verdict such as
  `correct / partial / incorrect`
- emit explicit hit/miss details for later bad-case inspection

This scorer should remain independent from provider calls and filesystem
concerns. It exists to keep answer evaluation deterministic and auditable.

## 5. Data Flow

The benchmark run should be linear and explicit:

1. load the formal dataset
2. load the fixed smoke subset definition
3. select either smoke or full case ids
4. expand the selected case ids across the three variants
5. run each `case x variant` through the real ask path under `qwen3.6-flash-2026-04-16`
6. score each result with deterministic rules
7. aggregate metrics per variant
8. write a dedicated result artifact

No benchmark run should mutate the formal dataset itself. Benchmark-owned side
artifacts such as a smoke subset definition or prompt-version stamp are allowed,
but the main dataset remains the source of truth for case semantics.

## 6. Result Contract

The answer benchmark should write a dedicated artifact under `eval/results/`,
separate from the regression runner artifacts.

The result schema should have three levels.

### 6.1 Run-Level Metadata

The top-level result payload should include at least:

- `schema_version`
- `benchmark_kind`
- `benchmark_mode`
- `dataset_version`
- `smoke_subset_version` when applicable
- `provider_name`
- `model_name`
- `run_timestamp`
- `git_commit`
- `prompt_version`
- `vault_fixture_id`
- `worktree_dirty`
- `selected_case_count`
- `selected_case_ids`

The purpose of this layer is reproducibility. A benchmark result should be
self-describing enough that the operator does not need chat history to explain
what exactly was run.

### 6.2 Case-Level Result

Each `case x variant` result should include at least:

- `case_id`
- `bucket`
- `allow_tool`
- `variant_id`
- `ask_result_mode`
- `answer_text`
- `citations`
- `guardrail_action`
- `guardrail_reason`
- `runtime_faithfulness`
- `provider_name`
- `model_name`
- `latency_ms`
- scoring outputs:
  - matched expected facts
  - missed expected facts
  - forbidden-claim hits
  - final verdict

This level is necessary for later bad-case debugging and for validating that the
aggregate numbers are backed by inspectable evidence.

### 6.3 Variant-Level Aggregate

Each variant aggregate should include at least:

- `answer_correctness`
- `unsupported_claim_rate`
- `generated_answer_rate`
- `retrieval_only_rate`
- `p50_latency_ms`
- `p95_latency_ms`

For full-mode runs, the result should also include a `tool_allowed` subset
aggregate with at least:

- `tool_trigger_rate`
- `expected_tool_hit_rate`
- `tool_case_answer_correctness`

Smoke mode may omit tool-specific aggregates because the fixed smoke subset does
not include `tool_allowed=true` cases.

## 7. Smoke Gate And Failure Semantics

The smoke run should gate the full run, but v1 should not hardcode benchmark
quality thresholds yet.

### 7.1 Automatic Structural Gate

Smoke must fail immediately when any of the following is true:

- canonical provider/model configuration is missing
- benchmark mode or selected cases cannot be resolved
- any variant fails to produce a complete result set
- required metadata fields are missing from the artifact
- the run aborts mid-execution

On structural failure, the benchmark should return a non-zero exit status and
must not write an artifact that looks like a successful benchmark result.

### 7.2 Manual Sanity Gate

After a successful smoke run, the operator reviews whether the numbers and case
behavior look normal enough to justify a full run.

The first-pass sanity questions are:

- do all three variants produce non-empty outputs?
- do the variants differ in plausible ways, rather than collapsing to one
  behavior?
- is `unsupported_claim_rate` obviously broken?
- is `generated_answer_rate` obviously implausible?
- is latency within a reasonable operational range?

This is intentionally a manual gate in v1. The project should first observe
smoke results in practice before locking hard thresholds into the benchmark
contract.

### 7.3 Preflight And Execution Failure

The benchmark should preflight:

- canonical provider/model readiness
- dataset readability
- smoke subset readability when smoke mode is selected
- result metadata prerequisites

If preflight fails, the CLI should exit before execution starts and should not
write a benchmark artifact.

If execution fails after the run starts, the benchmark should fail closed rather
than silently writing a partial "successful" result.

## 8. Testing Strategy

The validation strategy should be split into three layers.

### 8.1 Unit Tests

Add unit tests for:

- fixed smoke subset loading and drift protection
- variant matrix expansion
- deterministic rule scoring
- aggregate metric calculation
- run metadata serialization

These tests should not depend on real provider calls.

### 8.2 Integration Tests

Add integration tests around the benchmark orchestration surface using a
controlled mock or stub provider path.

They should verify:

- smoke/full selection behavior
- execution of all three variants
- fail-closed behavior on incomplete runs
- result schema completeness
- preflight gating behavior

### 8.3 Manual Provider Verification

Real `qwen3.6-flash-2026-04-16` runs remain manual.

The expected operator sequence is:

1. run smoke mode
2. inspect whether the smoke result looks normal
3. only then run full mode
4. inspect a small number of bad cases to ensure rule scoring is not obviously
   misclassifying results

This keeps CI deterministic while still validating the real-provider benchmark
surface.

## 9. Acceptance Criteria Mapping

`TASK-059` should be considered satisfied when the implementation can
demonstrate all of the following:

- there is an answer benchmark entrypoint independent from the regression runner
- the same selected cases can be compared across the three defined variants
- the benchmark runs through the real ask path under canonical cloud model
  `qwen3.6-flash-2026-04-16`
- result artifacts include the required benchmark metadata
- per-variant aggregates include at least:
  - `answer_correctness`
  - `unsupported_claim_rate`
  - `generated_answer_rate`
  - `retrieval_only_rate`
  - `p50_latency_ms`
  - `p95_latency_ms`
- smoke mode uses a fixed committed `10`-case subset
- smoke completes before full mode is expected to run
- automated tests cover preflight/configuration, result aggregation, metadata
  persistence, and deterministic rule scoring

## 10. Open Follow-Ups Deferred Out Of Scope

The following items remain intentionally outside `TASK-059`:

- hardcoded smoke promotion thresholds
- token and cost accounting
- prompt-version lifecycle tooling beyond a minimal version stamp
- multi-provider or multi-model comparison
- report export and interview-facing markdown summaries
- manual calibration workflows and bad-case taxonomy in `TASK-060`

Those follow-ups should build on top of this benchmark surface rather than being
mixed into the first answer benchmark implementation.
