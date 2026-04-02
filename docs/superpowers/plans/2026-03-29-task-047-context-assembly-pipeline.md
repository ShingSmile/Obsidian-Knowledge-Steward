# TASK-047 Context Assembly Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the ask path's current "dedupe + uniform trim" context assembly with a four-stage quality-control pipeline that filters low-value candidates, limits per-note dominance, enriches evidence with source structure, and applies weighted budget allocation without changing the outer ask contract.

**Architecture:** Keep retrieval unchanged and concentrate the new behavior in the existing assembly boundary. Extend `ContextBundle` with structured assembly metadata and source-note summaries, add focused unit coverage around ask assembly, then update ask rendering/integration so prompt-visible evidence and citations reflect the post-assembly result instead of raw retrieval order.

**Tech Stack:** Python 3.12, Pydantic, SQLite-backed retrieval fixtures, FastAPI ask workflow wrappers, `unittest`, offline golden eval runner.

---

## File Structure

Keep `TASK-047` inside the backend ask boundary. Do not move filtering into retrieval and do not widen the graph/API surface.

### Create

- `backend/tests/test_context_assembly.py`
  - Focused unit coverage for relevance filtering, diversity capping, structured evidence enrichment, source note summaries, and weighted budget allocation.

### Modify

- `backend/app/contracts/workflow.py`
  - Add assembly-specific models and fields required by the richer `ContextBundle`.
- `backend/app/context/assembly.py`
  - Implement the four-stage ask assembly pipeline and preserve current safety filtering semantics.
- `backend/app/context/render.py`
  - Render enriched retrieval evidence using `source_note_title` and `position_hint`.
- `backend/app/services/ask.py`
  - Continue deriving prompt-visible candidates and citations from the final assembled retrieval evidence.
- `backend/tests/test_ask_workflow.py`
  - Add integration coverage proving ask consumes the new assembly output without changing retrieval-only / generated-answer fallback behavior.

### No Changes Expected

- `backend/app/retrieval/hybrid.py`
  - Retrieval scoring and RRF fusion stay unchanged.
- `backend/app/main.py`
  - No API or endpoint changes belong to this task.
- plugin files
  - `TASK-047` is backend-only.

### Skills To Use During Execution

- `@test-driven-development` before each production edit.
- `@verification-before-completion` before any success claim or commit.
- `@requesting-code-review` after implementation and verification stabilize.

## Implementation Tasks

### Task 1: Add focused assembly unit tests and extend the assembly contract

**Files:**
- Create: `backend/tests/test_context_assembly.py`
- Modify: `backend/app/contracts/workflow.py`
- Modify: `backend/app/context/assembly.py`

- [ ] **Step 1: Write the failing assembly contract tests**

```python
import unittest

from app.context.assembly import build_ask_context_bundle
from app.contracts.workflow import RetrievedChunkCandidate, ToolExecutionResult


class AskContextAssemblyTests(unittest.TestCase):
    def test_build_ask_context_bundle_filters_low_score_tail_candidates(self) -> None:
        bundle = build_ask_context_bundle(
            user_query="roadmap",
            candidates=[
                RetrievedChunkCandidate(
                    chunk_id="c1",
                    note_id="n1",
                    path="vault/Roadmap.md",
                    title="Roadmap",
                    heading_path="Roadmap > Delivery",
                    note_type="note",
                    template_family="default",
                    daily_note_date=None,
                    source_mtime_ns=1,
                    start_line=1,
                    end_line=5,
                    score=1.0,
                    snippet="top",
                    text="top evidence",
                ),
                RetrievedChunkCandidate(
                    chunk_id="c2",
                    note_id="n2",
                    path="vault/Noise.md",
                    title="Noise",
                    heading_path="Noise > Tail",
                    note_type="note",
                    template_family="default",
                    daily_note_date=None,
                    source_mtime_ns=1,
                    start_line=1,
                    end_line=5,
                    score=0.1,
                    snippet="tail",
                    text="tail evidence",
                ),
            ],
            tool_results=[],
            token_budget=2400,
            allowed_tool_names=[],
        )

        self.assertEqual([item.chunk_id for item in bundle.evidence_items], ["c1"])
        self.assertEqual(bundle.assembly_metadata.initial_candidate_count, 2)
        self.assertEqual(bundle.assembly_metadata.relevance_filtered_count, 1)
        self.assertEqual(bundle.assembly_metadata.final_evidence_count, 1)

    def test_build_ask_context_bundle_exposes_source_note_summary_defaults(self) -> None:
        bundle = build_ask_context_bundle(
            user_query="roadmap",
            candidates=[...],
            tool_results=[],
            token_budget=2400,
            allowed_tool_names=[],
        )

        self.assertEqual(bundle.source_notes[0].title, "Roadmap")
        self.assertEqual(bundle.source_notes[0].chunk_count, 1)
```

