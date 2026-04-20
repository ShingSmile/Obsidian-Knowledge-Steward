from __future__ import annotations

from enum import Enum
import sqlite3

from app.config import Settings
from app.contracts.workflow import RetrievedChunkCandidate, RetrievalSearchResponse
from app.retrieval.embeddings import resolve_embedding_provider_targets
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
            _ensure_hybrid_vector_backend_ready(connection, settings)
            return search_hybrid_chunks(
                connection,
                query,
                settings=settings,
                limit=RETRIEVAL_BENCHMARK_LIMIT,
            )

    raise RetrievalBenchmarkModeError(f"Unsupported retrieval benchmark mode: {mode.value}")


def _ensure_hybrid_vector_backend_ready(
    connection: sqlite3.Connection,
    settings: Settings,
) -> None:
    targets = resolve_embedding_provider_targets(settings=settings)
    if not targets:
        raise RetrievalBenchmarkModeError(
            f"Retrieval mode {RetrievalBenchmarkMode.HYBRID_RRF.value} is disabled: "
            "no_available_embedding_provider"
        )

    chunk_count = _fetch_scalar_count(connection, "SELECT COUNT(*) FROM chunk;")
    if chunk_count == 0:
        return

    for target in targets:
        embedding_count = _fetch_scalar_count(
            connection,
            """
            SELECT COUNT(*)
            FROM chunk_embedding
            WHERE provider_key = ? AND model_name = ?;
            """,
            target.provider_key,
            target.model_name,
        )
        if embedding_count > 0:
            return

    raise RetrievalBenchmarkModeError(
        f"Retrieval mode {RetrievalBenchmarkMode.HYBRID_RRF.value} is disabled: "
        "vector_index_not_ready"
    )


def _fetch_scalar_count(
    connection: sqlite3.Connection,
    query: str,
    *params: object,
) -> int:
    row = connection.execute(query, params).fetchone()
    if row is None:
        return 0
    return int(row[0] or 0)
