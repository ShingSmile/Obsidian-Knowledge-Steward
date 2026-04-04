from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sqlite3

from app.config import Settings, get_settings
from app.contracts.workflow import (
    RetrievalMetadataFilter,
    RetrievalSearchResponse,
    RetrievedChunkCandidate,
)
from app.indexing.store import connect_sqlite, initialize_index_db
from app.retrieval.sqlite_fts import _normalize_metadata_filter, search_chunks
from app.retrieval.sqlite_vector import search_chunk_vectors


HYBRID_BRANCH_MIN_LIMIT = 8
HYBRID_RRF_K = 60
HYBRID_RETRIEVAL_SOURCE = "hybrid_rrf"


@dataclass
class _HybridCandidateAccumulator:
    candidates_by_source: dict[str, RetrievedChunkCandidate] = field(default_factory=dict)
    ranks_by_source: dict[str, int] = field(default_factory=dict)
    fused_score: float = 0.0


def search_hybrid_chunks(
    connection: sqlite3.Connection,
    query: str,
    *,
    settings: Settings,
    limit: int = 5,
    metadata_filter: RetrievalMetadataFilter | None = None,
    provider_preference: str | None = None,
    allow_filter_fallback: bool = True,
) -> RetrievalSearchResponse:
    if limit <= 0:
        raise ValueError("Search limit must be greater than 0.")

    requested_filter = _normalize_metadata_filter(
        metadata_filter,
        vault_root=settings.sample_vault_dir,
    )
    primary_response = _search_hybrid_once(
        connection,
        query,
        settings=settings,
        limit=limit,
        metadata_filter=requested_filter,
        provider_preference=provider_preference,
    )
    if primary_response.candidates:
        return primary_response

    if allow_filter_fallback and not requested_filter.is_empty():
        # 这里把 filter fallback 放在 hybrid 总入口统一处理，而不是让 FTS / vector 各自放宽，
        # 是为了避免两条分支的 effective filter 漂移，导致上游拿到一组“看似融合、实际条件不同”的候选。
        fallback_response = _search_hybrid_once(
            connection,
            query,
            settings=settings,
            limit=limit,
            metadata_filter=RetrievalMetadataFilter(),
            provider_preference=provider_preference,
        )
        return fallback_response.model_copy(
            update={
                "requested_filters": requested_filter,
                "effective_filters": RetrievalMetadataFilter(),
                "fallback_used": True,
                "fallback_reason": "metadata_filters_too_strict",
            }
        )

    return primary_response


def search_hybrid_chunks_in_db(
    db_path: Path,
    query: str,
    *,
    settings: Settings | None = None,
    limit: int = 5,
    metadata_filter: RetrievalMetadataFilter | None = None,
    provider_preference: str | None = None,
    allow_filter_fallback: bool = True,
) -> RetrievalSearchResponse:
    runtime_settings = settings or get_settings()
    initialized_db_path = initialize_index_db(
        db_path,
        settings=runtime_settings,
    )
    connection = connect_sqlite(initialized_db_path)
    try:
        return search_hybrid_chunks(
            connection,
            query,
            settings=runtime_settings,
            limit=limit,
            metadata_filter=metadata_filter,
            provider_preference=provider_preference,
            allow_filter_fallback=allow_filter_fallback,
        )
    finally:
        connection.close()


def _search_hybrid_once(
    connection: sqlite3.Connection,
    query: str,
    *,
    settings: Settings,
    limit: int,
    metadata_filter: RetrievalMetadataFilter,
    provider_preference: str | None,
) -> RetrievalSearchResponse:
    branch_limit = max(limit, HYBRID_BRANCH_MIN_LIMIT)
    fts_response = search_chunks(
        connection,
        query,
        limit=branch_limit,
        metadata_filter=metadata_filter,
        allow_filter_fallback=False,
        vault_root=settings.sample_vault_dir,
    )
    vector_response = search_chunk_vectors(
        connection,
        query,
        settings=settings,
        limit=branch_limit,
        metadata_filter=metadata_filter,
        provider_preference=provider_preference,
        allow_filter_fallback=False,
    )

    candidates = _fuse_candidates(
        lexical_candidates=fts_response.candidates,
        vector_candidates=vector_response.candidates,
        limit=limit,
    )
    return RetrievalSearchResponse(
        candidates=candidates,
        requested_filters=metadata_filter,
        effective_filters=metadata_filter,
        fallback_used=False,
        fallback_reason=None,
        provider_name=vector_response.provider_name,
        model_name=vector_response.model_name,
    )


def _fuse_candidates(
    *,
    lexical_candidates: list[RetrievedChunkCandidate],
    vector_candidates: list[RetrievedChunkCandidate],
    limit: int,
) -> list[RetrievedChunkCandidate]:
    accumulators: dict[str, _HybridCandidateAccumulator] = {}
    _merge_branch_candidates(
        accumulators,
        candidates=lexical_candidates,
        source_name="sqlite_fts",
    )
    _merge_branch_candidates(
        accumulators,
        candidates=vector_candidates,
        source_name="sqlite_vector",
    )

    fused_candidates: list[RetrievedChunkCandidate] = []
    for accumulator in accumulators.values():
        preferred_candidate = accumulator.candidates_by_source.get("sqlite_fts")
        if preferred_candidate is None:
            preferred_candidate = accumulator.candidates_by_source["sqlite_vector"]

        retrieval_source = (
            HYBRID_RETRIEVAL_SOURCE
            if len(accumulator.candidates_by_source) > 1
            else next(iter(accumulator.candidates_by_source))
        )
        fused_candidates.append(
            preferred_candidate.model_copy(
                update={
                    "retrieval_source": retrieval_source,
                    "score": accumulator.fused_score,
                }
            )
        )

    # 这里显式使用 RRF，而不是直接拼接 bm25 和 cosine 原始分数，
    # 是为了避免两种量纲硬相加后让某一路长期压死另一条，先把 hybrid 做成稳健可回归的底座。
    fused_candidates.sort(
        key=lambda candidate: (
            -candidate.score,
            candidate.path,
            candidate.start_line,
        )
    )
    return fused_candidates[:limit]


def _merge_branch_candidates(
    accumulators: dict[str, _HybridCandidateAccumulator],
    *,
    candidates: list[RetrievedChunkCandidate],
    source_name: str,
) -> None:
    for rank, candidate in enumerate(candidates, start=1):
        accumulator = accumulators.setdefault(
            candidate.chunk_id,
            _HybridCandidateAccumulator(),
        )
        accumulator.candidates_by_source[source_name] = candidate
        accumulator.ranks_by_source[source_name] = rank
        accumulator.fused_score += _rrf_score(rank)


def _rrf_score(rank: int) -> float:
    return 1.0 / (HYBRID_RRF_K + rank)