- [ ] **Step 2: Run the new assembly tests and confirm they fail for the expected reason**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly -v
```

Expected: FAIL because `ContextBundle` does not yet expose `assembly_metadata` / `source_notes`, and ask assembly still keeps the low-score tail candidate.

- [ ] **Step 3: Implement the minimal contract additions**

Add assembly-specific models in `backend/app/contracts/workflow.py`:

```python
class ContextSourceNote(BaseModel):
    source_path: str
    title: str
    chunk_count: int = 0
    max_score: float | None = None


class ContextAssemblyMetadata(BaseModel):
    initial_candidate_count: int = 0
    relevance_filtered_count: int = 0
    diversity_filtered_count: int = 0
    budget_filtered_count: int = 0
    suspicious_filtered_count: int = 0
    final_evidence_count: int = 0
    relevance_threshold: float = 0.0
    per_source_limit: int = 0
    full_text_char_budget: int = 0
    summary_char_budget: int = 0
```

Extend the existing structures without changing external ask result types:

```python
class ContextEvidenceItem(BaseModel):
    source_path: str
    chunk_id: str | None = None
    source_note_title: str | None = None
    heading_path: str | None = None
    position_hint: str | None = None
    text: str
    score: float | None = None
    source_kind: Literal["retrieval", "tool", "proposal", "digest"]


class ContextBundle(BaseModel):
    ...
    source_notes: list[ContextSourceNote] = Field(default_factory=list)
    assembly_metadata: ContextAssemblyMetadata = Field(
        default_factory=ContextAssemblyMetadata
    )
```

Update the non-ask bundle builders in `backend/app/context/assembly.py` to populate safe defaults so ingest/digest callers do not break.

- [ ] **Step 4: Re-run the assembly tests and make the contract expectations pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly -v
```

Expected: PASS for the initial contract-level expectations.

- [ ] **Step 5: Commit the contract groundwork**

```bash
git add backend/app/contracts/workflow.py backend/app/context/assembly.py backend/tests/test_context_assembly.py
git commit -m "feat: add ask assembly contract metadata"
```

### Task 2: Implement relevance filtering and source diversity control

**Files:**
- Modify: `backend/app/context/assembly.py`
- Modify: `backend/tests/test_context_assembly.py`

- [ ] **Step 1: Write the failing relevance/diversity tests**

```python
class AskContextAssemblyTests(unittest.TestCase):
    def test_build_ask_context_bundle_limits_each_source_to_two_chunks(self) -> None:
        bundle = build_ask_context_bundle(
            user_query="roadmap",
            candidates=[
                _candidate("c1", "vault/Roadmap.md", score=1.0),
                _candidate("c2", "vault/Roadmap.md", score=0.9),
                _candidate("c3", "vault/Roadmap.md", score=0.8),
                _candidate("c4", "vault/Strategy.md", score=0.7),
            ],
            tool_results=[],
            token_budget=2400,
            allowed_tool_names=[],
        )

        self.assertEqual(
            [item.chunk_id for item in bundle.evidence_items],
            ["c1", "c2", "c4"],
        )
        self.assertEqual(bundle.assembly_metadata.diversity_filtered_count, 1)
        self.assertEqual(bundle.assembly_metadata.per_source_limit, 2)

    def test_build_ask_context_bundle_keeps_top_candidate_when_threshold_would_drop_all(self) -> None:
        bundle = build_ask_context_bundle(
            user_query="roadmap",
            candidates=[_candidate("c1", "vault/Roadmap.md", score=0.2)],
            tool_results=[],
            token_budget=2400,
            allowed_tool_names=[],
        )

        self.assertEqual([item.chunk_id for item in bundle.evidence_items], ["c1"])
        self.assertEqual(bundle.assembly_metadata.relevance_filtered_count, 0)
```

