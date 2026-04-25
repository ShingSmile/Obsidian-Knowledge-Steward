# TASK-062 LLM Judge Answer Benchmark Design

**Task:** `TASK-062`

**Session:** `SES-20260425-01`

**Problem**

`TASK-059` added the real-provider ask answer benchmark. It can run the fixed
ask benchmark dataset through the real ask path, compare `hybrid`,
`hybrid_assembly`, and `hybrid_assembly_gate`, and write deterministic
rule-based correctness numbers. That was enough to prove that the answer
benchmark runner, provider wiring, prompt-version metadata, variant toggles, and
artifact writing work.

The remaining gap is correctness interpretation. The current
`answer_correctness` metric is based on normalized substring checks against
`expected_facts` and `forbidden_claims`. That makes it cheap and repeatable, but
it can misclassify semantically correct answers when the wording is different
from the dataset phrase. It can also make variant comparisons look worse or
better for the wrong reason.

`TASK-062` adds an optional LLM-as-judge layer next to the deterministic rule
score. The goal is not to make benchmark results more opaque. The goal is to
separate two signals:

- `rule_score` remains the deterministic smoke and drift-protection signal.
- `judge_score` becomes the semantic correctness signal used to interpret answer
  quality, context assembly impact, and runtime gate trade-offs.

**Goal**

Create an optional judge layer for the ask answer benchmark that:

- supports new answer benchmark runs with judge scoring enabled
- supports offline replay over existing answer benchmark artifacts without
  rerunning answer generation
- keeps rule scoring as the default deterministic baseline
- records judge provider/model/prompt metadata separately from the original
  answer-generation metadata
- fails soft per case when judge provider calls, JSON parsing, or schema
  validation fail
- aggregates rule correctness and judge correctness side by side

**Non-Goals**

- Do not put the judge in the ask runtime or user request path.
- Do not remove existing rule-based scoring or legacy artifact fields.
- Do not modify retrieval, context assembly, runtime faithfulness gate, or answer
  prompts as part of this task.
- Do not extend `eval/run_eval.py`; regression remains separate from the
  resume-grade answer benchmark.
- Do not add multi-judge model comparison in this task.
- Do not make full benchmark judge calls automatic or implicit.

**Approaches Considered**

1. Add an independent judge scorer plus artifact replay, reused by both new runs
   and offline rejudging.
   Recommended because it keeps provider IO out of deterministic scoring, keeps
   the replay path cheap, and preserves the existing benchmark boundary.
2. Put judge calls directly in `ask_answer_benchmark_scoring.py`.
   Rejected because that module should stay pure and deterministic. Mixing rule
   scoring with network calls would make tests and failure handling weaker.
3. Only add an artifact post-processor and leave new runs unchanged.
   Rejected because new benchmark runs should be able to emit a complete
   rule-plus-judge artifact when the operator explicitly enables judge scoring.

**Recommended Approach**

Add a focused judge module and two benchmark entrypoints that share it.

- `backend/app/benchmark/ask_answer_benchmark_judge.py`
  Owns judge prompt construction, provider calls, JSON parsing, structured
  result objects, status mapping, and aggregate helpers.
- `backend/app/benchmark/ask_answer_benchmark_scoring.py`
  Continues to own deterministic rule scoring. It can expose clearer `rule_*`
  payload helpers, but it should not call providers.
- `backend/app/benchmark/ask_answer_benchmark.py`
  Adds an optional judge path after rule scoring during new benchmark runs.
- `backend/app/benchmark/ask_answer_benchmark_preflight.py`
  Adds judge readiness checks only when judge scoring is enabled.
- `eval/benchmark/run_answer_benchmark.py`
  Adds explicit judge flags for new runs.
- `eval/benchmark/judge_answer_benchmark_artifact.py`
  Adds offline artifact replay: read an existing answer benchmark artifact,
  score its case records with the judge, recompute judge aggregates, and write a
  new artifact.

The operator surface should be explicit:

```bash
python eval/benchmark/run_answer_benchmark.py \
  --mode smoke \
  --judge enabled \
  --judge-model qwen3.6-max-preview \
  --output /tmp/answer-smoke-judged.json

python eval/benchmark/judge_answer_benchmark_artifact.py \
  --input /tmp/task-059-answer-benchmark-smoke-final-20260424.json \
  --judge-model qwen3.6-max-preview \
  --output /tmp/task-059-answer-benchmark-smoke-judged.json
```

