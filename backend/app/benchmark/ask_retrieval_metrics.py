from __future__ import annotations

from math import log2

from app.benchmark.ask_dataset import AskBenchmarkLocator
from app.contracts.workflow import RetrievedChunkCandidate


def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _normalized_excerpt_anchor(locator: AskBenchmarkLocator) -> str:
    return _normalize_line_endings(locator.excerpt_anchor).strip()


def _normalized_candidate_text(candidate: RetrievedChunkCandidate) -> str:
    return _normalize_line_endings(candidate.text)


def candidate_matches_locator(
    candidate: RetrievedChunkCandidate,
    locator: AskBenchmarkLocator,
) -> bool:
    return (
        candidate.path == locator.note_path
        and candidate.heading_path == locator.heading_path
        and _normalized_excerpt_anchor(locator) in _normalized_candidate_text(candidate)
    )


def first_matching_rank(
    candidates: list[RetrievedChunkCandidate],
    locator: AskBenchmarkLocator,
) -> int | None:
    for rank, candidate in enumerate(candidates, start=1):
        if candidate_matches_locator(candidate, locator):
            return rank
    return None


def _locator_key(locator: AskBenchmarkLocator) -> tuple[str, str | None, str]:
    return (
        locator.note_path,
        locator.heading_path,
        _normalized_excerpt_anchor(locator),
    )


def compute_case_mode_metrics(
    expected_locators: list[AskBenchmarkLocator],
    candidates: list[RetrievedChunkCandidate],
) -> dict[str, object]:
    unique_expected_locator_keys = list(dict.fromkeys(_locator_key(locator) for locator in expected_locators))
    matched_locator_keys: set[tuple[str, str | None, str]] = set()
    matched_locator_ranks: list[int] = []

    for rank, candidate in enumerate(candidates[:10], start=1):
        matched_this_candidate = False
        for locator in expected_locators:
            locator_key = _locator_key(locator)
            if locator_key in matched_locator_keys:
                continue
            if candidate_matches_locator(candidate, locator):
                matched_locator_keys.add(locator_key)
                matched_locator_ranks.append(rank)
                matched_this_candidate = True
                break
        if matched_this_candidate:
            continue

    dcg = sum(1.0 / log2(rank + 1) for rank in matched_locator_ranks)
    idcg = sum(1.0 / log2(rank + 1) for rank in range(1, min(len(unique_expected_locator_keys), 10) + 1))
    ndcg_at_10 = dcg / idcg if idcg > 0 else 0.0

    return {
        "matched_locator_ranks": matched_locator_ranks,
        "hit_at_5": 1 if any(rank <= 5 for rank in matched_locator_ranks) else 0,
        "hit_at_10": 1 if any(rank <= 10 for rank in matched_locator_ranks) else 0,
        "ndcg_at_10": ndcg_at_10,
    }


def compute_mode_summary(case_metrics: list[dict[str, object]]) -> dict[str, float]:
    if not case_metrics:
        return {"Recall@5": 0.0, "Recall@10": 0.0, "NDCG@10": 0.0}

    case_count = float(len(case_metrics))
    return {
        "Recall@5": sum(float(case["hit_at_5"]) for case in case_metrics) / case_count,
        "Recall@10": sum(float(case["hit_at_10"]) for case in case_metrics) / case_count,
        "NDCG@10": sum(float(case["ndcg_at_10"]) for case in case_metrics) / case_count,
    }