- [ ] **Step 2: Run the targeted assembly tests and watch them fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_limits_each_source_to_two_chunks tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_keeps_top_candidate_when_threshold_would_drop_all -v
```

Expected: FAIL because the current assembly path only deduplicates by `chunk_id` and never caps per-source contribution.

- [ ] **Step 3: Implement the minimal stage-1 and stage-2 pipeline logic**

Keep the logic local to `backend/app/context/assembly.py`:

```python
ASK_RELEVANCE_RATIO = 0.35
ASK_PER_SOURCE_LIMIT = 2


def _filter_candidates_by_relevance(
    candidates: list[RetrievedChunkCandidate],
) -> tuple[list[RetrievedChunkCandidate], int, float]:
    if not candidates:
        return [], 0, 0.0
    top_score = candidates[0].score
    threshold = top_score * ASK_RELEVANCE_RATIO
    kept = [candidate for candidate in candidates if candidate.score >= threshold]
    if not kept:
        return [candidates[0]], 0, threshold
    return kept, len(candidates) - len(kept), threshold


def _limit_candidates_per_source(
    candidates: list[RetrievedChunkCandidate],
) -> tuple[list[RetrievedChunkCandidate], int]:
    kept: list[RetrievedChunkCandidate] = []
    counts_by_path: dict[str, int] = {}
    dropped = 0
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.path, item.start_line)):
        path_count = counts_by_path.get(candidate.path, 0)
        if path_count >= ASK_PER_SOURCE_LIMIT:
            dropped += 1
            continue
        counts_by_path[candidate.path] = path_count + 1
        kept.append(candidate)
    return kept, dropped
```

Do not remove the existing suspicious-text filtering; the new stages sit before prompt-visible evidence is materialized.

- [ ] **Step 4: Re-run the targeted assembly tests and make them pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_limits_each_source_to_two_chunks tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_keeps_top_candidate_when_threshold_would_drop_all -v
```

Expected: PASS, proving the first two stages behave deterministically.

- [ ] **Step 5: Commit the filtering logic**

```bash
git add backend/app/context/assembly.py backend/tests/test_context_assembly.py
git commit -m "feat: add ask relevance and diversity filtering"
```

### Task 3: Implement structured enrichment and weighted budget allocation

**Files:**
- Modify: `backend/app/context/assembly.py`
- Modify: `backend/tests/test_context_assembly.py`

- [ ] **Step 1: Write the failing enrichment/budget tests**

```python
class AskContextAssemblyTests(unittest.TestCase):
    def test_build_ask_context_bundle_adds_source_titles_and_position_hints(self) -> None:
        bundle = build_ask_context_bundle(
            user_query="roadmap",
            candidates=[
                _candidate("c1", "vault/Roadmap.md", title="Roadmap", heading="Roadmap > Ask", score=1.0),
                _candidate("c2", "vault/Roadmap.md", title="Roadmap", heading="Roadmap > Scope", score=0.9),
            ],
            tool_results=[],
            token_budget=2400,
            allowed_tool_names=[],
        )

        self.assertEqual(bundle.evidence_items[0].source_note_title, "Roadmap")
        self.assertEqual(bundle.evidence_items[0].position_hint, "1/2")
        self.assertEqual(bundle.evidence_items[1].position_hint, "2/2")

    def test_build_ask_context_bundle_truncates_lower_ranked_candidates_before_dropping_them(self) -> None:
        bundle = build_ask_context_bundle(
            user_query="roadmap",
            candidates=[
                _candidate("c1", "vault/Roadmap.md", score=1.0, text="A" * 600),
                _candidate("c2", "vault/Strategy.md", score=0.9, text="B" * 600),
                _candidate("c3", "vault/Notes.md", score=0.8, text="C" * 600),
            ],
            tool_results=[],
            token_budget=1400,
            allowed_tool_names=[],
        )

        self.assertEqual(len(bundle.evidence_items), 3)
        self.assertGreater(len(bundle.evidence_items[0].text), len(bundle.evidence_items[2].text))
        self.assertEqual(bundle.assembly_metadata.summary_char_budget, 280)
        self.assertEqual(bundle.assembly_metadata.final_evidence_count, 3)
```

