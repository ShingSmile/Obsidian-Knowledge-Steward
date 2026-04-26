# TASK-062 LLM Judge Answer Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional LLM-as-judge semantic correctness scoring to the ask answer benchmark, including both new-run judging and offline artifact replay, while keeping deterministic rule scoring as the default baseline.

**Architecture:** Keep the judge layer inside `backend/app/benchmark/`, separate from the ask runtime. Add a focused judge module for provider config, prompt construction, response parsing, per-record judge scoring, and judge aggregate math; wire it into the existing answer benchmark runner only when explicitly enabled. Add a replay module and CLI that can judge existing `ask_answer` artifacts without rerunning answer generation.

**Tech Stack:** Python 3.12, existing `unittest` suite, Pydantic benchmark dataset models, `dataclasses`, OpenAI-compatible chat completions through the project’s existing provider conventions, JSON benchmark artifacts under `eval/benchmark/` and `eval/results/`.

---

## Scope Check

This is one bounded `medium` task. It extends the existing `TASK-059` answer benchmark scoring layer and operator surface. It does not tune retrieval, answer prompts, context assembly, runtime faithfulness gates, or `eval/run_eval.py`.

Before executing this plan, use `@using-git-worktrees` or otherwise isolate implementation from the current dirty `main` worktree. Use `@test-driven-development` for every behavior change, `@verification-before-completion` before each commit or completion claim, and `@requesting-code-review` after implementation stabilizes.

## Source Spec

- [docs/superpowers/specs/2026-04-25-task-062-llm-judge-answer-benchmark-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-25-task-062-llm-judge-answer-benchmark-design.md)

## File Structure

### Create

- `backend/app/benchmark/ask_answer_benchmark_judge.py`
  - Judge provider config resolution, judge prompt/message construction, JSON response parsing, per-record judge scoring, fail-soft score objects, and judge aggregate helpers.
- `backend/app/benchmark/ask_answer_benchmark_replay.py`
  - Offline artifact replay service: load existing `ask_answer` artifacts, match case records to dataset cases, run judge scoring, merge judge fields, recompute judge aggregates, and write a new artifact.
- `backend/tests/test_ask_answer_benchmark_judge.py`
  - Pure judge config, prompt, parser, score schema, and aggregate tests. No real provider calls.
- `backend/tests/test_ask_answer_benchmark_replay.py`
  - Artifact replay service tests.
- `backend/tests/test_ask_answer_benchmark_judge_cli.py`
  - CLI tests for `eval/benchmark/judge_answer_benchmark_artifact.py`.
- `eval/benchmark/judge_answer_benchmark_artifact.py`
  - Thin CLI for offline replay.

### Modify

- `backend/app/config.py`
  - Add judge-specific environment settings: `judge_provider_name`, `judge_base_url`, `judge_api_key`, `judge_model`.
- `backend/app/benchmark/ask_answer_benchmark_scoring.py`
  - Add rule-score payload helpers and aggregate payload helpers preserving legacy fields as aliases.
- `backend/app/benchmark/ask_answer_benchmark.py`
  - Add optional judge scoring to new benchmark runs.
- `backend/app/benchmark/ask_answer_benchmark_preflight.py`
  - Extend preflight for judge-enabled runs.
- `backend/tests/test_ask_answer_benchmark.py`
  - Add new-run judge integration tests.
- `backend/tests/test_ask_answer_benchmark_scoring.py`
  - Add rule alias aggregate tests.
- `backend/tests/test_ask_answer_benchmark_preflight.py`
  - Add judge-enabled and judge-disabled preflight tests.
- `backend/tests/test_ask_answer_benchmark_cli.py`
  - Add `--judge` and judge config forwarding tests for the existing answer benchmark CLI.
- `eval/benchmark/run_answer_benchmark.py`
  - Add `--judge enabled|disabled` and judge provider/model flags.
- `eval/README.md`
  - Document judge-enabled new runs and artifact replay commands.

### No Changes Expected

- `backend/app/services/ask.py`
  - Judge must not enter the ask runtime or user request path.
- `backend/app/graphs/ask_graph.py`
  - Existing ask graph execution remains unchanged.
- `eval/run_eval.py`
  - Regression runner remains deterministic and judge-free.
