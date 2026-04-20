from __future__ import annotations

import math
import unittest

from app.benchmark.ask_dataset import AskBenchmarkLocator
from app.benchmark.ask_retrieval_metrics import (
    candidate_matches_locator,
    compute_case_mode_metrics,
    compute_mode_summary,
    first_matching_rank,
)
from app.contracts.workflow import RetrievedChunkCandidate


def _candidate(
    *,
    path: str = "Notes/Alpha.md",
    heading_path: str | None = "Summary",
    text: str = "alpha",
    snippet: str = "snippet",
) -> RetrievedChunkCandidate:
    return RetrievedChunkCandidate(
        chunk_id="chunk-1",
        note_id="note-1",
        path=path,
        title="Alpha",
        heading_path=heading_path,
        note_type="note",
        template_family="default",
        daily_note_date=None,
        source_mtime_ns=1,
        start_line=1,
        end_line=1,
        score=1.0,
        snippet=snippet,
        text=text,
    )


class AskRetrievalMetricsTest(unittest.TestCase):
    def test_candidate_matches_locator_requires_exact_paths_and_trimmed_anchor(self) -> None:
        locator = AskBenchmarkLocator(
            note_path="Notes/Alpha.md",
            heading_path="Summary",
            excerpt_anchor="  first line\r\nsecond line  ",
        )
        candidate = _candidate(
            text="preamble first line\nsecond line postscript",
        )

        self.assertTrue(candidate_matches_locator(candidate, locator))

        self.assertFalse(
            candidate_matches_locator(
                _candidate(path="Notes/Beta.md", text="first line\nsecond line"),
                locator,
            )
        )
        self.assertFalse(
            candidate_matches_locator(
                _candidate(heading_path="Details", text="first line\nsecond line"),
                locator,
            )
        )
        self.assertFalse(
            candidate_matches_locator(
                _candidate(text="Snippet only here", snippet="first line\nsecond line"),
                locator,
            )
        )
        self.assertFalse(
            candidate_matches_locator(
                _candidate(text="FIRST LINE\nSECOND LINE"),
                locator,
            )
        )

    def test_first_matching_rank_returns_one_based_rank(self) -> None:
        locator = AskBenchmarkLocator(
            note_path="Notes/Alpha.md",
            heading_path="Summary",
            excerpt_anchor="anchor",
        )
        candidates = [
            _candidate(text="miss"),
            _candidate(text="anchor"),
            _candidate(text="anchor"),
        ]

        self.assertEqual(first_matching_rank(candidates, locator), 2)
        self.assertIsNone(first_matching_rank([_candidate(text="miss")], locator))

    def test_compute_case_mode_metrics_uses_case_level_recall_and_binary_ndcg(self) -> None:
        expected_locators = [
            AskBenchmarkLocator(
                note_path="Notes/Alpha.md",
                heading_path="Summary",
                excerpt_anchor="alpha",
            ),
            AskBenchmarkLocator(
                note_path="Notes/Alpha.md",
                heading_path="Summary",
                excerpt_anchor="beta",
            ),
        ]
        candidates = [
            _candidate(text="alpha and beta"),
            _candidate(text="miss"),
            _candidate(text="miss"),
            _candidate(text="miss"),
            _candidate(text="miss"),
            _candidate(text="miss"),
            _candidate(text="miss"),
            _candidate(text="miss"),
            _candidate(text="miss"),
            _candidate(text="miss"),
        ]

        metrics = compute_case_mode_metrics(expected_locators, candidates)

        self.assertEqual(metrics["hit_at_5"], 1)
        self.assertEqual(metrics["hit_at_10"], 1)
        self.assertAlmostEqual(
            metrics["ndcg_at_10"],
            1.0 / (1.0 + (1.0 / math.log2(3.0))),
        )

    def test_compute_mode_summary_averages_case_metrics(self) -> None:
        case_metrics = [
            {"hit_at_5": 1, "hit_at_10": 1, "ndcg_at_10": 1.0},
            {"hit_at_5": 0, "hit_at_10": 0, "ndcg_at_10": 0.0},
        ]

        summary = compute_mode_summary(case_metrics)

        self.assertEqual(summary["Recall@5"], 0.5)
        self.assertEqual(summary["Recall@10"], 0.5)
        self.assertEqual(summary["NDCG@10"], 0.5)


if __name__ == "__main__":
    unittest.main()
