from __future__ import annotations

import argparse
from pathlib import Path
import re
import sqlite3

from app.config import Settings, get_settings
from app.contracts.workflow import (
    RetrievalMetadataFilter,
    RetrievalSearchResponse,
    RetrievedChunkCandidate,
)
from app.indexing.store import connect_sqlite, initialize_index_db, rebuild_chunk_fts_index
from app.path_semantics import PathContractError, normalize_path_separators, normalize_to_vault_relative


QUERY_TERM_RE = re.compile(r"[0-9A-Za-z_\u4e00-\u9fff]+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
VERSION_RE = re.compile(r"[Vv]\d+(?:\.\d+)+")
CJK_ONLY_RE = re.compile(r"[\u4e00-\u9fff]+")

MAX_CJK_SUBTERM_LENGTH = 6
MIN_CJK_SUBTERM_LENGTH = 3
MAX_CJK_SUBTERMS = 2

# 兼容 TASK-006 阶段已有命名，避免后续接 TASK-007 时把调用面完全推翻。
ChunkSearchHit = RetrievedChunkCandidate


def _normalize_query(
    connection: sqlite3.Connection,
    raw_query: str,
) -> str | None:
    stripped_query = _strip_query_hints(raw_query)
    terms = QUERY_TERM_RE.findall(stripped_query.strip())
    if not terms:
        if _extract_query_hints(raw_query):
            return None
        terms = QUERY_TERM_RE.findall(raw_query.strip())
    if not terms:
        raise ValueError("Search query must contain at least one searchable term.")

    expanded_terms: list[str] = []
    for term in terms:
        expanded_terms.extend(_expand_query_term(connection, term))

    deduplicated_terms: list[str] = []
    seen: set[str] = set()
    for term in expanded_terms:
        lowered = term.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduplicated_terms.append(term)

    # 这里显式把任意输入降到“词项 AND 匹配”，是为了先兜住符号噪声和 FTS 语法错误，
    # 避免用户输入 `Roadmap!!!`、`(plan)` 之类内容时直接把 MATCH 语法打崩。
    escaped_terms = [term.replace('"', '""') for term in deduplicated_terms]
    return " ".join(f'"{term}"' for term in escaped_terms)


def _extract_query_hints(raw_query: str) -> list[str]:
    return _deduplicate_terms(
        DATE_RE.findall(raw_query) + VERSION_RE.findall(raw_query),
        casefold=True,
    )


def _strip_query_hints(raw_query: str) -> str:
    stripped_query = DATE_RE.sub(" ", raw_query)
    stripped_query = VERSION_RE.sub(" ", stripped_query)
    return stripped_query


def _expand_query_term(
    connection: sqlite3.Connection,
    term: str,
) -> list[str]:
    if not CJK_ONLY_RE.fullmatch(term):
        return [term]
    if len(term) <= MAX_CJK_SUBTERM_LENGTH:
        return [term]

    matched_subterms = _select_matching_cjk_subterms(connection, term)
    return matched_subterms or [term]


def _select_matching_cjk_subterms(
    connection: sqlite3.Connection,
    term: str,
) -> list[str]:
    selected_subterms = _select_matching_cjk_subterms_with_min_length(
        connection,
        term,
        min_length=MIN_CJK_SUBTERM_LENGTH,
    )
    if selected_subterms:
        return selected_subterms
    return _select_matching_cjk_subterms_with_min_length(
        connection,
        term,
        min_length=2,
    )


def _select_matching_cjk_subterms_with_min_length(
    connection: sqlite3.Connection,
    term: str,
    *,
    min_length: int,
) -> list[str]:
    candidate_ranges: list[tuple[int, int, str]] = []
    max_length = min(MAX_CJK_SUBTERM_LENGTH, len(term))
    for length in range(max_length, min_length - 1, -1):
        for start in range(0, len(term) - length + 1):
            subterm = term[start : start + length]
            if not _cjk_subterm_matches(connection, subterm):
                continue
            candidate_ranges.append((start, start + length, subterm))

    if not candidate_ranges:
        return []

    selected: list[tuple[int, int, str]] = []
    for start, end, subterm in candidate_ranges:
        if any(not (end <= selected_start or start >= selected_end) for selected_start, selected_end, _ in selected):
            continue
        selected.append((start, end, subterm))
        if len(selected) >= MAX_CJK_SUBTERMS:
            break

    return [subterm for _, _, subterm in selected]


def _cjk_subterm_matches(
    connection: sqlite3.Connection,
    subterm: str,
) -> bool:
    quoted_subterm = f'"{subterm.replace(chr(34), chr(34) * 2)}"'
    row = connection.execute(
        """
        SELECT 1
        FROM chunk_fts
        WHERE chunk_fts MATCH ?
        LIMIT 1;
        """,
        (quoted_subterm,),
    ).fetchone()
    return row is not None


def _deduplicate_terms(values: list[str], *, casefold: bool = False) -> list[str]:
    deduplicated: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        normalized = cleaned.casefold() if casefold else cleaned
        if normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(normalized if casefold else cleaned)
    return deduplicated


def _normalize_metadata_filter(
    metadata_filter: RetrievalMetadataFilter | None,
    *,
    vault_root: Path | None = None,
) -> RetrievalMetadataFilter:
    if metadata_filter is None:
        return RetrievalMetadataFilter()

    min_source_mtime_ns = metadata_filter.min_source_mtime_ns
    max_source_mtime_ns = metadata_filter.max_source_mtime_ns
    if (
        min_source_mtime_ns is not None
        and max_source_mtime_ns is not None
        and min_source_mtime_ns > max_source_mtime_ns
    ):
        raise ValueError("min_source_mtime_ns must be less than or equal to max_source_mtime_ns.")

    daily_note_date_from = (metadata_filter.daily_note_date_from or "").strip() or None
    daily_note_date_to = (metadata_filter.daily_note_date_to or "").strip() or None
    for field_name, field_value in (
        ("daily_note_date_from", daily_note_date_from),
        ("daily_note_date_to", daily_note_date_to),
    ):
        if field_value is not None and not DATE_RE.fullmatch(field_value):
            raise ValueError(f"{field_name} must use YYYY-MM-DD format.")
    if (
        daily_note_date_from is not None
        and daily_note_date_to is not None
        and daily_note_date_from > daily_note_date_to
    ):
        raise ValueError("daily_note_date_from must be less than or equal to daily_note_date_to.")

    return RetrievalMetadataFilter(
        path_prefixes=_normalize_path_prefixes(
            metadata_filter.path_prefixes,
            vault_root=vault_root,
        ),
        note_types=_deduplicate_terms(metadata_filter.note_types, casefold=True),
        template_families=_deduplicate_terms(
            metadata_filter.template_families,
            casefold=True,
        ),
        min_source_mtime_ns=min_source_mtime_ns,
        max_source_mtime_ns=max_source_mtime_ns,
        daily_note_date_from=daily_note_date_from,
        daily_note_date_to=daily_note_date_to,
    )


def _normalize_path_prefixes(
    values: list[str],
    *,
    vault_root: Path | None,
) -> list[str]:
    if vault_root is None:
        return _deduplicate_terms(values)

    normalized_prefixes: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue

        normalized_value = normalize_path_separators(cleaned)
        has_trailing_separator = normalized_value.endswith("/")
        prefix_body = normalized_value.rstrip("/")
        if not prefix_body:
            continue
        try:
            canonical_prefix = normalize_to_vault_relative(
                prefix_body,
                vault_root=vault_root,
            )
        except PathContractError as exc:
            raise ValueError("path_prefixes must stay within the configured vault.") from exc

        if has_trailing_separator:
            canonical_prefix = f"{canonical_prefix}/"
        if canonical_prefix in seen:
            continue
        seen.add(canonical_prefix)
        normalized_prefixes.append(canonical_prefix)

    return normalized_prefixes


def _ensure_chunk_fts_ready(connection: sqlite3.Connection) -> None:
    chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
    if chunk_count == 0:
        return

    fts_count = connection.execute("SELECT COUNT(*) FROM chunk_fts;").fetchone()[0]
    if fts_count == 0:
        rebuild_chunk_fts_index(connection)


def _escape_like_prefix(prefix: str) -> str:
    return prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _escape_like_contains(value: str) -> str:
    return _escape_like_prefix(value)


def _build_filter_sql(
    metadata_filter: RetrievalMetadataFilter,
) -> tuple[list[str], list[object]]:
    clauses: list[str] = []
    params: list[object] = []

    if metadata_filter.path_prefixes:
        path_clauses: list[str] = []
        for prefix in metadata_filter.path_prefixes:
            # 这里把 path filter 固定成“字面量前缀匹配”，而不是开放 LIKE 通配符，
            # 是为了避免路径里恰好包含 `%` / `_` 时把过滤语义意外放大。
            path_clauses.append("note.path LIKE ? ESCAPE '\\'")
            params.append(f"{_escape_like_prefix(prefix)}%")
        clauses.append(f"({' OR '.join(path_clauses)})")

    if metadata_filter.note_types:
        placeholders = ", ".join("?" for _ in metadata_filter.note_types)
        clauses.append(f"note.note_type IN ({placeholders})")
        params.extend(metadata_filter.note_types)

    if metadata_filter.template_families:
        placeholders = ", ".join("?" for _ in metadata_filter.template_families)
        clauses.append(f"note.template_family IN ({placeholders})")
        params.extend(metadata_filter.template_families)

    if metadata_filter.min_source_mtime_ns is not None:
        clauses.append("note.source_mtime_ns >= ?")
        params.append(metadata_filter.min_source_mtime_ns)

    if metadata_filter.max_source_mtime_ns is not None:
        clauses.append("note.source_mtime_ns <= ?")
        params.append(metadata_filter.max_source_mtime_ns)

    if metadata_filter.daily_note_date_from is not None:
        clauses.append("note.daily_note_date IS NOT NULL AND note.daily_note_date >= ?")
        params.append(metadata_filter.daily_note_date_from)

    if metadata_filter.daily_note_date_to is not None:
        clauses.append("note.daily_note_date IS NOT NULL AND note.daily_note_date <= ?")
        params.append(metadata_filter.daily_note_date_to)

    return clauses, params


def _query_candidates(
    connection: sqlite3.Connection,
    normalized_query: str | None,
    *,
    limit: int,
    metadata_filter: RetrievalMetadataFilter,
    query_hints: list[str],
) -> list[RetrievedChunkCandidate]:
    rows: list[sqlite3.Row] = []
    if normalized_query is not None:
        filter_clauses, filter_params = _build_filter_sql(metadata_filter)
        where_clauses = ["chunk_fts MATCH ?"]
        where_clauses.extend(filter_clauses)
        params: list[object] = [normalized_query, *filter_params, limit]

        rows = connection.execute(
            f"""
            SELECT
                chunk_fts.chunk_id AS chunk_id,
                chunk_fts.note_id AS note_id,
                note.path AS path,
                note.title AS title,
                note.note_type AS note_type,
                note.template_family AS template_family,
                note.daily_note_date AS daily_note_date,
                note.source_mtime_ns AS source_mtime_ns,
                chunk.heading_path AS heading_path,
                chunk.start_line AS start_line,
                chunk.end_line AS end_line,
                chunk.text AS text,
                -bm25(chunk_fts) AS score,
                snippet(chunk_fts, -1, '[', ']', '...', 12) AS snippet
            FROM chunk_fts
            INNER JOIN chunk ON chunk.chunk_id = chunk_fts.chunk_id
            INNER JOIN note ON note.note_id = chunk.note_id
            WHERE {' AND '.join(where_clauses)}
            ORDER BY score DESC, note.path ASC, chunk.start_line ASC
            LIMIT ?;
            """,
            params,
        ).fetchall()

    if query_hints:
        rows = _merge_candidate_rows(
            base_rows=rows,
            supplemental_rows=_query_hint_rows(
                connection,
                normalized_query,
                metadata_filter=metadata_filter,
                query_hints=query_hints,
            ),
        )

    candidates = [
        RetrievedChunkCandidate(
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
            score=row["score"] + _compute_hint_boost(row, query_hints),
            snippet=row["snippet"],
            text=row["text"],
        )
        for row in rows
    ]
    candidates.sort(
        key=lambda candidate: (
            -candidate.score,
            candidate.path,
            candidate.start_line,
        )
    )
    return candidates[:limit]


def _query_hint_rows(
    connection: sqlite3.Connection,
    normalized_query: str | None,
    *,
    metadata_filter: RetrievalMetadataFilter,
    query_hints: list[str],
) -> list[sqlite3.Row]:
    filter_clauses, filter_params = _build_filter_sql(metadata_filter)
    hint_clauses, hint_params = _build_hint_sql(query_hints)
    if not hint_clauses:
        return []

    where_clauses = list(filter_clauses)
    where_clauses.append(f"({' OR '.join(hint_clauses)})")
    params: list[object] = [*filter_params, *hint_params]

    score_sql = "0.0 AS score"
    snippet_sql = "substr(chunk.text, 1, 240) AS snippet"
    from_sql = """
        FROM chunk
        INNER JOIN note ON note.note_id = chunk.note_id
    """

    if normalized_query is not None:
        where_clauses.insert(0, "chunk_fts MATCH ?")
        params.insert(0, normalized_query)
        score_sql = "-bm25(chunk_fts) AS score"
        snippet_sql = "snippet(chunk_fts, -1, '[', ']', '...', 12) AS snippet"
        from_sql = """
        FROM chunk_fts
        INNER JOIN chunk ON chunk.chunk_id = chunk_fts.chunk_id
        INNER JOIN note ON note.note_id = chunk.note_id
        """

    return connection.execute(
        f"""
        SELECT
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
            chunk.text AS text,
            {score_sql},
            {snippet_sql}
        {from_sql}
        WHERE {' AND '.join(where_clauses)}
        ORDER BY score DESC, note.path ASC, chunk.start_line ASC;
        """,
        params,
    ).fetchall()


def _build_hint_sql(query_hints: list[str]) -> tuple[list[str], list[object]]:
    clauses: list[str] = []
    params: list[object] = []
    for hint in query_hints:
        normalized_hint = hint.casefold()
        like_param = f"%{_escape_like_contains(normalized_hint)}%"
        clauses.append(
            "("
            "lower(note.path) LIKE ? ESCAPE '\\' OR "
            "lower(note.title) LIKE ? ESCAPE '\\' OR "
            "lower(COALESCE(chunk.heading_path, '')) LIKE ? ESCAPE '\\' OR "
            "lower(chunk.text) LIKE ? ESCAPE '\\'"
            ")"
        )
        params.extend([like_param, like_param, like_param, like_param])
    return clauses, params


def _merge_candidate_rows(
    *,
    base_rows: list[sqlite3.Row],
    supplemental_rows: list[sqlite3.Row],
) -> list[sqlite3.Row]:
    merged_rows: dict[int, sqlite3.Row] = {}
    for row in base_rows:
        merged_rows[row["chunk_id"]] = row
    for row in supplemental_rows:
        merged_rows[row["chunk_id"]] = row
    return list(merged_rows.values())


def _compute_hint_boost(
    row: sqlite3.Row,
    query_hints: list[str],
) -> float:
    if not query_hints:
        return 0.0

    path = str(row["path"] or "").casefold()
    title = str(row["title"] or "").casefold()
    heading_path = str(row["heading_path"] or "").casefold()
    text = str(row["text"] or "").casefold()

    boost = 0.0
    for hint in query_hints:
        if _hint_matches_value(path, hint):
            boost += 100.0
        elif _hint_matches_value(title, hint):
            boost += 80.0
        elif _hint_matches_value(heading_path, hint):
            boost += 40.0
        elif _hint_matches_value(text, hint):
            boost += 20.0
    return boost


def _hint_matches_value(value: str, hint: str) -> bool:
    if not value or not hint:
        return False

    search_start = 0
    while True:
        match_index = value.find(hint, search_start)
        if match_index < 0:
            return False
        if _is_valid_hint_boundary(value, hint, match_index):
            return True
        search_start = match_index + 1


def _is_valid_hint_boundary(
    value: str,
    hint: str,
    match_index: int,
) -> bool:
    before = value[match_index - 1] if match_index > 0 else ""
    after_index = match_index + len(hint)
    after = value[after_index] if after_index < len(value) else ""

    if VERSION_RE.fullmatch(hint):
        invalid_neighbors = set("0123456789abcdefghijklmnopqrstuvwxyz.")
    elif DATE_RE.fullmatch(hint):
        invalid_neighbors = set("0123456789abcdefghijklmnopqrstuvwxyz")
    else:
        invalid_neighbors = set("0123456789abcdefghijklmnopqrstuvwxyz")

    return before not in invalid_neighbors and after not in invalid_neighbors


def search_chunks(
    connection: sqlite3.Connection,
    query: str,
    *,
    limit: int = 5,
    metadata_filter: RetrievalMetadataFilter | None = None,
    allow_filter_fallback: bool = True,
    vault_root: Path | None = None,
) -> RetrievalSearchResponse:
    if limit <= 0:
        raise ValueError("Search limit must be greater than 0.")

    _ensure_chunk_fts_ready(connection)
    query_hints = _extract_query_hints(query)
    normalized_query = _normalize_query(connection, query)
    requested_filter = _normalize_metadata_filter(
        metadata_filter,
        vault_root=vault_root,
    )
    candidates = _query_candidates(
        connection,
        normalized_query,
        limit=limit,
        metadata_filter=requested_filter,
        query_hints=query_hints,
    )

    fallback_used = False
    fallback_reason: str | None = None
    effective_filter = requested_filter
    if not candidates and allow_filter_fallback and not requested_filter.is_empty():
        # 这里显式退回“仅 query 的 FTS 检索”，是为了避免上游 ask 链路在 filter 过严时
        # 直接卡成空结果；首版先保证可恢复，再把更细粒度的放宽策略留到后续任务。
        fallback_used = True
        fallback_reason = "metadata_filters_too_strict"
        effective_filter = RetrievalMetadataFilter()
        candidates = _query_candidates(
            connection,
            normalized_query,
            limit=limit,
            metadata_filter=effective_filter,
            query_hints=query_hints,
        )

    return RetrievalSearchResponse(
        candidates=candidates,
        requested_filters=requested_filter,
        effective_filters=effective_filter,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
    )


def search_chunks_in_db(
    db_path: Path,
    query: str,
    *,
    settings: Settings | None = None,
    limit: int = 5,
    metadata_filter: RetrievalMetadataFilter | None = None,
    allow_filter_fallback: bool = True,
) -> RetrievalSearchResponse:
    runtime_settings = settings or get_settings()
    initialized_db_path = initialize_index_db(
        db_path,
        settings=runtime_settings,
    )
    connection = connect_sqlite(initialized_db_path)
    try:
        return search_chunks(
            connection,
            query,
            limit=limit,
            metadata_filter=metadata_filter,
            allow_filter_fallback=allow_filter_fallback,
            vault_root=runtime_settings.sample_vault_dir,
        )
    finally:
        connection.close()


def _build_arg_parser(default_db_path: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search the Knowledge Steward SQLite FTS index and return top-k chunk candidates."
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
        help="Search query used for SQLite FTS5 matching.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of chunk candidates to return.",
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
    results = search_chunks_in_db(
        args.db_path,
        args.query,
        limit=args.limit,
        metadata_filter=metadata_filter,
    )

    if not results.candidates:
        print("No chunk candidates matched the query.")
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