- `eval/benchmark/ask_benchmark_cases.json`
  - Dataset schema and cases remain unchanged.

## Implementation Tasks

### Task 1: Add Judge Config, Prompt, Parser, and Score Objects

**Files:**
- Create: `backend/app/benchmark/ask_answer_benchmark_judge.py`
- Create: `backend/tests/test_ask_answer_benchmark_judge.py`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Write failing judge unit tests**

Add `backend/tests/test_ask_answer_benchmark_judge.py` with focused tests for:

- provider config precedence: CLI overrides > `Settings.judge_*` > cloud connection fallback, with `qwen3.6-max-preview` as model fallback
- prompt/message construction includes `user_query`, `expected_facts`, `forbidden_claims`, `answer_text`, and citation snippets
- all five verdicts parse with expected points
- invalid JSON returns `judge_status="parse_error"` with `verdict is None` and `correctness_points is None`
- missing required fields returns `judge_status="invalid_schema"`
- OpenAI-compatible provider calls send the expected `model`, `temperature=0`,
  and judge messages payload; extract response text from `choices[0].message.content`
- provider calls use a finite `urlopen(..., timeout=JUDGE_TIMEOUT_SECONDS)` value
- provider connection failures map to `judge_status="provider_unavailable"` and
  timeout failures map to `judge_status="timeout"`

Use real data objects and mock only provider IO. Example test shape:

```python
import unittest
from dataclasses import replace

from app.benchmark.ask_answer_benchmark_judge import (
    DEFAULT_JUDGE_MODEL,
    JudgeConfigOverrides,
    JudgeInput,
    build_judge_messages,
    parse_judge_response_payload,
    resolve_judge_provider_config,
    score_answer_with_judge,
    JUDGE_TIMEOUT_SECONDS,
)
from app.config import get_settings


class AskAnswerBenchmarkJudgeTests(unittest.TestCase):
    def test_resolve_config_uses_cli_then_judge_env_then_cloud_then_model_default(self) -> None:
        settings = replace(
            get_settings(),
            judge_provider_name="judge-env",
            judge_base_url="https://judge.example/v1",
            judge_api_key="judge-key",
            judge_model="",
            cloud_provider_name="cloud-env",
            cloud_base_url="https://cloud.example/v1",
            cloud_api_key="cloud-key",
            cloud_chat_model="qwen3.6-flash-2026-04-16",
        )

        config = resolve_judge_provider_config(settings=settings, overrides=JudgeConfigOverrides())

        self.assertEqual(config.provider_name, "judge-env")
        self.assertEqual(config.base_url, "https://judge.example/v1")
        self.assertEqual(config.api_key, "judge-key")
        self.assertEqual(config.model_name, DEFAULT_JUDGE_MODEL)
```

Add a provider-call test that patches URL opening instead of calling the network:

