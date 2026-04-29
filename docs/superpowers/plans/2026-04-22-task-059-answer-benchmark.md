# TASK-059 Answer Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-provider ask answer benchmark for `TASK-059` that runs `qwen-max` across a fixed `10`-case smoke subset or the full `50`-case dataset, compares three ablation variants, scores outputs with deterministic rules, and writes self-describing result artifacts without modifying the existing regression runner.

**Architecture:** Keep regression and answer benchmarking separate. Add a benchmark-owned smoke subset file, variant/config helpers, deterministic scoring and aggregation modules, and a dedicated answer benchmark runner under `backend/app/benchmark/` plus a thin CLI under `eval/benchmark/`. Reuse the real ask graph for execution, but thread benchmark metadata through the ask workflow so the benchmark can explicitly disable context assembly or runtime gate behavior without introducing a second answer-generation implementation.

**Tech Stack:** Python 3.12, FastAPI/Pydantic workflow contracts already in `backend/app/`, LangGraph ask workflow, existing benchmark dataset in `eval/benchmark/`, SQLite-backed runtime/checkpoints, `unittest`, importlib-based CLI tests, `qwen-max` via the configured cloud provider.

---

## Scope Check

Keep this as one implementation plan. The fixed smoke subset, ask-runtime
variant hooks, deterministic scoring, benchmark orchestration, and CLI surface
are all one bounded subsystem from the approved `TASK-059` spec:
[2026-04-22-task-059-answer-benchmark-design.md](/Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/docs/superpowers/specs/2026-04-22-task-059-answer-benchmark-design.md)

Do **not** expand this plan into:

- rerank work
- multi-provider or multi-model comparison
- LLM judge scoring
- CI automation for real-provider runs
- `TASK-060` manual review, taxonomy, or report export
- governance doc sync in `docs/TASK_QUEUE.md`, `docs/CURRENT_STATE.md`, or
  `docs/SESSION_LOG.md` during implementation

## File Structure

### Create

- `backend/app/benchmark/ask_answer_benchmark_variants.py`
  - Fixed smoke subset loader, variant definitions, metadata helpers, and
    benchmark-mode constants.
- `backend/app/benchmark/ask_answer_benchmark_scoring.py`
  - Deterministic case scoring plus per-variant aggregate calculations.
- `backend/app/benchmark/ask_answer_benchmark.py`
  - Benchmark orchestration, synthetic ask invocations, result assembly, output
    path helpers, and artifact writing.
- `backend/app/benchmark/ask_answer_benchmark_preflight.py`
  - Structured config/file readiness checks for smoke/full runs.
- `backend/tests/test_ask_answer_benchmark.py`
  - Smoke/full selection, variant expansion, artifact metadata, and
    orchestration behavior.
- `backend/tests/test_ask_answer_benchmark_scoring.py`
  - Deterministic verdict and aggregate math tests.
- `backend/tests/test_ask_answer_benchmark_preflight.py`
  - Cloud-provider/model readiness and subset/dataset readability checks.
- `backend/tests/test_ask_answer_benchmark_cli.py`
  - CLI argument forwarding, preflight gating, and exit-status behavior.
- `eval/benchmark/ask_answer_benchmark_smoke_cases.json`
  - Fixed committed `10`-case smoke subset.
- `eval/benchmark/run_answer_benchmark.py`
  - Thin CLI entrypoint for smoke/full answer benchmark runs.

### Modify

- `backend/app/services/ask.py`
  - Read benchmark metadata, support `context assembly` on/off, support
    `runtime faithfulness gate` on/off while still recording the signal, and
    expose a prompt-version stamp helper for benchmark metadata.
- `backend/app/graphs/ask_graph.py`
  - Pass benchmark metadata through the finalize path so runtime-gate toggles
    are applied consistently when the real ask graph runs.
- `backend/app/context/render.py`
  - Add explicit prompt-version constants for grounded answer and tool
    selection prompts.
- `backend/tests/test_ask_workflow.py`
  - Lock benchmark variant behavior in the real ask workflow.
