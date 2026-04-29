# TASK-057 Ask Benchmark Dataset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone ask benchmark dataset workflow that can generate `5` review candidates at a time, route `approve / revise / reject` outcomes into the correct files, and validate heading-based evidence locators for a formal `50`-case dataset.

**Architecture:** Keep the formal benchmark assets under `eval/benchmark/`, but put the implementation logic in a small backend `benchmark` package so it can reuse the existing markdown parser and test harness cleanly. Split the work into four concerns: schema-backed dataset storage, locator/distribution validation, candidate generation from `sample_vault`, and a thin operator CLI that generates batches, applies review decisions, and validates the formal dataset after each write.

**Tech Stack:** Python 3.12, Pydantic, existing markdown parsing in `backend/app/indexing/parser.py`, JSON dataset assets, `unittest`.

---

## Scope Check

Keep this as one implementation plan. Formal dataset storage, locator validation,
candidate generation, and review routing are not independent subsystems here;
they all enforce one dataset contract from the approved `TASK-057` spec. Split
execution into separate commits, but do not split this into multiple plans.

## File Structure

### Create

- `backend/app/benchmark/__init__.py`
  - Export the small benchmark helpers used by tests and the operator CLI.
- `backend/app/benchmark/ask_dataset.py`
  - Pydantic models plus load/save helpers for the formal cases file and review backlog.
- `backend/app/benchmark/ask_dataset_validation.py`
  - Validate schema-level rules, heading-based locators, excerpt drift, and progressive/final distribution rules.
- `backend/app/benchmark/ask_dataset_candidates.py`
  - Generate conservative candidate cases from `sample_vault` and skip fingerprints already present in the formal dataset or backlog.
- `backend/app/benchmark/ask_dataset_review.py`
  - Apply `approve / revise / reject` decisions and route cases into the formal dataset or backlog, then re-run validation.
- `backend/tests/test_ask_benchmark_dataset.py`
  - Contract tests for model enums, JSON layout, load/save behavior, and approved/backlog record shapes.
- `backend/tests/test_ask_benchmark_validation.py`
  - Focused tests for `note_path + heading_path`, `line_range`, `excerpt_anchor`, and bucket/sample-vault distribution rules.
- `backend/tests/test_ask_benchmark_candidates.py`
  - Focused tests for batch size, de-duplication, conservative query generation, and `sample_vault`-first behavior.
- `backend/tests/test_ask_benchmark_review.py`
  - Tests for approval routing, backlog routing, and post-write validation.
- `eval/benchmark/manage_ask_benchmark.py`
  - Thin operator entrypoint with subcommands for `generate-batch`, `apply-review`, and `validate`.
- `eval/benchmark/ask_benchmark_cases.json`
  - Formal approved dataset.
- `eval/benchmark/ask_benchmark_review_backlog.json`
  - Rejected/revise candidates and reasons.
- `eval/benchmark/ask_benchmark_spec.md`
  - Operator-facing contract summary derived from the approved design doc, not a second project-governance source.

### Modify

- `eval/README.md`
  - Add a short section that points to the new benchmark dataset assets and exact operator commands.

### No Changes Expected

- `eval/run_eval.py`
  - `TASK-057` should not wire the new dataset into the existing regression runner yet.
- `eval/golden/*.json`
  - Existing regression cases stay untouched.
- `backend/app/indexing/parser.py`
  - Reuse the current heading/chunk parser instead of changing markdown parsing semantics.
- `docs/TASK_QUEUE.md`
- `docs/CURRENT_STATE.md`
- `docs/SESSION_LOG.md`
  - Governance docs should wait for governed-session closeout, not be edited during implementation.

### Skills To Use During Execution

- `@using-git-worktrees` before Task 1 so implementation happens outside the dirty main worktree.
- `@test-driven-development` before every production edit.
- `@verification-before-completion` before any “done” claim or commit.
- `@requesting-code-review` after implementation and verification stabilize.

## Implementation Tasks

### Task 1: Seed the formal benchmark assets and schema-backed storage

**Files:**
- Create: `backend/app/benchmark/__init__.py`
- Create: `backend/app/benchmark/ask_dataset.py`
- Create: `backend/tests/test_ask_benchmark_dataset.py`
- Create: `eval/benchmark/ask_benchmark_cases.json`
- Create: `eval/benchmark/ask_benchmark_review_backlog.json`
- Create: `eval/benchmark/ask_benchmark_spec.md`

- [ ] **Step 1: Write the failing dataset contract tests**

Add tests that lock:

- allowed `bucket` values are exactly `single_hop`, `multi_hop`, `metadata_filter`, `abstain_or_no_hit`, `tool_allowed`
- approved dataset cases always carry `review_status="approved"`
- locator objects require `note_path`, `heading_path`, and `excerpt_anchor`
- the seeded formal dataset file uses one top-level JSON shape
- the seeded backlog file uses one top-level JSON shape