```python
def test_score_answer_with_judge_posts_openai_compatible_payload_and_parses_response(self) -> None:
    judge_input = JudgeInput(
        case_id="case-1",
        variant_id="hybrid",
        user_query="Alpha 状态是什么？",
        expected_facts=["Alpha 已完成"],
        forbidden_claims=[],
        answer_text="Alpha 已完成。",
        citations=[],
        ask_result_mode="generated_answer",
        runtime_faithfulness=None,
    )
    provider_config = JudgeProviderConfig(
        provider_name="openai-compatible",
        base_url="https://judge.example/v1",
        api_key="judge-key",
        model_name=DEFAULT_JUDGE_MODEL,
    )
    response_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "verdict": "correct",
                            "matched_facts": ["Alpha 已完成"],
                            "missed_facts": [],
                            "unsupported_claims": [],
                            "reason": "Covers the expected fact.",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }

    with patch("app.benchmark.ask_answer_benchmark_judge.urllib_request.urlopen") as mocked_urlopen:
        mocked_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(
            response_payload,
            ensure_ascii=False,
        ).encode("utf-8")
        score = score_answer_with_judge(judge_input=judge_input, provider_config=provider_config)

    self.assertEqual(score.judge_status, "scored")
    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))
    self.assertEqual(payload["model"], DEFAULT_JUDGE_MODEL)
    self.assertEqual(payload["temperature"], 0)
    self.assertIn("messages", payload)
    self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], JUDGE_TIMEOUT_SECONDS)
    self.assertEqual(request.headers["Content-type"], "application/json")
    self.assertEqual(request.headers["Authorization"], "Bearer judge-key")
```

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_judge -v
```

Expected: FAIL because `ask_answer_benchmark_judge.py` does not exist yet.

- [ ] **Step 3: Implement judge config and parser primitives**

Modify `backend/app/config.py`:

```python
judge_provider_name: str = os.getenv("KS_JUDGE_PROVIDER_NAME", "")
judge_base_url: str = os.getenv("KS_JUDGE_BASE_URL", "")
judge_api_key: str = os.getenv("KS_JUDGE_API_KEY", "")
judge_model: str = os.getenv("KS_JUDGE_MODEL", "")
```

Create `backend/app/benchmark/ask_answer_benchmark_judge.py` with:

```python
DEFAULT_JUDGE_MODEL = "qwen3.6-max-preview"
JUDGE_PROMPT_VERSION = "2026-04-25-answer-judge-v1"
JUDGE_TIMEOUT_SECONDS = 30
JUDGE_VERDICT_POINTS = {
    "correct": 1.0,
    "mostly_correct": 0.75,
    "partial": 0.5,
    "mostly_incorrect": 0.25,
    "incorrect": 0.0,
}
```

Add dataclasses:

- `JudgeConfigOverrides`
- `JudgeProviderConfig`
- `JudgeCitation`
- `JudgeInput`
- `JudgeScore`

Add functions:

- `resolve_judge_provider_config(settings, overrides) -> JudgeProviderConfig`
- `build_judge_messages(judge_input) -> list[dict[str, str]]`
- `parse_judge_response_payload(payload) -> JudgeScore`
- `build_non_scored_judge_score(status, error_reason, raw_response_excerpt=None) -> JudgeScore`
- `score_answer_with_judge(judge_input, provider_config) -> JudgeScore`

Parser rules:

- Accept only verdicts in `JUDGE_VERDICT_POINTS`.
- Missing or non-list `matched_facts`, `missed_facts`, or `unsupported_claims` returns `invalid_schema`.
- Missing or empty `reason` returns `invalid_schema`.
- Invalid JSON returns `parse_error` and preserves a short `raw_response_excerpt`.
- Non-scored scores always include `verdict=None`, `correctness_points=None`, empty fact lists, `reason=None`, and `error_reason`.
- `score_answer_with_judge(...)` uses an OpenAI-compatible
  `/v1/chat/completions` request with `temperature=0`, the configured judge
  model, and `build_judge_messages(...)`.
- `score_answer_with_judge(...)` must call `urllib_request.urlopen` with
  `timeout=JUDGE_TIMEOUT_SECONDS`; judge calls must never wait indefinitely.
- Request headers must include `Content-Type: application/json`, and include
  `Authorization: Bearer <api_key>` when an API key is configured.
- Reuse the existing URL normalization approach from `backend/app/services/ask.py`:
  if the base URL ends with `/chat/completions`, use it as-is; if it ends with
  `/v1`, append `/chat/completions`; otherwise append `/v1/chat/completions`.
- Extract text from `choices[0].message.content`; if content is a list, join
  text parts where `type == "text"`.
- Map `TimeoutError` to `judge_status="timeout"`.
- Map `urllib_error.HTTPError`, `urllib_error.URLError`, `OSError`, and invalid
  provider response shapes to `judge_status="provider_unavailable"`.

- [ ] **Step 4: Run judge unit tests and verify GREEN**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_judge -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add backend/app/config.py \
  backend/app/benchmark/ask_answer_benchmark_judge.py \
  backend/tests/test_ask_answer_benchmark_judge.py
git commit -m "feat: add TASK-062 judge scoring primitives"
```

### Task 2: Add Rule Aggregate Aliases and Judge Aggregate Helpers

**Files:**
- Modify: `backend/app/benchmark/ask_answer_benchmark_scoring.py`
- Modify: `backend/app/benchmark/ask_answer_benchmark_judge.py`
- Modify: `backend/tests/test_ask_answer_benchmark_scoring.py`
- Modify: `backend/tests/test_ask_answer_benchmark_judge.py`

- [ ] **Step 1: Write failing scoring and aggregate tests**

