from __future__ import annotations

from enum import Enum
import sqlite3

from app.config import Settings
from app.contracts.workflow import RetrievedChunkCandidate, RetrievalSearchResponse
from app.retrieval.hybrid import HYBRID_BRANCH_MIN_LIMIT, _fuse_candidates
from app.retrieval.sqlite_fts import search_chunks
from app.retrieval.sqlite_vector import search_chunk_vectors


RETRIEVAL_BENCHMARK_LIMIT = 10


class RetrievalBenchmarkMode(str, Enum):
    FTS_ONLY = "fts_only"
    VECTOR_ONLY = "vector_only"
    HYBRID_RRF = "hybrid_rrf"


class RetrievalBenchmarkModeError(RuntimeError):
    pass


def run_retrieval_mode(
    connection: sqlite3.Connection,
    query: str,
    settings: Settings,
    mode: RetrievalBenchmarkMode | str,
) -> list[RetrievedChunkCandidate]:
    normalized_mode = _normalize_mode(mode)
    try:
        response = _dispatch_retrieval_mode(
            connection=connection,
            query=query,
            settings=settings,
            mode=normalized_mode,
        )
    except RetrievalBenchmarkModeError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise RetrievalBenchmarkModeError(
            f"Retrieval mode {normalized_mode.value} failed: {exc}"
        ) from exc

    if response.disabled:
        reason = response.disabled_reason or "disabled"
        raise RetrievalBenchmarkModeError(
            f"Retrieval mode {normalized_mode.value} is disabled: {reason}"
        )

    return response.candidates


def _normalize_mode(mode: RetrievalBenchmarkMode | str) -> RetrievalBenchmarkMode:
    if isinstance(mode, RetrievalBenchmarkMode):
        return mode
    try:
        return RetrievalBenchmarkMode(mode)
    except ValueError as exc:
        raise RetrievalBenchmarkModeError(f"Unsupported retrieval benchmark mode: {mode!r}") from exc


def _dispatch_retrieval_mode(
    *,
    connection: sqlite3.Connection,
    query: str,
    settings: Settings,
    mode: RetrievalBenchmarkMode,
) -> RetrievalSearchResponse:
    match mode:
        case RetrievalBenchmarkMode.FTS_ONLY:
            return search_chunks(
                connection,
                query,
                limit=RETRIEVAL_BENCHMARK_LIMIT,
                vault_root=settings.sample_vault_dir,
            )
        case RetrievalBenchmarkMode.VECTOR_ONLY:
            return search_chunk_vectors(
                connection,
                query,
                settings=settings,
                limit=RETRIEVAL_BENCHMARK_LIMIT,
            )
        case RetrievalBenchmarkMode.HYBRID_RRF:
            return _run_hybrid_rrf(
                connection=connection,
                query=query,
                settings=settings,
            )

    raise RetrievalBenchmarkModeError(f"Unsupported retrieval benchmark mode: {mode.value}")


def _run_hybrid_rrf(
    connection: sqlite3.Connection,
    query: str,
    settings: Settings,
) -> RetrievalSearchResponse:
    branch_limit = max(RETRIEVAL_BENCHMARK_LIMIT, HYBRID_BRANCH_MIN_LIMIT)
    lexical_response = search_chunks(
        connection,
        query,
        limit=branch_limit,
        vault_root=settings.sample_vault_dir,
    )
    vector_response = search_chunk_vectors(
        connection,
        query,
        settings=settings,
        limit=branch_limit,
    )
    if vector_response.disabled:
        reason = vector_response.disabled_reason or "disabled"
        raise RetrievalBenchmarkModeError(
            f"Retrieval mode {RetrievalBenchmarkMode.HYBRID_RRF.value} is disabled: {reason}"
        )

    fused_candidates = _fuse_candidates(
        lexical_candidates=lexical_response.candidates,
        vector_candidates=vector_response.candidates,
        limit=RETRIEVAL_BENCHMARK_LIMIT,
    )
    return RetrievalSearchResponse(
        candidates=fused_candidates,
        requested_filters=lexical_response.requested_filters,
        effective_filters=lexical_response.effective_filters,
        fallback_used=lexical_response.fallback_used or vector_response.fallback_used,
        fallback_reason=lexical_response.fallback_reason or vector_response.fallback_reason,
        provider_name=vector_response.provider_name,
        model_name=vector_response.model_name,
    )