- `eval/README.md`
  - Document the new smoke/full answer benchmark entrypoint and example manual
    commands once the implementation stabilizes.

### No Changes Expected

- `eval/run_eval.py`
  - Regression runner stays deterministic and separate from `TASK-059`.
- `backend/app/benchmark/ask_retrieval_benchmark.py`
  - Retrieval-only benchmark remains unchanged.
- `backend/app/benchmark/ask_retrieval_metrics.py`
  - Retrieval metrics are unrelated to answer benchmark scoring.
- `eval/benchmark/ask_benchmark_cases.json`
  - Use the committed `50`-case dataset as-is.

### Skills To Use During Execution

- `@using-git-worktrees` before Task 1 because planning was done on a dirty
  `main` worktree and implementation should be isolated.
- `@test-driven-development` before each production edit.
- `@verification-before-completion` before every commit or “done” claim.
- `@requesting-code-review` after implementation and verification stabilize.

## Implementation Tasks

### Task 1: Add benchmark contracts, fixed smoke subset, and prompt-version plumbing

**Files:**
- Create: `backend/app/benchmark/ask_answer_benchmark_variants.py`
- Create: `backend/tests/test_ask_answer_benchmark.py`
- Create: `eval/benchmark/ask_answer_benchmark_smoke_cases.json`
- Modify: `backend/app/context/render.py`

- [ ] **Step 1: Write the failing contract tests**

Add focused tests that lock the benchmark-owned subset and variant matrix
instead of burying those assumptions in the runner tests.

Use concrete checks like:

```python
import unittest

from app.benchmark.ask_answer_benchmark_variants import (
    ANSWER_BENCHMARK_VARIANTS,
    load_answer_benchmark_smoke_case_ids,
    resolve_answer_benchmark_prompt_version,
)


class AskAnswerBenchmarkContractTests(unittest.TestCase):
    def test_load_smoke_case_ids_returns_fixed_unique_ten_case_subset(self) -> None:
        case_ids = load_answer_benchmark_smoke_case_ids()
        self.assertEqual(len(case_ids), 10)
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_variant_matrix_matches_task_059_ablation_contract(self) -> None:
        self.assertEqual(
            [
                (
                    variant.variant_id,
                    variant.context_assembly_enabled,
                    variant.runtime_faithfulness_gate_enabled,
                )
                for variant in ANSWER_BENCHMARK_VARIANTS
            ],
            [
                ("hybrid", False, False),
                ("hybrid_assembly", True, False),
                ("hybrid_assembly_gate", True, True),
            ],
        )

    def test_prompt_version_is_non_empty_and_stable(self) -> None:
        prompt_version = resolve_answer_benchmark_prompt_version()
        self.assertIsInstance(prompt_version, str)
        self.assertTrue(prompt_version)
```

- [ ] **Step 2: Run the contract tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark -v
```

Expected: FAIL because the benchmark contract helpers and fixed smoke subset do
not exist yet.

- [ ] **Step 3: Implement the variant helper module and prompt-version constants**

Create `backend/app/benchmark/ask_answer_benchmark_variants.py` with:

- one immutable `AskAnswerBenchmarkVariant` dataclass
- a fixed `ANSWER_BENCHMARK_VARIANTS` tuple
- `load_answer_benchmark_smoke_case_ids(...)`
- `build_answer_benchmark_metadata(...)` for ask requests
- `resolve_answer_benchmark_prompt_version()`

Also add explicit prompt-version constants in `backend/app/context/render.py`,
for example:

```python
ASK_TOOL_SELECTION_PROMPT_VERSION = "2026-04-22-tool-v1"
ASK_GROUNDED_ANSWER_PROMPT_VERSION = "2026-04-22-grounded-v1"
```

Then make `resolve_answer_benchmark_prompt_version()` compose them into one
string that can be written into benchmark artifacts.

Commit a fixed smoke subset file in
`eval/benchmark/ask_answer_benchmark_smoke_cases.json`. Keep it simple and
machine-readable:

```json
{
  "version": 1,
  "case_ids": [
    "ask_case_001",
    "ask_case_004"
  ]
}
```

The final implementation must validate:

- exactly `10` ids
- no duplicates
- no empty strings

- [ ] **Step 4: Re-run the contract tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark -v
```