Extend `backend/tests/test_ask_answer_benchmark_scoring.py`:

```python
from app.benchmark.ask_answer_benchmark_scoring import (
    build_rule_score_payload,
    build_rule_variant_aggregate_payload,
)


def test_rule_payload_preserves_existing_fact_details(self) -> None:
    score = score_answer_benchmark_case(
        case=_case(case_id="case-rule", expected_facts=["Alpha 已完成"]),
        ask_result=_ask_result(
            mode=AskResultMode.GENERATED_ANSWER,
            answer="Alpha 已完成。",
        ),
        latency_ms=120,
    )

    self.assertEqual(
        build_rule_score_payload(score),
        {
            "verdict": "correct",
            "correctness_points": 1.0,
            "matched_expected_facts": ["Alpha 已完成"],
            "missed_expected_facts": [],
            "forbidden_claim_hits": [],
        },
    )


def test_rule_aggregate_payload_keeps_legacy_aliases(self) -> None:
    aggregate = aggregate_answer_benchmark_variant_scores(
        variant_id="hybrid",
        case_scores=[
            score_answer_benchmark_case(
                case=_case(case_id="case-rule", expected_facts=["Alpha 已完成"]),
                ask_result=_ask_result(
                    mode=AskResultMode.GENERATED_ANSWER,
                    answer="Alpha 已完成。",
                ),
                latency_ms=120,
            )
        ],
    )
    payload = build_rule_variant_aggregate_payload(aggregate)

    self.assertEqual(payload["answer_correctness"], payload["rule_answer_correctness"])
    self.assertEqual(payload["unsupported_claim_rate"], payload["rule_unsupported_claim_rate"])
```

Extend `backend/tests/test_ask_answer_benchmark_judge.py` with judge aggregate tests:

```python
from app.benchmark.ask_answer_benchmark_judge import aggregate_judge_scores


def test_judge_aggregate_averages_only_scored_records_and_counts_failures(self) -> None:
    aggregate = aggregate_judge_scores(
        [
            JudgeScore(
                judge_status="scored",
                verdict="correct",
                correctness_points=1.0,
                matched_facts=["Alpha"],
                missed_facts=[],
                unsupported_claims=["unsupported beta"],
                reason="Covers the answer.",
                error_reason=None,
                raw_response_excerpt=None,
            ),
            JudgeScore(
                judge_status="scored",
                verdict="mostly_correct",
                correctness_points=0.75,
                matched_facts=["Gamma"],
                missed_facts=[],
                unsupported_claims=[],
                reason="Mostly covers the answer.",
                error_reason=None,
                raw_response_excerpt=None,
            ),
            JudgeScore(
                judge_status="parse_error",
                verdict=None,
                correctness_points=None,
                matched_facts=[],
                missed_facts=[],
                unsupported_claims=[],
                reason=None,
                error_reason="judge_response_not_json",
                raw_response_excerpt="{not json",
            ),
        ]
    )

    self.assertEqual(aggregate["judge_case_count"], 3)
    self.assertEqual(aggregate["judge_scored_count"], 2)
    self.assertEqual(aggregate["judge_failed_count"], 1)
    self.assertEqual(aggregate["judge_answer_correctness"], 0.875)
    self.assertEqual(aggregate["judge_unsupported_claim_rate"], 0.5)
    self.assertEqual(aggregate["judge_scored_rate"], 0.6667)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_scoring \
  backend.tests.test_ask_answer_benchmark_judge -v
```

Expected: FAIL because the payload and aggregate helpers do not exist.

- [ ] **Step 3: Implement rule and judge aggregate helpers**

In `ask_answer_benchmark_scoring.py`, add:

- `build_rule_score_payload(case_score) -> dict[str, object]`
- `build_rule_variant_aggregate_payload(aggregate) -> dict[str, object]`

The aggregate payload must include both legacy and rule-prefixed keys:

```python
payload = asdict(aggregate)
payload["rule_answer_correctness"] = aggregate.answer_correctness
payload["rule_unsupported_claim_rate"] = aggregate.unsupported_claim_rate
```

Do not remove the existing `answer_correctness` or `unsupported_claim_rate`.

In `ask_answer_benchmark_judge.py`, add:

- `judge_score_to_payload(score) -> dict[str, object]`
- `aggregate_judge_scores(scores) -> dict[str, object]`