Use a concrete shape like:

```python
from pathlib import Path
import tempfile
import unittest

from app.benchmark.ask_dataset import (
    AskBenchmarkCase,
    AskBenchmarkDataset,
    AskBenchmarkLocator,
    AskBenchmarkReviewBacklog,
    load_ask_benchmark_dataset,
)


class AskBenchmarkDatasetTests(unittest.TestCase):
    def test_case_rejects_unknown_bucket(self) -> None:
        with self.assertRaisesRegex(ValueError, "bucket"):
            AskBenchmarkCase(
                case_id="ask_case_001",
                bucket="bad_bucket",
                user_query="总结这篇笔记",
                source_origin="sample_vault",
                expected_relevant_paths=["日常/2024-03-14_星期四.md"],
                expected_relevant_locators=[
                    AskBenchmarkLocator(
                        note_path="日常/2024-03-14_星期四.md",
                        heading_path="一、工作任务",
                        excerpt_anchor="完成 digest graph",
                    )
                ],
                expected_facts=["今天接通了 DAILY_DIGEST。"],
                forbidden_claims=[],
                allow_tool=False,
                expected_tool_names=[],
                allow_retrieval_only=False,
                should_generate_answer=True,
                review_status="approved",
                review_notes="seed",
            )
```

- [ ] **Step 2: Run the dataset tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_dataset -v
```

Expected: FAIL because the benchmark dataset models, loaders, and seeded files do not exist yet.

- [ ] **Step 3: Implement the minimal dataset store and seed assets**

Create `backend/app/benchmark/ask_dataset.py` with:

- one constant for the benchmark directory under `ROOT_DIR / "eval" / "benchmark"`
- `AskBenchmarkLocator`
- `AskBenchmarkCase`
- `AskBenchmarkDataset`
- `AskBenchmarkBacklogItem`
- `AskBenchmarkReviewBacklog`
- `load_ask_benchmark_dataset()`
- `write_ask_benchmark_dataset()`
- `load_ask_benchmark_backlog()`
- `write_ask_benchmark_backlog()`

Keep the seeded JSON files minimal:

```json
{
  "schema_version": 1,
  "cases": []
}
```

```json
{
  "schema_version": 1,
  "items": []
}
```

`eval/benchmark/ask_benchmark_spec.md` should be a concise operator-facing
contract summary derived from the approved design doc. It should document the
field shapes and commands, but it should not repeat the entire project-governance
history from `docs/superpowers/specs/...`.

- [ ] **Step 4: Re-run the dataset tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_dataset -v
```

Expected: PASS with model validation and seeded-file load/save behavior locked.

- [ ] **Step 5: Commit the schema/storage slice**

```bash
git add backend/app/benchmark/__init__.py \
  backend/app/benchmark/ask_dataset.py \
  backend/tests/test_ask_benchmark_dataset.py \
  eval/benchmark/ask_benchmark_cases.json \
  eval/benchmark/ask_benchmark_review_backlog.json \
  eval/benchmark/ask_benchmark_spec.md
git commit -m "feat: add ask benchmark dataset store"
```

### Task 2: Add locator, drift, and progressive distribution validation

**Files:**
- Create: `backend/app/benchmark/ask_dataset_validation.py`
- Create: `backend/tests/test_ask_benchmark_validation.py`

- [ ] **Step 1: Write the failing validation tests**

Lock the behaviors that can silently corrupt the dataset:

- `note_path + heading_path` resolves through `parse_markdown_note()`
- `line_range` must stay inside the matched heading scope when present
- `excerpt_anchor` mismatch becomes drift
- missing note path is a hard failure
- missing heading path is a locator failure
- in-progress datasets may be smaller than `50`, but they must never exceed the final bucket caps
- in-progress datasets may use fewer than `40` `sample_vault` cases, but fixture count must never exceed `10`
- once case count reaches `50`, exact bucket counts and `sample_vault >= 40` become hard requirements

Use small temporary notes for locator tests so failures are deterministic:

```python
def test_validate_locator_rejects_excerpt_drift(self) -> None:
    note_path.write_text(
        "# Summary\n\n## Highlights\n\nShip the benchmark.\n",
        encoding="utf-8",
    )
    case = self._make_case(
        expected_relevant_locators=[
            AskBenchmarkLocator(
                note_path="Summary.md",
                heading_path="Summary > Highlights",
                line_range={"start_line": 3, "end_line": 4},
                excerpt_anchor="Old content no longer present",
            )
        ]
    )

    result = validate_ask_benchmark_case(case=case, vault_root=vault_root)
    self.assertIn("excerpt_anchor", result.errors[0])
```