Expected: PASS with the smoke subset and variant matrix locked in.

- [ ] **Step 5: Commit the benchmark contract slice**

```bash
git add backend/app/benchmark/ask_answer_benchmark_variants.py \
  backend/app/context/render.py \
  backend/tests/test_ask_answer_benchmark.py \
  eval/benchmark/ask_answer_benchmark_smoke_cases.json
git commit -m "feat: add TASK-059 benchmark contract helpers"
```

### Task 2: Thread benchmark variant config through the real ask workflow

**Files:**
- Modify: `backend/app/services/ask.py`
- Modify: `backend/app/graphs/ask_graph.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write failing ask-workflow tests for assembly and gate toggles**

Extend `backend/tests/test_ask_workflow.py` with two focused tests:

1. disabling runtime gate should keep a generated answer even when the computed
   `RuntimeFaithfulnessSignal` would normally downgrade it
2. disabling context assembly should bypass `build_ask_context_bundle(...)` and
   preserve raw retrieval candidates as prompt-visible evidence

Use tight mock-based tests like:

```python
def test_generate_ask_result_keeps_generated_answer_when_benchmark_disables_runtime_gate(self) -> None:
    with patch(
        "app.services.ask.build_runtime_ask_faithfulness_signal",
        return_value=RuntimeFaithfulnessSignal(
            outcome=RuntimeFaithfulnessOutcome.DOWNGRADE_TO_RETRIEVAL_ONLY,
            score=0.1,
            threshold=0.67,
            backend="lexical_semantic",
            reason="forced_test_signal",
            claim_count=1,
            unsupported_claim_count=1,
        ),
    ):
        result = self._invoke_ask_result(
            WorkflowInvokeRequest(
                action_type=WorkflowAction.ASK_QA,
                user_query="Roadmap",
                provider_preference="cloud",
                metadata={
                    "answer_benchmark_variant": {
                        "variant_id": "hybrid_assembly",
                        "context_assembly_enabled": True,
                        "runtime_faithfulness_gate_enabled": False,
                    }
                },
            ),
            settings=settings,
        )
    self.assertEqual(result.mode, AskResultMode.GENERATED_ANSWER)
    self.assertIsNotNone(result.runtime_faithfulness)
```

For the assembly toggle test, patch `build_ask_context_bundle` and assert it is
not called when `context_assembly_enabled=False`.

- [ ] **Step 2: Run the ask workflow tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_workflow -v
```

Expected: FAIL because benchmark metadata is not interpreted yet.

- [ ] **Step 3: Implement benchmark metadata handling in `ask.py` and `ask_graph.py`**

Add one small benchmark-runtime config helper inside `ask.py`, for example:

```python
@dataclass(frozen=True)
class AskBenchmarkRuntimeConfig:
    context_assembly_enabled: bool = True
    runtime_faithfulness_gate_enabled: bool = True


def _resolve_ask_benchmark_runtime_config(metadata: dict[str, object]) -> AskBenchmarkRuntimeConfig:
    ...
```

Then use it in two places:

1. `build_initial_ask_turn(...)`
   - when assembly is enabled, preserve the current `build_ask_context_bundle(...)`
     path
   - when assembly is disabled, build a raw prompt-visible bundle directly from
     retrieval candidates instead of calling the assembly pipeline

2. `generate_ask_result(...)`
   - always compute `runtime_faithfulness` and attach it to the result
   - only apply `evaluate_runtime_ask_faithfulness(...)` when the benchmark
     config says the gate is enabled

Finally, modify `backend/app/graphs/ask_graph.py` so `_finalize_ask_node(...)`
passes `state["request_metadata"]` into `generate_ask_result(...)`.