Formula requirements:

- count every record in `judge_case_count`
- average `correctness_points` over `judge_status == "scored"` only
- compute `judge_unsupported_claim_rate` as scored records with one or more
  `unsupported_claims` divided by `judge_scored_count`
- if zero scored records, set `judge_answer_correctness=0.0`
- round all ratios to four decimals

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_scoring \
  backend.tests.test_ask_answer_benchmark_judge -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

```bash
git add backend/app/benchmark/ask_answer_benchmark_scoring.py \
  backend/app/benchmark/ask_answer_benchmark_judge.py \
  backend/tests/test_ask_answer_benchmark_scoring.py \
  backend/tests/test_ask_answer_benchmark_judge.py
git commit -m "feat: add TASK-062 rule and judge aggregate payloads"
```

### Task 3: Wire Optional Judge Scoring Into New Answer Benchmark Runs

**Files:**
- Modify: `backend/app/benchmark/ask_answer_benchmark.py`
- Modify: `backend/tests/test_ask_answer_benchmark.py`

- [ ] **Step 1: Write failing new-run integration tests**

Extend `backend/tests/test_ask_answer_benchmark.py` with three tests:

1. judge disabled:
   - `judge_run_metadata["judge_enabled"] is False`
   - no per-record `judge_score`
   - no judge aggregate keys
   - existing rule/legacy aggregate fields still exist
2. judge enabled with successful scores:
   - runner calls a mocked judge scorer once per case-variant record
   - records include `rule_score` and `judge_score`
   - aggregates include judge counts and `judge_answer_correctness`
3. judge enabled with non-scored result:
   - runner still returns `run_status="passed"`
   - record includes stable non-scored `judge_score`
   - aggregate counts failure in `judge_failed_count`

Example assertion shape:

```python
with patch(
    "app.benchmark.ask_answer_benchmark.score_answer_with_judge",
    return_value=JudgeScore(
        judge_status="scored",
        verdict="mostly_correct",
        correctness_points=0.75,
        matched_facts=["Alpha"],
        missed_facts=[],
        unsupported_claims=[],
        reason="Covers the core answer.",
    ),
) as mocked_judge:
    result = run_ask_answer_benchmark(
        settings=settings,
        mode="smoke",
        output_path=output_path,
        judge_enabled=True,
        judge_provider_config=judge_config,
    )

self.assertEqual(mocked_judge.call_count, 30)
self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_scored_rate"], 1.0)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark -v
```

Expected: FAIL because `run_ask_answer_benchmark(...)` does not accept judge options and records do not include judge fields.

- [ ] **Step 3: Implement optional judge scoring in the runner**

Modify `run_ask_answer_benchmark(...)` signature:

```python
def run_ask_answer_benchmark(
    settings: Settings,
    mode: Literal["smoke", "full"],
    dataset_path: Path | None = None,
    output_path: Path | None = None,
    *,
    judge_enabled: bool = False,
    judge_provider_config: JudgeProviderConfig | None = None,
) -> dict[str, Any]:
```

Implementation details:

- Always add `rule_score` to each case record using `build_rule_score_payload(...)`.
- Keep legacy per-record fields for compatibility.
- When `judge_enabled=False`, omit per-record `judge_score`, omit judge aggregate keys, and add `judge_run_metadata={"judge_enabled": False}`.
- When `judge_enabled=True`, call `score_answer_with_judge(...)` for each case record after rule score.
- Build `JudgeInput` from dataset case, answer text, citations, variant id, ask result mode, and runtime faithfulness.
- Merge judge aggregate payloads into each variant aggregate.
- Add `judge_run_metadata` with provider/model/prompt/timestamp.

Do not let non-scored judge results change `run_status`.

- [ ] **Step 4: Run integration tests and verify GREEN**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark \
  backend.tests.test_ask_answer_benchmark_judge \
  backend.tests.test_ask_answer_benchmark_scoring -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 3**

```bash
git add backend/app/benchmark/ask_answer_benchmark.py \
  backend/tests/test_ask_answer_benchmark.py
git commit -m "feat: add optional judge scoring to answer benchmark"
```

### Task 4: Extend Answer Benchmark Preflight and CLI Judge Flags