Judge scoring defaults to disabled. Enabling it is always an explicit operator
choice.

## 1. Architecture Boundary

The judge layer belongs to the benchmark system, not the product runtime.

The existing ask path remains responsible for retrieval, context assembly,
tool-call selection, answer generation, guardrails, citations, and runtime
faithfulness. The benchmark remains responsible for selecting cases, executing
variants, scoring results, aggregating metrics, and writing artifacts.

The judge layer is a benchmark scoring component. It receives already-produced
answers and case metadata, and it emits a structured semantic correctness score.
It must never feed back into the generated answer or change `AskWorkflowResult`.

This boundary keeps the judge safe to use for analysis while preserving the
determinism and debuggability of the underlying ask runtime.

## 2. Artifact Contract

The artifact should remain backward-compatible with `TASK-059`, while adding a
clear v2 scoring shape.

Existing `case_variant_records` fields such as `final_verdict`,
`matched_expected_facts`, `missed_expected_facts`, and `forbidden_claim_hits`
can remain for one compatibility cycle. New code should also write an explicit
`rule_score` object:

```json
{
  "rule_score": {
    "verdict": "partial",
    "correctness_points": 0.5,
    "matched_expected_facts": ["..."],
    "missed_expected_facts": ["..."],
    "forbidden_claim_hits": []
  }
}
```

When judge scoring is enabled, each record also gets `judge_score`:

```json
{
  "judge_score": {
    "judge_status": "scored",
    "verdict": "correct",
    "correctness_points": 1.0,
    "matched_facts": ["..."],
    "missed_facts": [],
    "unsupported_claims": [],
    "reason": "The answer covers all required facts without unsupported claims."
  }
}
```

For non-scored judge attempts, `judge_score` must keep the same top-level shape
so tests and downstream readers can rely on stable fields:

```json
{
  "judge_score": {
    "judge_status": "parse_error",
    "verdict": null,
    "correctness_points": null,
    "matched_facts": [],
    "missed_facts": [],
    "unsupported_claims": [],
    "reason": null,
    "error_reason": "judge_response_not_json",
    "raw_response_excerpt": "{not json..."
  }
}
```

`raw_response_excerpt` is only required for `parse_error` and `invalid_schema`;
other failure statuses can omit it or set it to `null`. `error_reason` should be
a stable machine-readable string, not a long provider exception dump.

When judge is disabled, per-record `judge_score` is omitted entirely. The
artifact-level `judge_run_metadata` records `judge_enabled=false`. Disabled
runs do not emit judge aggregates.

Judge metadata must not overwrite original answer-generation metadata. The
artifact should include a separate block:

```json
{
  "judge_run_metadata": {
    "judge_enabled": true,
    "judge_provider_name": "openai-compatible",
    "judge_model_name": "qwen3.6-max-preview",
    "judge_prompt_version": "2026-04-25-answer-judge-v1",
    "judge_run_timestamp": "2026-04-25T12:00:00",
    "source_artifact_path": "/tmp/task-059-answer-benchmark-smoke-final-20260424.json"
  }
}
```

Variant aggregates should report both rule and judge metrics:

- `answer_correctness`
- `unsupported_claim_rate`
- `rule_answer_correctness`
- `rule_unsupported_claim_rate`
- `judge_answer_correctness`
- `judge_unsupported_claim_rate`
- `judge_case_count`
- `judge_scored_count`
- `judge_failed_count`
- `judge_scored_rate`
- `judge_failed_rate`

For compatibility, existing aggregate fields remain in place:

- `answer_correctness` remains as a legacy alias for
  `rule_answer_correctness`.
- `unsupported_claim_rate` remains as a legacy alias for
  `rule_unsupported_claim_rate`.
- `generated_answer_rate`, `retrieval_only_rate`, `p50_latency_ms`,
  `p95_latency_ms`, and tool subset metrics keep their existing names.

Judge aggregate formulas:

- `judge_case_count = total case_variant_records for that variant`
- `judge_scored_count = count(judge_status == "scored")`
- `judge_failed_count = judge_case_count - judge_scored_count`
- `judge_scored_rate = judge_scored_count / judge_case_count`
- `judge_failed_rate = judge_failed_count / judge_case_count`
- `judge_answer_correctness = average(correctness_points)` over scored records
  only
