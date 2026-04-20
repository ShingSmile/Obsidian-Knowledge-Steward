from __future__ import annotations

from enum import Enum
import sqlite3

from app.config import Settings
from app.contracts.workflow import RetrievedChunkCandidate, RetrievalSearchResponse
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
            vector_probe_response = search_chunk_vectors(
                connection,
                query,
                settings=settings,
                limit=RETRIEVAL_BENCHMARK_LIMIT,
            )
            if vector_probe_response.disabled:
                reason = vector_probe_response.disabled_reason or "disabled"
                raise RetrievalBenchmarkModeError(
                    f"Retrieval mode {mode.value} is disabled: {reason}"
                )
            return search_hybrid_chunks(
                connection,
                query,
                settings=settings,
                limit=RETRIEVAL_BENCHMARK_LIMIT,
            )

    raise RetrievalBenchmarkModeError(f"Unsupported retrieval benchmark mode: {mode.value}")
