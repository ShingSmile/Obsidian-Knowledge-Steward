# TASK-057 Ask Benchmark Dataset Design

**Task:** `TASK-057`

**Session:** `SES-20260418-03`

**Problem**

The current ask offline eval in `eval/` is still a mixed regression baseline. It
combines real `sample_vault` cases, deterministic fixtures, retrieval-only
fallbacks, generated-answer cases, and tool/guardrail paths inside the same
golden suite. That is enough to catch contract regressions, but it is not yet a
fixed ask benchmark dataset that can answer a narrower question: what should the
system retrieve and say for a stable set of representative ask queries?

`TASK-057` exists to create that dataset layer first. It should define the case
contract, sample sourcing rules, locator contract, review loop, and minimal
validation needed to build a fixed set of `50` approved ask benchmark cases. It
should not leak into retrieval metrics, provider benchmarking, or answer-level
runtime ablations from later tasks.

**Goal**

Create a dedicated ask benchmark dataset for `TASK-057` only:

- a fixed `50`-case ask benchmark asset
- at least `40` approved cases sourced from real `sample_vault` content
- a case schema centered on evidence location and ideal target behavior
- a review loop that proposes `5` cases at a time for human approval
- minimal validation that checks schema, locator resolution, drift, and bucket
  distribution

**Non-Goals**

- Do not implement retrieval benchmark runners or rank-based metrics.
- Do not design `TASK-058` or `TASK-059` execution contracts.
- Do not wire real providers into eval.
- Do not migrate the existing regression `eval/golden/*.json` suites.
- Do not auto-repair locator drift.
- Do not create a draft-only staging system that duplicates the formal dataset.

**Approaches Considered**

1. `Schema-first`
   Rejected because it front-loads too much design work before the first approved
   cases exist. `TASK-057` needs a usable dataset quickly, not a large framework.
2. `Review-loop-first`
   Recommended because it keeps the contract thin but complete, then lets the
   formal dataset grow in small approved batches.
3. `Markdown-first`
   Rejected because it creates a second source of truth and delays the creation
   of the formal machine-readable dataset.

**Recommended Approach**

Use a `review-loop-first` workflow:

1. define a minimal formal case contract
2. generate candidate cases mainly from `sample_vault`
3. review `5` candidates per batch with explicit recommendations
4. write approved cases directly into the formal benchmark file
5. record `revise` and `reject` outcomes in a separate backlog file
6. repeat until the formal dataset reaches `50` approved cases

This keeps the benchmark dataset growing as a real asset from the first review
batch onward, without waiting for all `50` cases to exist.

## 1. Dataset Scope

This design is intentionally limited to `TASK-057`.

It defines:

- where the benchmark dataset lives
- what fields each case must contain
- how evidence is located
- how case reviews are handled
- what validation is required before a case is accepted

It does not define:

- retrieval-only benchmark modes
- metric panels such as `Recall@K`, `MRR`, or `NDCG`
- real-provider answer runs
- runtime gate trade-off experiments

Those belong to later tasks and must not be preloaded into this dataset design.

## 2. Asset Layout

Create a dedicated directory under `eval/benchmark/` with three assets:

- `eval/benchmark/ask_benchmark_cases.json`
  - the formal dataset
  - contains approved cases only
- `eval/benchmark/ask_benchmark_spec.md`
  - human-readable schema, annotation rules, locator rules, review workflow, and
    acceptance guidance
- `eval/benchmark/ask_benchmark_review_backlog.json`
  - candidate cases that were marked `revise` or `reject`, plus short reasons

This keeps the new benchmark layer physically separate from the current
regression-oriented `eval/golden/` suites and avoids mixing approved truth data
with work-in-progress review artifacts.

## 3. Case Sourcing Strategy

The formal `50` cases should be built mainly from real `sample_vault` content.

Required sourcing rules:

- at least `40` approved cases must come from `sample_vault`
- candidate queries should be generated conservatively from real note content:
  headings, task items, explicit facts, dates, metadata, and natural summary
  prompts
- user-view rewrites are allowed only when the literal source wording would be
  too unnatural as a question
- deterministic fixtures are allowed only when a bucket cannot be covered
  adequately with real `sample_vault` cases

This preserves a benchmark dataset that still feels like real usage, while
allowing limited fixture fallback for coverage holes.

