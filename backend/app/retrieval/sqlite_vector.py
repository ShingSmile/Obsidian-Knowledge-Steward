from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3

from app.config import Settings, get_settings
from app.contracts.workflow import (
    RetrievalMetadataFilter,
    RetrievalSearchResponse,
    RetrievedChunkCandidate,
)
from app.indexing.store import connect_sqlite, initialize_index_db
from app.retrieval.embeddings import embed_texts
from app.retrieval.sqlite_fts import _build_filter_sql, _normalize_metadata_filter


VECTOR_SNIPPET_MAX_CHARS = 220


def search_chunk_vectors(
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

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("Vector search query must be a non-empty string.")

    requested_filter = _normalize_metadata_filter(
        metadata_filter,
        vault_root=settings.sample_vault_dir,
    )
    query_embedding_result = embed_texts(
        [normalized_query],
        settings=settings,
        provider_preference=provider_preference,
    )
    if query_embedding_result.disabled:
        return RetrievalSearchResponse(
            candidates=[],
            requested_filters=requested_filter,
            effective_filters=requested_filter,
            disabled=True,
            disabled_reason=query_embedding_result.disabled_reason,
            provider_name=query_embedding_result.provider_name,
            model_name=query_embedding_result.model_name,
        )

    query_embedding = query_embedding_result.embeddings[0]
    matching_embedding_count = _count_matching_embeddings(
        connection,
        provider_key=query_embedding_result.provider_key or "",
        model_name=query_embedding_result.model_name or "",
    )
    if matching_embedding_count == 0:
        chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
        if chunk_count > 0:
            return RetrievalSearchResponse(
                candidates=[],
                requested_filters=requested_filter,
                effective_filters=requested_filter,
                disabled=True,
                disabled_reason="vector_index_not_ready",
                provider_name=query_embedding_result.provider_name,
                model_name=query_embedding_result.model_name,
            )

    candidates = _query_vector_candidates(
        connection,
        query_embedding=query_embedding,
        limit=limit,
        metadata_filter=requested_filter,
        provider_key=query_embedding_result.provider_key or "",
        model_name=query_embedding_result.model_name or "",
    )

    fallback_used = False
    fallback_reason: str | None = None
    effective_filter = requested_filter
    if not candidates and allow_filter_fallback and not requested_filter.is_empty():
        fallback_used = True
        fallback_reason = "metadata_filters_too_strict"
        effective_filter = RetrievalMetadataFilter()
        candidates = _query_vector_candidates(
            connection,
            query_embedding=query_embedding,
            limit=limit,
            metadata_filter=effective_filter,
            provider_key=query_embedding_result.provider_key or "",
            model_name=query_embedding_result.model_name or "",
        )

    return RetrievalSearchResponse(
        candidates=candidates,
        requested_filters=requested_filter,
        effective_filters=effective_filter,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        provider_name=query_embedding_result.provider_name,
        model_name=query_embedding_result.model_name,
    )


def search_chunk_vectors_in_db(
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
        return search_chunk_vectors(
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


def _count_matching_embeddings(
    connection: sqlite3.Connection,
    *,
    provider_key: str,
    model_name: str,
) -> int:
    return connection.execute(
        """
        SELECT COUNT(*)
        FROM chunk_embedding
        WHERE provider_key = ? AND model_name = ?;
        """,
        (provider_key, model_name),
    ).fetchone()[0]


def _query_vector_candidates(
    connection: sqlite3.Connection,
    *,
    query_embedding: list[float],
    limit: int,
    metadata_filter: RetrievalMetadataFilter,
    provider_key: str,
    model_name: str,
) -> list[RetrievedChunkCandidate]:
    query_norm = _vector_norm(query_embedding)
    if query_norm <= 0:
        return []

    filter_clauses, filter_params = _build_filter_sql(metadata_filter)
    where_clauses = [
        "chunk_embedding.provider_key = ?",
        "chunk_embedding.model_name = ?",
    ]
    where_clauses.extend(filter_clauses)
    params: list[object] = [provider_key, model_name, *filter_params]

    rows = connection.execute(
        f"""
        SELECT
            chunk_embedding.embedding_json AS embedding_json,
            chunk_embedding.vector_norm AS vector_norm,
            chunk.chunk_id AS chunk_id,
            chunk.note_id AS note_id,
            note.path AS path,
            note.title AS title,
            note.note_type AS note_type,
            note.template_family AS template_family,
            note.daily_note_date AS daily_note_date,
            note.source_mtime_ns AS source_mtime_ns,
            chunk.heading_path AS heading_path,
            chunk.start_line AS start_line,
            chunk.end_line AS end_line,
            chunk.text AS text
        FROM chunk_embedding
        INNER JOIN chunk ON chunk.chunk_id = chunk_embedding.chunk_id
        INNER JOIN note ON note.note_id = chunk.note_id
        WHERE {' AND '.join(where_clauses)};
        """,
        params,
    ).fetchall()

    candidates: list[RetrievedChunkCandidate] = []
    for row in rows:
        candidate_embedding = _parse_embedding(row["embedding_json"])
        if len(candidate_embedding) != len(query_embedding):
            continue

        candidate_norm = float(row["vector_norm"] or 0.0)
        if candidate_norm <= 0:
            continue

        score = _cosine_similarity(
            query_embedding=query_embedding,
            query_norm=query_norm,
            candidate_embedding=candidate_embedding,
            candidate_norm=candidate_norm,
        )
        if score <= 0:
            continue

        text = row["text"]
        candidates.append(
            RetrievedChunkCandidate(
                retrieval_source="sqlite_vector",
                chunk_id=row["chunk_id"],
                note_id=row["note_id"],
                path=row["path"],
                title=row["title"],
                heading_path=row["heading_path"],
                note_type=row["note_type"],
                template_family=row["template_family"],
                daily_note_date=row["daily_note_date"],
                source_mtime_ns=row["source_mtime_ns"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                score=score,
                snippet=_build_snippet(text),
                text=text,
            )
        )

    candidates.sort(
        key=lambda candidate: (
            -candidate.score,
            candidate.path,
            candidate.start_line,
        )
    )
    return candidates[:limit]


def _parse_embedding(raw_embedding_json: str) -> list[float]:
    try:
        raw_values = json.loads(raw_embedding_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(raw_values, list):
        return []

    normalized_values: list[float] = []
    for raw_value in raw_values:
        if not isinstance(raw_value, (int, float)):
            return []
        normalized_values.append(float(raw_value))
    return normalized_values


def _cosine_similarity(
    *,
    query_embedding: list[float],
    query_norm: float,
    candidate_embedding: list[float],
    candidate_norm: float,
) -> float:
    if query_norm <= 0 or candidate_norm <= 0:
        return 0.0
    dot_product = sum(
        query_value * candidate_value
        for query_value, candidate_value in zip(query_embedding, candidate_embedding, strict=True)
    )
    return dot_product / (query_norm * candidate_norm)


def _vector_norm(values: list[float]) -> float:
    return sum(value * value for value in values) ** 0.5


def _build_snippet(text: str) -> str:
    collapsed_text = " ".join(text.split())
    if len(collapsed_text) <= VECTOR_SNIPPET_MAX_CHARS:
        return collapsed_text
    return f"{collapsed_text[: VECTOR_SNIPPET_MAX_CHARS - 3].rstrip()}..."


def _build_arg_parser(default_db_path: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search the Knowledge Steward SQLite vector index and return top-k chunk candidates."
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=default_db_path,
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Query text used to build the search embedding.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of chunk candidates to return.",
    )
    parser.add_argument(
        "--provider-preference",
        default=None,
        help="Optional provider preference, for example cloud or local.",
    )
    parser.add_argument(
        "--path-prefix",
        action="append",
        default=[],
        help="Literal note path prefix filter. Can be passed multiple times.",
    )
    parser.add_argument(
        "--note-type",
        action="append",
        default=[],
        help="Metadata note_type filter. Can be passed multiple times.",
    )
    parser.add_argument(
        "--template-family",
        action="append",
        default=[],
        help="Metadata template_family filter. Can be passed multiple times.",
    )
    return parser


def main() -> None:
    settings = get_settings()
    parser = _build_arg_parser(settings.index_db_path)
    args = parser.parse_args()
    metadata_filter = RetrievalMetadataFilter(
        path_prefixes=args.path_prefix,
        note_types=args.note_type,
        template_families=args.template_family,
    )
    results = search_chunk_vectors_in_db(
        args.db_path,
        args.query,
        settings=settings,
        limit=args.limit,
        metadata_filter=metadata_filter,
        provider_preference=args.provider_preference,
    )

    if results.disabled:
        print(f"Vector search disabled: {results.disabled_reason}")
        return

    if not results.candidates:
        print("No chunk candidates matched the vector query.")
        return

    if results.fallback_used:
        print(f"Fallback used: {results.fallback_reason}")

    for index, result in enumerate(results.candidates, start=1):
        print(
            f"[{index}] score={result.score:.4f} "
            f"note_type={result.note_type} "
            f"path={result.path} "
            f"chunk_id={result.chunk_id}"
        )
        print(f"    snippet={result.snippet}")


if __name__ == "__main__":
    main()