Do **not** change normal ask behavior when benchmark metadata is absent.

- [ ] **Step 4: Re-run the ask workflow tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_workflow -v
```

Expected: PASS with benchmark-only assembly/gate toggles covered.

- [ ] **Step 5: Commit the ask-runtime variant hook slice**

```bash
git add backend/app/services/ask.py \
  backend/app/graphs/ask_graph.py \
  backend/tests/test_ask_workflow.py
git commit -m "feat: add TASK-059 ask benchmark runtime toggles"
```

### Task 3: Implement deterministic scoring and aggregate math

**Files:**
- Create: `backend/app/benchmark/ask_answer_benchmark_scoring.py`
- Create: `backend/tests/test_ask_answer_benchmark_scoring.py`

- [ ] **Step 1: Write the failing scoring tests**

Add focused unit tests that lock the rule-scoring contract before the runner
exists.

Cover at least:

- generated answer with all expected facts and no forbidden claims -> `correct`
- generated answer with partial fact coverage -> `partial`
- generated answer with forbidden claims -> `incorrect` and
  `unsupported_claim=True`
- retrieval-only result on a case that allows retrieval-only -> compliant
  fallback instead of blanket failure
- aggregate calculations for:
  - `answer_correctness`
  - `unsupported_claim_rate`
  - `generated_answer_rate`
  - `retrieval_only_rate`
  - `p50_latency_ms`
  - `p95_latency_ms`

Use concrete shapes like:

```python
def test_score_case_marks_forbidden_claim_as_unsupported(self) -> None:
    score = score_answer_benchmark_case(
        case=benchmark_case,
        ask_result=ask_result,
        latency_ms=420,
    )
    self.assertEqual(score.verdict, "incorrect")
    self.assertTrue(score.unsupported_claim)
    self.assertEqual(score.matched_expected_facts, ["Alpha 已完成"])
```

- [ ] **Step 2: Run the scoring tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_scoring -v
```

Expected: FAIL because the scoring module does not exist yet.

- [ ] **Step 3: Implement the scorer and aggregate helpers**

Create `backend/app/benchmark/ask_answer_benchmark_scoring.py` with two layers:

1. case scoring
2. variant aggregation

Use explicit shapes, for example:

```python
@dataclass(frozen=True)
class AskAnswerBenchmarkCaseScore:
    case_id: str
    variant_id: str
    verdict: str
    correctness_points: float
    unsupported_claim: bool
    matched_expected_facts: list[str]
    missed_expected_facts: list[str]
    forbidden_claim_hits: list[str]
    latency_ms: int
```

Implement deterministic rules that use the dataset contract, not a judge model:

- `expected_facts` drive fact-hit coverage
- `forbidden_claims` drive unsupported-claim detection
- `should_generate_answer` and `allow_retrieval_only` determine whether a
  `retrieval_only` / `no_hits` outcome is compliant or a miss
- `answer_correctness` should be an explicit numeric aggregate derived from
  verdict scores, for example `correct=1.0`, `partial=0.5`, `incorrect=0.0`

Also add aggregate helpers for the tool subset used in full mode:

- `tool_trigger_rate`
- `expected_tool_hit_rate`
- `tool_case_answer_correctness`

- [ ] **Step 4: Re-run the scoring tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_scoring -v
```

Expected: PASS with deterministic scoring locked in.

- [ ] **Step 5: Commit the scoring slice**

```bash
git add backend/app/benchmark/ask_answer_benchmark_scoring.py \
  backend/tests/test_ask_answer_benchmark_scoring.py