- [ ] **Step 2: Run the targeted enrichment/budget tests and confirm they fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_adds_source_titles_and_position_hints tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_truncates_lower_ranked_candidates_before_dropping_them -v
```

Expected: FAIL because the current bundle builder does not compute `position_hint`, `source_note_title`, or ranked truncation.

- [ ] **Step 3: Implement the minimal stage-3 and stage-4 logic**

In `backend/app/context/assembly.py`, enrich the final retained candidates and build source-note summaries:

```python
ASK_FULL_TEXT_CHAR_BUDGET = 900
ASK_SUMMARY_CHAR_BUDGET = 280
ASK_FULL_TEXT_EVIDENCE_COUNT = 2


def _apply_weighted_budget(
    candidates: list[RetrievedChunkCandidate],
    token_budget: int,
) -> tuple[list[tuple[RetrievedChunkCandidate, str]], int]:
    kept: list[tuple[RetrievedChunkCandidate, str]] = []
    consumed = 0
    dropped = 0
    for index, candidate in enumerate(candidates):
        char_limit = (
            ASK_FULL_TEXT_CHAR_BUDGET
            if index < ASK_FULL_TEXT_EVIDENCE_COUNT
            else ASK_SUMMARY_CHAR_BUDGET
        )
        visible_text = candidate.text[:char_limit]
        candidate_chars = len(candidate.path) + len(candidate.heading_path or "") + len(visible_text)
        if token_budget > 0 and consumed + candidate_chars > token_budget:
            dropped += 1
            continue
        kept.append((candidate, visible_text))
        consumed += candidate_chars
    return kept, dropped
```

Then materialize evidence:

```python
ContextEvidenceItem(
    source_path=item.path,
    chunk_id=item.chunk_id,
    source_note_title=item.title,
    heading_path=item.heading_path,
    position_hint=f"{position}/{total_for_path}",
    text=visible_text,
    score=item.score,
    source_kind="retrieval",
)
```

Populate `source_notes` and the remaining `assembly_metadata` counters in the same pass.

- [ ] **Step 4: Re-run the targeted tests and make them pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_adds_source_titles_and_position_hints tests.test_context_assembly.AskContextAssemblyTests.test_build_ask_context_bundle_truncates_lower_ranked_candidates_before_dropping_them -v
```

Expected: PASS, proving structured evidence and weighted truncation work together.

- [ ] **Step 5: Commit the enrichment/budget work**

```bash
git add backend/app/context/assembly.py backend/tests/test_context_assembly.py
git commit -m "feat: enrich ask evidence and weighted budgets"
```

### Task 4: Update prompt rendering and ask workflow integration

**Files:**
- Modify: `backend/app/context/render.py`
- Modify: `backend/app/services/ask.py`
- Modify: `backend/tests/test_ask_workflow.py`

- [ ] **Step 1: Write the failing ask integration tests**

```python
class AskWorkflowTests(unittest.TestCase):
    def test_run_minimal_ask_includes_source_title_and_position_hint_in_prompt(self) -> None:
        captured = {}

        def _capture_grounded_answer(*, provider_target, query, bundle):
            captured["prompt"] = render_grounded_answer_prompt(bundle)
            return "Roadmap 当前只记录问答结果的引用要求。[1]"

        with patch("app.services.ask._request_grounded_answer", side_effect=_capture_grounded_answer):
            result = run_minimal_ask(
                WorkflowInvokeRequest(
                    action_type=WorkflowAction.ASK_QA,
                    user_query="Roadmap",
                ),
                settings=settings,
            )

        self.assertEqual(result.mode, AskResultMode.GENERATED_ANSWER)
        self.assertIn("source_note_title: Roadmap", captured["prompt"])
        self.assertIn("position_hint: 1/1", captured["prompt"])

    def test_run_minimal_ask_builds_citations_from_post_assembly_visible_evidence(self) -> None:
        result = run_minimal_ask(...)
        self.assertEqual(len(result.citations), len(result.retrieved_candidates))
        self.assertLessEqual(len(result.retrieved_candidates), 4)
```

