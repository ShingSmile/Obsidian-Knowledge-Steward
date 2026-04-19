# Ask Benchmark Dataset Contract

Scope: `TASK-057` only.

## Files

- `eval/benchmark/ask_benchmark_cases.json`
  - formal dataset
  - approved cases only
- `eval/benchmark/ask_benchmark_review_backlog.json`
  - review backlog for `revise` and `reject`
- `eval/benchmark/ask_benchmark_spec.md`
  - operator-facing contract summary

## Case Shape

Approved dataset cases use this shape:

```json
{
  "case_id": "ask_case_001",
  "bucket": "single_hop",
  "user_query": "总结这篇笔记",
  "source_origin": "sample_vault",
  "expected_relevant_paths": ["日常/2024-03-14_星期四.md"],
  "expected_relevant_locators": [
    {
      "note_path": "日常/2024-03-14_星期四.md",
      "heading_path": "一、工作任务",
      "excerpt_anchor": "完成 digest graph"
    }
  ],
  "expected_facts": ["今天接通了 DAILY_DIGEST。"],
  "forbidden_claims": [],
  "allow_tool": false,
  "expected_tool_names": [],
  "allow_retrieval_only": false,
  "should_generate_answer": true,
  "review_status": "approved",
  "review_notes": "seed"
}
```

Allowed bucket values:

- `single_hop`
- `multi_hop`
- `metadata_filter`
- `abstain_or_no_hit`
- `tool_allowed`

Allowed source origins:

- `sample_vault`
- `fixture`

Formal dataset rule:

- every case in `ask_benchmark_cases.json` must have `review_status="approved"`

Locator rule:

- every locator must include `note_path`, `heading_path`, and `excerpt_anchor`

## Backlog Shape

Backlog items use the same core case fields, but `review_status` is either `revise`
or `reject`. Backlog items also persist the original candidate `fingerprint` so the
review backlog can preserve the full incoming payload and reject fingerprint collisions
during apply-review.

`apply-review` accepts partial review files. Only the case_ids present in the review
file are applied; unreviewed candidates from the batch are skipped and reported in the
operator success output.

Review-file validation is strict. Every reviewed candidate or backlog item must have
non-empty `expected_relevant_paths`, `expected_relevant_locators`, and `expected_facts`,
and each locator `note_path` must appear in `expected_relevant_paths`.

## Commands

Load the formal dataset:

```python
from app.benchmark.ask_dataset import load_ask_benchmark_dataset

dataset = load_ask_benchmark_dataset()
```

Load the review backlog:

```python
from app.benchmark.ask_dataset import load_ask_benchmark_backlog

backlog = load_ask_benchmark_backlog()
```

Write the formal dataset:

```python
from app.benchmark.ask_dataset import write_ask_benchmark_dataset

write_ask_benchmark_dataset(dataset)
```

Write the review backlog:

```python
from app.benchmark.ask_dataset import write_ask_benchmark_backlog

write_ask_benchmark_backlog(backlog)
```