- `judge_unsupported_claim_rate = scored records with one or more
  `unsupported_claims` divided by `judge_scored_count`

All ratios should be rounded to four decimals. If `judge_case_count` is zero,
all judge counts are zero and rates are `0.0`. If `judge_scored_count` is zero,
`judge_answer_correctness` and `judge_unsupported_claim_rate` are `0.0`; the
low `judge_scored_rate` makes the result explicitly non-authoritative.

## 3. Data Flow

### 3.1 New Benchmark Run

The new-run flow is:

1. load dataset
2. select smoke or full case set
3. execute each `case x variant` through the existing ask graph
4. compute deterministic rule score
5. if judge is enabled, compute judge score
6. write case records and variant aggregates
7. write artifact metadata and judge metadata

If a single judge call fails, the case record receives a non-`scored`
`judge_status`, and the benchmark continues. The overall benchmark run does not
become failed unless the startup preflight or answer benchmark execution fails.

### 3.2 Offline Artifact Replay

The replay flow is:

1. load an existing answer benchmark artifact
2. verify `benchmark_kind == "ask_answer"`
3. load the current benchmark dataset
4. match artifact records back to dataset cases by `case_id`
5. build judge inputs from artifact record plus dataset case
6. add or replace `judge_score`
7. recompute judge aggregates
8. preserve original artifact metadata and add `judge_run_metadata`
9. write a new artifact

Replay must not mutate the source artifact in place by default. If an operator
needs overwrite behavior later, it should be an explicit flag.

If the artifact dataset version differs from the current dataset version, replay
should continue with a warning in `judge_run_metadata`, because old smoke
artifacts may still be useful for analysis. The warning means the result should
not be used as a formal apples-to-apples benchmark comparison.

## 4. Judge Input And Prompt

The judge prompt should be rubric-driven and JSON-only. It should not ask the
judge for an open-ended quality review.

Each judge request should include:

- `user_query`
- `expected_facts`
- `forbidden_claims`
- `answer_text`
- visible citation snippets with `path`, `heading_path`, and `snippet`
- optional context: `variant_id`, `ask_result_mode`, and `runtime_faithfulness`

The required judge response is:

```json
{
  "verdict": "correct|mostly_correct|partial|mostly_incorrect|incorrect",
  "matched_facts": ["..."],
  "missed_facts": ["..."],
  "unsupported_claims": ["..."],
  "reason": "short explanation"
}
```

Verdict mapping:

- `correct` -> `1.0`
- `mostly_correct` -> `0.75`
- `partial` -> `0.5`
- `mostly_incorrect` -> `0.25`
- `incorrect` -> `0.0`

The five levels should be interpreted as:

- `correct`: all required facts are covered, and there are no unsupported or
  forbidden claims.
- `mostly_correct`: the answer covers the central facts but has a minor omission
  or imprecise wording that does not change the final meaning.
- `partial`: the answer covers some required facts but misses material facts or
  gives an incomplete answer.
- `mostly_incorrect`: the answer contains a small amount of relevant material
  but misses the main answer, or the useful content is outweighed by omissions.
- `incorrect`: the answer is mostly wrong, unsupported, refuses when it should
  answer, or contains forbidden/unsupported claims that change the answer.

The prompt must instruct the judge to mark unsupported claims when the answer
adds claims that are not supported by the visible citations, even if those claims
are not explicitly listed in `forbidden_claims`.

## 5. Provider Configuration

Judge provider/model should be configurable and decoupled from the generation
model.

The recommended default judge model for `TASK-062` is
`qwen3.6-max-preview`, while the answer-generation benchmark can continue to use
the `TASK-059` canonical answer model. The first implementation can reuse
`KS_CLOUD_*` connection settings as defaults, but the CLI should allow explicit
judge overrides:

- `--judge-provider-name`
- `--judge-base-url`
- `--judge-api-key`
- `--judge-model`

Both `run_answer_benchmark.py` and `judge_answer_benchmark_artifact.py` should
support the same judge configuration flags. The resolution precedence is:

1. explicit CLI flag
2. judge-specific environment variable:
   - `KS_JUDGE_PROVIDER_NAME`
   - `KS_JUDGE_BASE_URL`
   - `KS_JUDGE_API_KEY`
   - `KS_JUDGE_MODEL`
3. cloud connection fallback for provider name, base URL, and API key:
   - `KS_CLOUD_PROVIDER_NAME`
   - `KS_CLOUD_BASE_URL`
   - `KS_CLOUD_API_KEY`
4. model fallback: `qwen3.6-max-preview`

`KS_CLOUD_CHAT_MODEL` is not the default judge model, because judge and answer
generation are intentionally decoupled. A missing judge base URL or judge model
when judge is enabled is a startup preflight failure. A missing API key is not a
startup failure, because some OpenAI-compatible endpoints may not require one;
provider authentication failures are recorded per record as
`provider_unavailable`.

When judge is disabled, no judge provider readiness check should run. When judge
is enabled, preflight should verify that a base URL and model are available.

Full mode does not automatically enable judge. The operator must still pass
`--judge enabled`.

## 6. Error Handling

Judge failures are per-record failures. They should be visible in artifacts but
should not erase rule scores.

Recommended statuses:

- `scored`
- `provider_unavailable`
- `timeout`
- `parse_error`
- `invalid_schema`
- `skipped_missing_record_fields`
- `skipped_missing_dataset_case`

For parse errors, keep a short `raw_response_excerpt` for debugging. Avoid
storing entire long model responses unless there is a clear need.

Startup-level failures should still return a non-zero CLI exit:

- input artifact missing or unreadable
- input artifact is not JSON
- input artifact is not an `ask_answer` benchmark artifact
- dataset unreadable
- output path unwritable

## 7. Testing Strategy

Unit tests should avoid real provider calls.

Pure judge tests:

- prompt payload includes query, expected facts, forbidden claims, answer text,
  and citations
- valid JSON parses into `judge_score`
- `correct`, `mostly_correct`, `partial`, `mostly_incorrect`, and `incorrect`
  map to the expected points
- invalid JSON returns `parse_error`
- missing fields return `invalid_schema`
- unsupported claims are preserved in the structured result

Artifact replay tests:

- a legacy `TASK-059` artifact receives `judge_score` without losing original
  fields
- original artifact metadata is preserved
- `judge_run_metadata` is added
- non-scored judge results preserve the stable `judge_score` shape with
  `verdict=null` and `correctness_points=null`
- disabled judge runs omit per-record `judge_score` and judge aggregates
- legacy aggregate fields remain as aliases for rule aggregates
- dataset version mismatch records a warning
- missing per-record fields produce skipped records, not a failed replay

CLI and preflight tests:

- `run_answer_benchmark.py --judge disabled` does not require judge provider
  settings
- `run_answer_benchmark.py --judge enabled` checks judge settings
- both judge-capable CLIs use the same judge provider precedence:
  CLI > `KS_JUDGE_*` > `KS_CLOUD_*` connection fallback, with model fallback to
  `qwen3.6-max-preview`
- `judge_answer_benchmark_artifact.py` rejects missing, invalid, or wrong-kind
  artifacts
- both CLIs return non-zero for startup failures

Manual verification can use real provider calls:

```bash
python eval/benchmark/run_answer_benchmark.py \
  --mode smoke \
  --judge enabled \
  --judge-model qwen3.6-max-preview \
  --output /tmp/answer-smoke-judged.json