**Files:**
- Modify: `backend/app/benchmark/ask_answer_benchmark_preflight.py`
- Modify: `backend/tests/test_ask_answer_benchmark_preflight.py`
- Modify: `eval/benchmark/run_answer_benchmark.py`
- Modify: `backend/tests/test_ask_answer_benchmark_cli.py`

- [ ] **Step 1: Write failing preflight and CLI tests**

Preflight tests:

- disabled judge does not require judge config
- enabled judge fails startup when base URL is missing
- enabled judge uses `qwen3.6-max-preview` when no judge model is configured
- missing API key is not a startup failure

CLI tests:

- default `--judge` is disabled
- `--judge enabled` resolves judge config and passes it to preflight and runner
- CLI flags override settings/env-derived config
- `--judge-model qwen3.6-max-preview` is accepted and forwarded

Example CLI assertion:

```python
exit_code = module.main(
    [
        "--mode",
        "smoke",
        "--judge",
        "enabled",
        "--judge-provider-name",
        "openai-compatible",
        "--judge-base-url",
        "https://judge.example/v1",
        "--judge-model",
        "qwen3.6-max-preview",
    ]
)

_, kwargs = mocked_run_benchmark.call_args
self.assertTrue(kwargs["judge_enabled"])
self.assertEqual(kwargs["judge_provider_config"].model_name, "qwen3.6-max-preview")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_preflight \
  backend.tests.test_ask_answer_benchmark_cli -v
```

Expected: FAIL because preflight and CLI do not support judge flags yet.

- [ ] **Step 3: Implement preflight and CLI changes**

In `ask_answer_benchmark_preflight.py`:

- Extend `run_answer_benchmark_preflight(...)` with:
  - `judge_enabled: bool = False`
  - `judge_provider_config: JudgeProviderConfig | None = None`
- Preserve existing answer provider/canonical model checks.
- If `judge_enabled=False`, skip judge readiness.
- If `judge_enabled=True`, fail when `judge_provider_config.base_url` or `.model_name` is empty.
- Do not fail on missing API key.

In `eval/benchmark/run_answer_benchmark.py`:

- Add parser args:
  - `--judge` choices `enabled|disabled`, default `disabled`
  - `--judge-provider-name`
  - `--judge-base-url`
  - `--judge-api-key`
  - `--judge-model`
- Build `JudgeConfigOverrides` from CLI args.
- Resolve `JudgeProviderConfig` once.
- Pass `judge_enabled` and config to preflight and runner.

- [ ] **Step 4: Run tests and verify GREEN**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_preflight \
  backend.tests.test_ask_answer_benchmark_cli \
  backend.tests.test_ask_answer_benchmark -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 4**

```bash
git add backend/app/benchmark/ask_answer_benchmark_preflight.py \
  backend/tests/test_ask_answer_benchmark_preflight.py \
  eval/benchmark/run_answer_benchmark.py \
  backend/tests/test_ask_answer_benchmark_cli.py
git commit -m "feat: add TASK-062 judge CLI and preflight"
```

### Task 5: Add Offline Artifact Replay Service and CLI

**Files:**
- Create: `backend/app/benchmark/ask_answer_benchmark_replay.py`
- Create: `backend/tests/test_ask_answer_benchmark_replay.py`
- Create: `eval/benchmark/judge_answer_benchmark_artifact.py`
- Create: `backend/tests/test_ask_answer_benchmark_judge_cli.py`

- [ ] **Step 1: Write failing replay service tests**

Create minimal legacy artifact fixtures in tests. Cover:

- rejects artifact when `benchmark_kind != "ask_answer"`
- adds `judge_score` to valid legacy records
- preserves original top-level metadata
- adds `judge_run_metadata` with `judge_enabled`, judge provider/model, prompt
  version, run timestamp, and `source_artifact_path`
- records dataset version mismatch warning in
  `judge_run_metadata["warnings"]` as
  `{"code": "dataset_version_mismatch", "artifact_dataset_version": ..., "current_dataset_version": ...}`
- initializes `judge_run_metadata["warnings"]` as an empty list when there are no
  warnings
- backfills `rule_answer_correctness` and `rule_unsupported_claim_rate` aliases
  for legacy variant aggregates