git commit -m "feat: add TASK-059 deterministic answer scoring"
```

### Task 4: Build the answer benchmark orchestration and artifact writer

**Files:**
- Modify: `backend/tests/test_ask_answer_benchmark.py`
- Create: `backend/app/benchmark/ask_answer_benchmark.py`

- [ ] **Step 1: Extend the benchmark tests with orchestration expectations**

Add failing tests in `backend/tests/test_ask_answer_benchmark.py` that cover:

- smoke mode selects the fixed `10` cases
- full mode selects all `50` dataset cases
- every selected case expands across all three variants
- runner pins the invoke request to `provider_preference="cloud"`
- artifact metadata records `provider_name`, `model_name`, `prompt_version`,
  `git_commit`, `benchmark_mode`, `selected_case_ids`
- full mode includes tool-subset aggregates while smoke mode does not

Use a patch-based test around `invoke_ask_graph(...)`, for example:

```python
with patch("app.benchmark.ask_answer_benchmark.invoke_ask_graph") as mocked_invoke:
    mocked_invoke.return_value = fake_execution
    result = run_ask_answer_benchmark(
        settings=settings,
        mode="smoke",
        dataset_path=dataset_path,
    )

self.assertEqual(result["benchmark_mode"], "smoke")
self.assertEqual(len(result["selected_case_ids"]), 10)
self.assertEqual(mocked_invoke.call_count, 30)
first_request = mocked_invoke.call_args_list[0].args[0]
self.assertEqual(first_request.provider_preference, "cloud")
```

- [ ] **Step 2: Run the benchmark tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark -v
```

Expected: FAIL because the orchestration layer does not exist yet.

- [ ] **Step 3: Implement `ask_answer_benchmark.py`**

Create `backend/app/benchmark/ask_answer_benchmark.py` with:

- mode selection (`smoke` / `full`)
- dataset loading
- smoke subset loading
- synthetic ask invocation loop via `invoke_ask_graph(...)`
- latency timing
- benchmark metadata assembly
- result writing helpers

Keep the execution path real by building one `WorkflowInvokeRequest` per
`case x variant`, for example:

```python
request = WorkflowInvokeRequest(
    action_type=WorkflowAction.ASK_QA,
    user_query=case.user_query,
    provider_preference="cloud",
    metadata=build_answer_benchmark_metadata(variant),
)
execution = invoke_ask_graph(
    request,
    settings=benchmark_settings,
    thread_id=f"task059_{case.case_id}_{variant.variant_id}",
    run_id=f"task059_{case.case_id}_{variant.variant_id}_{uuid4().hex}",
)
```

Use `replace(settings, cloud_chat_model="qwen-max", local_chat_model="")` or an
equivalent helper so the benchmark stays pinned to canonical cloud model
`qwen-max`.

The result artifact should be a dedicated answer-benchmark JSON under
`eval/results/`, for example:

```python
answer-benchmark-YYYYMMDD-HHMMSS.json
```

Do **not** write through `eval/run_eval.py`.

- [ ] **Step 4: Re-run the benchmark tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark -v
```

Expected: PASS with smoke/full orchestration and artifact schema covered.

- [ ] **Step 5: Commit the orchestration slice**

```bash
git add backend/app/benchmark/ask_answer_benchmark.py \
  backend/tests/test_ask_answer_benchmark.py
git commit -m "feat: add TASK-059 answer benchmark runner"
```

### Task 5: Add preflight, CLI surface, operator docs, and manual verification commands

**Files:**
- Create: `backend/app/benchmark/ask_answer_benchmark_preflight.py`
- Create: `backend/tests/test_ask_answer_benchmark_preflight.py`
- Create: `backend/tests/test_ask_answer_benchmark_cli.py`
- Create: `eval/benchmark/run_answer_benchmark.py`
- Modify: `eval/README.md`

- [ ] **Step 1: Write failing preflight and CLI tests**

Add tests for:

- missing cloud provider config -> preflight failure
- cloud model not equal to `qwen-max` -> preflight failure
- missing smoke subset file in smoke mode -> preflight failure
- CLI returns non-zero and skips benchmark execution when preflight fails
- CLI forwards `--mode`, `--output`, and `--dataset`

Use concrete shapes like:

```python
preflight = run_answer_benchmark_preflight(
    settings=settings,
    mode="smoke",
    dataset_path=dataset_path,
    smoke_subset_path=smoke_subset_path,
)
self.assertEqual(preflight.status, "canonical_model_mismatch")
```

and:

```python
exit_code = module.main(["--mode", "smoke", "--output", str(output_path)])
self.assertEqual(exit_code, 1)
mocked_run_benchmark.assert_not_called()
```

- [ ] **Step 2: Run the preflight and CLI tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_preflight \
  backend.tests.test_ask_answer_benchmark_cli -v
```