## 4. Review Loop

The benchmark should be built through repeated small review batches.

Review rules:

1. generate `5` candidate cases at a time
2. present each candidate with recommended annotations
3. the human reviewer returns one of:
   - `approve`
   - `revise`
   - `reject`
4. write outcomes immediately:
   - `approve` -> formal dataset
   - `revise` or `reject` -> review backlog
5. continue batch-by-batch until the formal dataset contains `50` approved cases

This process intentionally avoids a large draft pool. Approved cases become part
of the formal dataset immediately instead of waiting for a later merge step.

## 5. Formal Case Contract

Each approved benchmark case must contain at least:

- `case_id`
- `bucket`
- `user_query`
- `source_origin`
- `expected_relevant_paths`
- `expected_relevant_locators`
- `expected_facts`
- `forbidden_claims`
- `allow_tool`
- `expected_tool_names`
- `allow_retrieval_only`
- `should_generate_answer`
- `review_status`
- `review_notes`

Required case-level enums:

- `bucket` must be exactly one primary value from:
  - `single_hop`
  - `multi_hop`
  - `metadata_filter`
  - `abstain_or_no_hit`
  - `tool_allowed`
- `source_origin` must be one of:
  - `sample_vault`
  - `fixture`
- `review_status` inside the formal dataset must be:
  - `approved`

Field intent:

- `case_id`
  - globally unique identifier for the benchmark case
- `bucket`
  - the coverage bucket the case belongs to
- `user_query`
  - the natural-language ask query under test
- `source_origin`
  - whether the case came from `sample_vault` or a fixture fallback
- `expected_relevant_paths`
  - note-level truth: which notes should matter
- `expected_relevant_locators`
  - section-level truth: which evidence locations matter inside those notes
- `expected_facts`
  - the must-cover facts a correct answer should support
- `forbidden_claims`
  - claims a correct answer must not assert
- `allow_tool`
  - whether tool usage is acceptable for the ideal target behavior
- `expected_tool_names`
  - the tool names that are acceptable when tool usage is allowed
- `allow_retrieval_only`
  - whether retrieval-only fallback is acceptable for the ideal target behavior
- `should_generate_answer`
  - whether the ideal target behavior is to produce a generated answer
- `review_status`
  - fixed to `approved` inside the formal dataset
- `review_notes`
  - short human-review notes that preserve why the final case shape was accepted

The benchmark should be annotated against ideal target behavior, not current
system limitations. In particular, `allow_tool`, `allow_retrieval_only`, and
`should_generate_answer` should not be biased toward current implementation
gaps.

`bucket` is intentionally a single primary classification so the formal
distribution can be validated unambiguously against the target `50`-case shape.
If a case allows tools, it should be classified into the `tool_allowed` bucket
instead of also being counted inside another bucket.

## 6. Locator Contract

The evidence locator contract should prioritize stability over maximal precision.

Each locator should use:

- primary key: `note_path + heading_path`
- secondary disambiguation: `line_range`
- drift anchor: `excerpt_anchor`

The minimum locator object shape should be:

- `note_path`
- `heading_path`
- `line_range`
  - `start_line`
  - `end_line`
- `excerpt_anchor`

Rules:

- `note_path` is required
- `heading_path` is required
- `line_range` is optional but recommended when one heading contains multiple
  plausible evidence spans
- `excerpt_anchor` is required for drift detection, even when `line_range` is
  present

Rationale:

- `heading_path` is more stable than raw line numbers when note bodies change
- `line_range` remains useful inside one heading when multiple chunks exist
- `excerpt_anchor` provides a lightweight content check without turning the
  contract into a runtime `chunk_id` dependency

The locator contract should stay human-readable. `chunk_id` is intentionally not
the primary contract for `TASK-057`, even though the runtime can materialize it.

## 7. Drift Handling

The benchmark must fail explicitly on drift instead of auto-repairing data.

Drift policy:

- `note_path` missing
  - hard failure
  - case returns to manual review
- `heading_path` missing but note still exists
  - mark as locator drift
  - require manual review
- `heading_path` resolves but `line_range` drifts
  - warning first
  - if `excerpt_anchor` still matches, the case can remain valid
  - if `excerpt_anchor` also fails, return the case for manual revision