- skips records missing `case_id`, `variant_id`, `answer_text`, or `citations`
- skipped records get `judge_status="skipped_missing_record_fields"` and stable non-scored schema
- mocks `score_answer_with_judge(...)` so replay service tests never make real
  provider calls

Example replay assertion:

```python
result = judge_answer_benchmark_artifact(
    input_path=input_path,
    output_path=output_path,
    settings=settings,
    dataset_path=dataset_path,
    judge_provider_config=judge_config,
)

record = result["case_variant_records"][0]
self.assertEqual(record["judge_score"]["judge_status"], "scored")
self.assertEqual(result["judge_run_metadata"]["source_artifact_path"], str(input_path))
self.assertTrue(result["judge_run_metadata"]["judge_enabled"])
self.assertEqual(result["judge_run_metadata"]["judge_provider_name"], "openai-compatible")
self.assertEqual(result["judge_run_metadata"]["judge_model_name"], "qwen3.6-max-preview")
self.assertEqual(result["judge_run_metadata"]["judge_prompt_version"], "2026-04-25-answer-judge-v1")
self.assertIn("judge_run_timestamp", result["judge_run_metadata"])
self.assertEqual(result["variant_aggregates"]["hybrid"]["judge_scored_rate"], 1.0)
```

- [ ] **Step 2: Write failing replay CLI tests**

Create `backend/tests/test_ask_answer_benchmark_judge_cli.py` using the existing importlib CLI pattern from `test_ask_answer_benchmark_cli.py`.

Cover:

- missing input returns exit code `1`
- wrong artifact kind returns exit code `1`
- missing judge base URL returns exit code `1`
- missing resolved judge model returns exit code `1`
- `--judge-model qwen3.6-max-preview` is accepted and forwarded
- valid input forwards `--input`, `--output`, `--dataset`, and judge config flags

- [ ] **Step 3: Run replay tests and verify RED**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_replay \
  backend.tests.test_ask_answer_benchmark_judge_cli -v
```

Expected: FAIL because replay module and CLI do not exist.

- [ ] **Step 4: Implement replay service**

Create `backend/app/benchmark/ask_answer_benchmark_replay.py` with:

- `judge_answer_benchmark_artifact(...) -> dict[str, Any]`
- `load_answer_benchmark_artifact(path) -> dict[str, Any]`
- `write_answer_benchmark_artifact(result, path) -> Path`
- record validation helpers
- variant regrouping and judge aggregate recomputation

Rules:

- Do not overwrite source artifact unless output path explicitly points to same path.
- Validate startup-level inputs and raise `ValueError` for wrong kind.
- Load dataset with `load_ask_benchmark_dataset(dataset_path)`.
- Match by `case_id`.
- For missing dataset cases, emit `judge_status="skipped_missing_dataset_case"`.
- Preserve original artifact metadata and existing record fields.
- Add `judge_run_metadata` with:
  - `judge_enabled: true`
  - `judge_provider_name`
  - `judge_model_name`
  - `judge_prompt_version`
  - `judge_run_timestamp`
  - `source_artifact_path`
  - `warnings`, always present as a list
- Recompute judge aggregate keys while keeping existing runtime aggregate fields
  intact.
- Ensure every variant aggregate also has `rule_answer_correctness` and
  `rule_unsupported_claim_rate`; when replaying legacy artifacts, backfill those
  from existing `answer_correctness` and `unsupported_claim_rate` if rule-prefixed
  keys are absent.
- Use `judge_run_metadata["warnings"]` as a list of objects. For dataset version
  mismatch, append:
  `{"code": "dataset_version_mismatch", "artifact_dataset_version": <artifact>, "current_dataset_version": <dataset>}`.

- [ ] **Step 5: Implement replay CLI**

Create `eval/benchmark/judge_answer_benchmark_artifact.py`:

- Parse:
  - `--input` required
  - `--output` required
  - `--dataset`
  - same judge flags as `run_answer_benchmark.py`
- Load settings and resolve judge config.
- Validate that resolved judge config has a non-empty base URL and model before
  invoking replay. Missing base URL/model is a startup error with exit code `1`.
  Missing API key is allowed.
- Add separate CLI tests for missing base URL and missing model. The missing
  model test can patch config resolution to return `JudgeProviderConfig` with
  `model_name=""`, then assert exit code `1` and that replay service is not
  called.
- Return exit code `1` for startup errors.
- Print concise `ERROR: ...` to stderr on failure.

- [ ] **Step 6: Run replay tests and verify GREEN**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_replay \
  backend.tests.test_ask_answer_benchmark_judge_cli \
  backend.tests.test_ask_answer_benchmark_judge -v
```