Expected: FAIL because the preflight module and CLI do not exist yet.

- [ ] **Step 3: Implement the preflight module, CLI, and README entry**

Create `backend/app/benchmark/ask_answer_benchmark_preflight.py` with a small
structured result type and checks for:

- cloud provider base URL presence
- cloud chat model presence
- cloud chat model exactly equal to `qwen-max`
- dataset readability
- smoke subset readability when `mode="smoke"`

Then add `eval/benchmark/run_answer_benchmark.py` modeled after the retrieval
benchmark CLI:

```python
parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
parser.add_argument("--output", type=Path)
parser.add_argument("--dataset", type=Path)
```

and:

```python
preflight = run_answer_benchmark_preflight(...)
if preflight.status != "ok":
    print(f"ERROR: {preflight.message}", file=sys.stderr)
    return 1
```

Finally, update `eval/README.md` with the new operator commands:

```bash
set -a; source backend/.env; set +a
./.conda/knowledge-steward/bin/python eval/benchmark/run_answer_benchmark.py --mode smoke --output /tmp/task-059-smoke.json
./.conda/knowledge-steward/bin/python eval/benchmark/run_answer_benchmark.py --mode full --output /tmp/task-059-full.json
```

- [ ] **Step 4: Re-run the preflight and CLI tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark_preflight \
  backend.tests.test_ask_answer_benchmark_cli -v
```

Expected: PASS with CLI/preflight coverage locked in.

- [ ] **Step 5: Run the full benchmark test suite for `TASK-059`**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
PYTHONPATH=backend ./.conda/knowledge-steward/bin/python -m unittest \
  backend.tests.test_ask_answer_benchmark \
  backend.tests.test_ask_answer_benchmark_scoring \
  backend.tests.test_ask_answer_benchmark_preflight \
  backend.tests.test_ask_answer_benchmark_cli \
  backend.tests.test_ask_workflow -v
```

Expected: PASS. If any failure remains, fix it before moving on.

- [ ] **Step 6: Run the real-provider smoke command manually**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
set -a; source backend/.env; set +a
./.conda/knowledge-steward/bin/python eval/benchmark/run_answer_benchmark.py \
  --mode smoke \
  --output /tmp/task-059-answer-benchmark-smoke.json
```

Expected:

- exit code `0`
- a complete smoke artifact with `benchmark_mode="smoke"`
- all three variants present
- plausible values for `answer_correctness`,
  `unsupported_claim_rate`, and `generated_answer_rate`

If the numbers look normal, record that full mode is now safe to run manually.

- [ ] **Step 7: Commit the CLI and verification slice**

```bash
git add backend/app/benchmark/ask_answer_benchmark_preflight.py \
  backend/tests/test_ask_answer_benchmark_preflight.py \
  backend/tests/test_ask_answer_benchmark_cli.py \
  eval/benchmark/run_answer_benchmark.py \
  eval/README.md
git commit -m "feat: add TASK-059 answer benchmark CLI"
```

## Final Verification Checklist

- [ ] The fixed smoke subset is committed and validated as exactly `10` unique
  ids.
- [ ] The benchmark executes the real ask graph, not a duplicate ask pipeline.
- [ ] Benchmark metadata can disable assembly and gate behavior per variant
  without changing default ask runtime behavior.
- [ ] `runtime_faithfulness` is still recorded even when the gate is disabled.
- [ ] Deterministic scoring uses dataset expectations rather than an LLM judge.
- [ ] Smoke/full artifacts record canonical cloud model `qwen-max`.
- [ ] CLI preflight fails before execution on bad config or unreadable inputs.
- [ ] Smoke mode runs successfully before any full manual run is attempted.