- `expected_facts` or `forbidden_claims` no longer match current note content
  - treat as content drift
  - require manual review

No automatic fuzzy rewrite should mutate formal cases silently. The benchmark is
meant to surface drift, not mask it.

## 8. Review Conflict Policy

The human reviewer is the source of truth for benchmark acceptance.

Rules:

- human decisions override model suggestions
- only the approved version of a case enters the formal dataset
- `revise` and `reject` cases remain in backlog, not the formal dataset
- if a candidate needs heavy rewriting across repeated review loops, it is better
  to discard it and propose a new one than to preserve a weak candidate

This keeps the formal benchmark from accumulating ambiguous or over-repaired
cases.

## 9. Validation Boundary

`TASK-057` only needs minimal validation for dataset integrity and locator
correctness.

Required validation:

- schema validation
  - required fields exist
  - field types are correct
  - enums and booleans are valid
- uniqueness validation
  - `case_id` values are unique
- path validation
  - every `expected_relevant_path` resolves
- locator validation
  - `note_path + heading_path` resolves
  - `line_range`, when present, falls inside the resolved heading scope
  - `excerpt_anchor` still matches the intended section
- distribution validation
  - bucket counts satisfy the planned distribution
  - approved `sample_vault` cases stay at or above `40`
- workflow validation
  - approved cases are written only to the formal dataset
  - `revise` and `reject` cases are written only to the backlog

Out of scope for `TASK-057` validation:

- retrieval ranking correctness
- benchmark metric aggregation
- provider execution
- runtime answer quality scoring

Those belong to later tasks.

## 10. Candidate Bucket Distribution

The benchmark should preserve the `TASK-057` target shape:

- `20` single-hop factual QA cases
- `10` multi-hop QA cases
- `8` metadata/tag/date filter cases
- `6` abstain or `no-hit` cases
- `6` tool-allowed cases

Batch reviews do not need to be perfectly balanced. The requirement is that the
formal dataset converges to this distribution by the time it reaches `50`
approved cases.

## 11. Execution Flow

The end-to-end workflow for `TASK-057` should be:

1. initialize `eval/benchmark/` assets
2. generate candidate cases mainly from `sample_vault`
3. present `5` candidates per review batch
4. apply human review outcomes immediately
5. validate formal data after each write
6. continue until `50` approved cases exist

The benchmark becomes useful incrementally. It does not wait for a later
"publish" step.

## 12. Acceptance Check

`TASK-057` is satisfied when:

- `eval/benchmark/` contains the formal dataset, human-readable spec, and review
  backlog
- the formal dataset contains exactly `50` approved ask benchmark cases
- at least `40` approved cases come from `sample_vault`
- every approved case follows the formal contract
- locators use `note_path + heading_path` as primary matching, with `line_range`
  for disambiguation and `excerpt_anchor` for drift checks
- minimal validation exists for schema, locator resolution, drift, uniqueness,
  and bucket distribution
- the review loop is codified as `5` cases per batch with immediate formal
  writes for approvals

**Files**

- Add: `eval/benchmark/ask_benchmark_cases.json`
- Add: `eval/benchmark/ask_benchmark_spec.md`
- Add: `eval/benchmark/ask_benchmark_review_backlog.json`
- Add: minimal validation script or tests under `eval/` or `backend/tests/`

**Testing Strategy**

- validate formal schema and required fields
- validate unique `case_id`
- validate `note_path + heading_path` resolution
- validate `line_range` containment within the intended heading
- validate `excerpt_anchor` drift checks
- validate batch outcome routing:
  - approvals go to the formal dataset
  - `revise` and `reject` go to backlog only

**Risks**

- heading names may change less often than line numbers, but they can still
  drift and invalidate locators
- forcing all annotation against ideal behavior may initially create cases the
  current system fails badly
- human review can become slow if candidate quality is poor
- bucket quotas may look correct numerically while still overfitting to a narrow
  style of query

**Mitigations**

- use `excerpt_anchor` as an explicit drift signal instead of relying on line
  ranges alone
- keep the benchmark honest by annotating ideal target behavior now and letting
  later tasks measure the gap
- prefer generating conservative candidates from real note content to reduce
  rewrite load during review
- use the backlog file to record why candidates were rejected or sent back for
  revision so the generation strategy can be tightened over time