Expected: PASS.

- [ ] **Step 7: Commit Task 5**

```bash
git add backend/app/benchmark/ask_answer_benchmark_replay.py \
  backend/tests/test_ask_answer_benchmark_replay.py \
  eval/benchmark/judge_answer_benchmark_artifact.py \
  backend/tests/test_ask_answer_benchmark_judge_cli.py
git commit -m "feat: add TASK-062 artifact judge replay"
```

### Task 6: Document Operator Commands and Run Focused Verification

**Files:**
- Modify: `eval/README.md`

- [ ] **Step 1: Write the README update**

Update `eval/README.md` under `Operator Entry Points` with:

```bash
set -a; source backend/.env; set +a
./.conda/knowledge-steward/bin/python eval/benchmark/run_answer_benchmark.py \
  --mode smoke \
  --judge enabled \
  --judge-model qwen3.6-max-preview \
  --output /tmp/task-062-smoke-judged.json

./.conda/knowledge-steward/bin/python eval/benchmark/judge_answer_benchmark_artifact.py \
  --input /tmp/task-059-answer-benchmark-smoke-final-20260424.json \
  --output /tmp/task-059-answer-benchmark-smoke-judged.json \
  --judge-model qwen3.6-max-preview
```

Also state:

- judge is disabled by default
- judge does not run in `eval/run_eval.py`
- judge failures do not overwrite rule score

- [ ] **Step 2: Run all targeted benchmark tests**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark \
  backend.tests.test_ask_answer_benchmark_scoring \
  backend.tests.test_ask_answer_benchmark_judge \
  backend.tests.test_ask_answer_benchmark_preflight \
  backend.tests.test_ask_answer_benchmark_cli \
  backend.tests.test_ask_answer_benchmark_replay \
  backend.tests.test_ask_answer_benchmark_judge_cli -v
```

Expected: PASS.

- [ ] **Step 3: Run adjacent retrieval benchmark tests**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_retrieval_benchmark \
  backend.tests.test_ask_retrieval_preflight -v
```

Expected: PASS.

- [ ] **Step 4: Run static diff check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 5: Commit Task 6**

```bash
git add eval/README.md
git commit -m "docs: document TASK-062 judge benchmark commands"
```

### Task 7: Final Verification and Handoff Notes

**Files:**
- No production edits expected unless verification exposes a defect.

- [ ] **Step 1: Run final targeted suite**

Run:

```bash
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark \
  backend.tests.test_ask_answer_benchmark_scoring \
  backend.tests.test_ask_answer_benchmark_judge \
  backend.tests.test_ask_answer_benchmark_preflight \
  backend.tests.test_ask_answer_benchmark_cli \
  backend.tests.test_ask_answer_benchmark_replay \
  backend.tests.test_ask_answer_benchmark_judge_cli \
  backend.tests.test_ask_workflow \
  backend.tests.test_faithfulness -v
```

Expected: PASS.

- [ ] **Step 2: Run `git diff --check`**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 3: Confirm no regression runner changes**

Run:

```bash
git diff --name-only HEAD~6..HEAD | rg '^eval/run_eval.py$' || true
```

Expected: no output.

- [ ] **Step 4: Summarize manual real-provider verification without running it by default**

Do not run real provider commands unless the human explicitly asks. Record the manual commands in handoff:

```bash
set -a; source backend/.env; set +a
./.conda/knowledge-steward/bin/python eval/benchmark/run_answer_benchmark.py \
  --mode smoke \
  --judge enabled \
  --judge-model qwen3.6-max-preview \
  --output /tmp/task-062-smoke-judged.json
```

- [ ] **Step 5: Prepare governed-session closeout facts**

Do not update governance docs unless the human asks for closeout. Prepare facts for later:

- task: `TASK-062`
- session: `SES-20260425-01`
- implementation commits
- tests run and results
- whether real provider judge was manually run
- whether derived tasks were created