- [ ] **Step 2: Run the validation tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_validation -v
```

Expected: FAIL because no validation helpers exist yet.

- [ ] **Step 3: Implement the minimal validator**

Build focused helpers in `backend/app/benchmark/ask_dataset_validation.py`:

- `validate_ask_benchmark_case(case, vault_root)`
- `validate_ask_benchmark_dataset(dataset, vault_root)`
- `resolve_heading_locator(note_path, heading_path, vault_root)`
- `check_line_range_within_heading(...)`
- `check_excerpt_anchor(...)`

Implementation rules:

- reuse `parse_markdown_note()` instead of adding a second markdown parser
- treat `heading_path` as the primary locator
- treat `line_range` as optional disambiguation, not the primary key
- emit explicit error messages; do not auto-rewrite locators
- apply progressive distribution rules while the formal dataset is still growing

- [ ] **Step 4: Re-run the validation tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_validation -v
```

Expected: PASS with hard failures for missing note/heading drift and clear behavior for in-progress versus final distribution checks.

- [ ] **Step 5: Commit the validation slice**

```bash
git add backend/app/benchmark/ask_dataset_validation.py \
  backend/tests/test_ask_benchmark_validation.py
git commit -m "feat: validate ask benchmark locators"
```

### Task 3: Add `sample_vault`-first candidate generation for `5`-case review batches

**Files:**
- Create: `backend/app/benchmark/ask_dataset_candidates.py`
- Create: `backend/tests/test_ask_benchmark_candidates.py`

- [ ] **Step 1: Write the failing candidate-generation tests**

Cover the minimum behaviors needed for the human review loop:

- `build_candidate_batch(..., count=5)` returns exactly `5` candidates when enough unused source material exists
- candidates default to `source_origin="sample_vault"`
- generated locators use `note_path + heading_path`
- generated batches skip fingerprints already present in the approved dataset or backlog
- generated queries stay conservative: heading/task/date/fact rewrites before freer paraphrase

Use a test fixture with a few notes and an existing approved case to lock de-duplication:

```python
def test_build_candidate_batch_skips_existing_case_fingerprints(self) -> None:
    approved = AskBenchmarkDataset(
        schema_version=1,
        cases=[
            self._make_case(
                case_id="ask_case_001",
                user_query="这篇日记做了什么？",
                expected_relevant_locators=[
                    AskBenchmarkLocator(
                        note_path="日常/2024-03-14_星期四.md",
                        heading_path="一、工作任务",
                        excerpt_anchor="完成 digest graph",
                    )
                ],
            )
        ],
    )

    batch = build_candidate_batch(
        vault_root=vault_root,
        approved_dataset=approved,
        backlog=self._empty_backlog(),
        count=5,
    )

    self.assertEqual(len(batch), 5)
    self.assertNotIn("这篇日记做了什么？", {item.user_query for item in batch})
```

- [ ] **Step 2: Run the candidate-generation tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_candidates -v
```

Expected: FAIL because no candidate generator exists yet.

- [ ] **Step 3: Implement the minimal generator**

Create a focused generator that:

- crawls `sample_vault`
- parses notes with `parse_markdown_note()`
- proposes one or more candidate prompts from:
  - heading titles
  - task lists
  - dates
  - explicit summary facts
- attaches:
  - a suggested primary `bucket`
  - `expected_relevant_paths` derived from the selected note(s)
  - suggested locators
  - seed `expected_facts` from the matched chunk text
  - conservative default `forbidden_claims`
  - ideal-behavior defaults for `allow_tool`, `allow_retrieval_only`, and `should_generate_answer`
- de-duplicates by a stable fingerprint derived from note path, heading path, and query text

Keep this heuristic and local. Do not call the LLM to generate benchmark cases.

- [ ] **Step 4: Re-run the candidate-generation tests and make them pass**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_candidates -v
```

Expected: PASS with `5`-item batches, sample-vault-first sourcing, and de-duplication against both approved and backlog records.

- [ ] **Step 5: Commit the candidate-generation slice**

```bash
git add backend/app/benchmark/ask_dataset_candidates.py \
  backend/tests/test_ask_benchmark_candidates.py
git commit -m "feat: generate ask benchmark review batches"
```

### Task 4: Add review routing and the thin operator CLI

**Files:**
- Create: `backend/app/benchmark/ask_dataset_review.py`
- Create: `backend/tests/test_ask_benchmark_review.py`
- Create: `eval/benchmark/manage_ask_benchmark.py`
- Modify: `eval/README.md`

- [ ] **Step 1: Write the failing review-routing tests**

Add tests that lock the review loop contract:

- approved cases append to `ask_benchmark_cases.json` only
- `revise` and `reject` decisions append to `ask_benchmark_review_backlog.json` only
- approved writes re-run dataset validation before committing changes
- duplicate `case_id` or duplicate fingerprints are rejected during apply-review

Use explicit review payloads like:

```python
review_input = [
    {"case_id": "ask_case_010", "decision": "approve", "review_notes": "keep"},
    {"case_id": "ask_case_011", "decision": "revise", "review_notes": "bucket wrong"},
]
```

- [ ] **Step 2: Run the review-routing tests and confirm they fail**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_review -v
```

Expected: FAIL because there is no apply-review workflow yet.

- [ ] **Step 3: Implement review routing and the CLI**

In `backend/app/benchmark/ask_dataset_review.py`, add one focused entry point:

```python
def apply_review_outcomes(
    *,
    candidate_batch: list[AskBenchmarkCase],
    review_decisions: list[ReviewDecision],
    dataset_path: Path,
    backlog_path: Path,
    vault_root: Path,
) -> ReviewApplyResult: ...
```

Rules:

- `approve` -> normalize `review_status="approved"` and append to the formal dataset
- `revise` / `reject` -> append to backlog with short reason and original candidate payload
- no partial writes if validation fails after an `approve`
- keep approved data and backlog data physically separate

Add `eval/benchmark/manage_ask_benchmark.py` with subcommands:

- `generate-batch --count 5 --output <path> [--dataset <path>] [--backlog <path>] [--vault-root <path>]`
- `apply-review --batch <path> --review <path> [--dataset <path>] [--backlog <path>] [--vault-root <path>]`
- `validate [--dataset <path>] [--backlog <path>] [--vault-root <path>]`

Path overrides are required so focused end-to-end verification can use temporary
copies instead of mutating the real formal dataset during smoke tests.

Update `eval/README.md` with exact commands and a short explanation that:

- `eval/golden/` remains the regression layer
- `eval/benchmark/` is the new benchmark dataset layer

- [ ] **Step 4: Re-run the review-routing tests and smoke the CLI**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_benchmark_review -v
```

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
./.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py validate
```

Expected: tests PASS and the CLI reports that the freshly seeded dataset/backlog are valid.

- [ ] **Step 5: Commit the review-loop slice**

```bash
git add backend/app/benchmark/ask_dataset_review.py \
  backend/tests/test_ask_benchmark_review.py \
  eval/benchmark/manage_ask_benchmark.py \
  eval/README.md
git commit -m "feat: add ask benchmark review workflow"
```

### Task 5: Run focused end-to-end verification for the whole `TASK-057` slice

**Files:**
- No new files

- [ ] **Step 1: Run all new benchmark-focused tests**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward/backend
../.conda/knowledge-steward/bin/python -m unittest \
  tests.test_ask_benchmark_dataset \
  tests.test_ask_benchmark_validation \
  tests.test_ask_benchmark_candidates \
  tests.test_ask_benchmark_review \
  -v
```

Expected: PASS across schema, validation, candidate generation, and review routing.

- [ ] **Step 2: Generate one real review batch from `sample_vault`**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
./.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py \
  generate-batch \
  --count 5 \
  --output /tmp/task-057-batch.json
```

Expected: a JSON batch with `5` conservative candidate cases, all using heading-based locators and no duplicates against the seeded formal/backlog assets.

- [ ] **Step 3: Smoke `apply-review` against temporary dataset copies**

Create a temporary review file with one `reject` decision so the smoke test can
exercise routing without changing the real formal dataset:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
cp eval/benchmark/ask_benchmark_cases.json /tmp/task-057-cases.json
cp eval/benchmark/ask_benchmark_review_backlog.json /tmp/task-057-backlog.json
cat >/tmp/task-057-review.json <<'EOF'
[
  {
    "case_id": "ask_case_smoke_001",
    "decision": "reject",
    "review_notes": "cli smoke test"
  }
]
EOF
./.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py \
  apply-review \
  --batch /tmp/task-057-batch.json \
  --review /tmp/task-057-review.json \
  --dataset /tmp/task-057-cases.json \
  --backlog /tmp/task-057-backlog.json
```

Expected: PASS with the rejected candidate routed into the temporary backlog copy and the temporary formal dataset left unchanged.

- [ ] **Step 4: Re-run formal validation after generation and review smoke**

Run:

```bash
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward
./.conda/knowledge-steward/bin/python eval/benchmark/manage_ask_benchmark.py validate
```

Expected: PASS because generation should not mutate the formal dataset or backlog.

- [ ] **Step 4: Request code review before claiming completion**

Use `@requesting-code-review` once the implementation and focused verification have stabilized.