python eval/benchmark/judge_answer_benchmark_artifact.py \
  --input /tmp/task-059-answer-benchmark-smoke-final-20260424.json \
  --judge-model qwen3.6-max-preview \
  --output /tmp/task-059-answer-benchmark-smoke-judged.json
```

## 8. Acceptance Criteria

- New answer benchmark runs can optionally emit `rule_score` and `judge_score`
  in the same artifact.
- Existing answer benchmark artifacts can be judged offline without rerunning
  answer generation.
- Rule correctness remains available and is not overwritten by judge failures.
- Variant aggregates include both `rule_answer_correctness` and
  `judge_answer_correctness`.
- Judge aggregate formulas define exact denominators and zero-scored behavior.
- Non-scored judge attempts use a stable `judge_score` schema with nullable
  verdict and points plus a machine-readable `error_reason`.
- Disabled judge runs omit per-record `judge_score` and judge aggregates.
- Legacy aggregate fields remain as aliases for rule aggregate fields.
- Judge provider/model metadata is recorded separately from the original
  answer-generation metadata.
- The recommended judge model is `qwen3.6-max-preview`, configurable separately
  from the `TASK-059` answer-generation model.
- Judge correctness uses five scoring levels: `correct=1.0`,
  `mostly_correct=0.75`, `partial=0.5`, `mostly_incorrect=0.25`, and
  `incorrect=0.0`.
- Judge disabled mode remains the default and does not require provider
  readiness.
- Unit tests cover all five judge verdict levels, unsupported claims, parse
  failure, invalid schema, disabled mode, and artifact replay.
