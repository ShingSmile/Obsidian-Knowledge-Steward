from __future__ import annotations

from enum import Enum
import sqlite3
from unittest.mock import patch

from app.config import Settings
from app.contracts.workflow import RetrievedChunkCandidate, RetrievalSearchResponse
import app.retrieval.hybrid as hybrid_retrieval
from app.retrieval.hybrid import search_hybrid_chunks
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
            return _run_hybrid_with_vector_tracking(
                connection=connection,
                query=query,
                settings=settings,
            )

    raise RetrievalBenchmarkModeError(f"Unsupported retrieval benchmark mode: {mode.value}")


def _run_hybrid_with_vector_tracking(
    connection: sqlite3.Connection,
    query: str,
    settings: Settings,
) -> RetrievalSearchResponse:
    vector_state = {"disabled": False, "reason": None}
    original_search_chunk_vectors = hybrid_retrieval.search_chunk_vectors

    def _tracking_search_chunk_vectors(
        connection: sqlite3.Connection,
        query: str,
        *,
        settings: Settings,
        limit: int = 5,
        metadata_filter=None,
        provider_preference: str | None = None,
        allow_filter_fallback: bool = True,
    ) -> RetrievalSearchResponse:
        response = original_search_chunk_vectors(
            connection,
            query,
            settings=settings,
            limit=limit,
            metadata_filter=metadata_filter,
            provider_preference=provider_preference,
            allow_filter_fallback=allow_filter_fallback,
        )
        if response.disabled:
            vector_state["disabled"] = True
            vector_state["reason"] = response.disabled_reason
        return response

    with patch.object(hybrid_retrieval, "search_chunk_vectors", _tracking_search_chunk_vectors):
        response = search_hybrid_chunks(
            connection,
            query,
            settings=settings,
            limit=RETRIEVAL_BENCHMARK_LIMIT,
        )

    if vector_state["disabled"]:
        reason = vector_state["reason"] or "disabled"
        raise RetrievalBenchmarkModeError(
            f"Retrieval mode {RetrievalBenchmarkMode.HYBRID_RRF.value} is disabled: {reason}"
        )

    return response