- [ ] **Step 2: Run the targeted ask tests and watch them fail**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_includes_source_title_and_position_hint_in_prompt tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_builds_citations_from_post_assembly_visible_evidence -v
```

Expected: FAIL because the prompt renderer does not yet emit the new fields and ask integration has not been proven against the assembled evidence list.

- [ ] **Step 3: Implement the minimal render/integration changes**

Render the new retrieval fields in `backend/app/context/render.py`:

```python
lines.extend(
    [
        f"[{index}] path: {item.source_path}",
        f"source_note_title: {item.source_note_title or item.source_path}",
        f"heading_path: {item.heading_path or item.source_path}",
        f"position_hint: {item.position_hint or '1/1'}",
        "content:",
        item.text,
        "",
    ]
)
```

Keep `backend/app/services/ask.py` deriving prompt candidates from `bundle.evidence_items` only, so citations remain aligned with the post-assembly visible retrieval evidence instead of the raw retrieval list.

- [ ] **Step 4: Re-run the targeted ask tests and make them pass**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_includes_source_title_and_position_hint_in_prompt tests.test_ask_workflow.AskWorkflowTests.test_run_minimal_ask_builds_citations_from_post_assembly_visible_evidence -v
```

Expected: PASS, showing the prompt and citations now reflect the assembled evidence.

- [ ] **Step 5: Commit the ask integration work**

```bash
git add backend/app/context/render.py backend/app/services/ask.py backend/tests/test_ask_workflow.py
git commit -m "feat: wire ask to structured assembly evidence"
```

### Task 5: Run full verification and document any follow-up gaps

**Files:**
- Modify: `backend/tests/test_context_assembly.py`
- Modify: `backend/tests/test_ask_workflow.py`
- No planned production changes unless verification finds a real regression

- [ ] **Step 1: Run the full ask-related backend suites**

Run from `backend/`:

```bash
../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly tests.test_ask_workflow -v
```

Expected: PASS with no newly introduced failures.

- [ ] **Step 2: Run the focused offline eval cases that exercise ask fallback and hybrid retrieval**

Run from repo root:

```bash
./.conda/knowledge-steward/bin/python eval/run_eval.py \
  --case-id ask_fixture_hybrid_retrieval_only \
  --case-id ask_fixture_generated_answer_citation_valid \
  --output /tmp/task047-ask-eval.json
```

Expected: exit code `0` and a summary line reporting `2 passed, 0 failed`.

- [ ] **Step 3: If verification fails, add the smallest missing regression test first**

Examples:

```python
def test_build_ask_context_bundle_keeps_suspicious_retrieval_text_out_of_prompt_visible_evidence(self) -> None:
    ...
```

Only add a new test if the failure reveals a real behavior gap. Do not broaden the task into trace wiring, config extraction, or eval threshold tuning.

- [ ] **Step 4: Re-run the exact failing verification command until it passes**

Run whichever command failed in Step 1 or Step 2, then repeat the full verification sweep:

```bash
cd backend && ../.conda/knowledge-steward/bin/python -m unittest tests.test_context_assembly tests.test_ask_workflow -v
cd /Users/qi/PycharmProjects/Obsidian-Knowledge-Steward && ./.conda/knowledge-steward/bin/python eval/run_eval.py --case-id ask_fixture_hybrid_retrieval_only --case-id ask_fixture_generated_answer_citation_valid --output /tmp/task047-ask-eval.json
```

- [ ] **Step 5: Commit the verified implementation**

```bash
git add backend/app/contracts/workflow.py backend/app/context/assembly.py backend/app/context/render.py backend/app/services/ask.py backend/tests/test_context_assembly.py backend/tests/test_ask_workflow.py
git commit -m "feat: add staged ask context assembly pipeline"
```

## Execution Notes

- Do not touch `docs/` during implementation. Governance sync belongs to session closeout, not the coding phase.
- Do not edit unrelated dirty files such as `backend/app/services/proposal_validation.py`, SQLite DB files, or runtime traces unless verification explicitly proves the task depends on them.
- If `TASK-047` exposes a second medium-sized follow-up such as trace wiring or config extraction, stop and log it as a derived task instead of continuing inline.
