from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.contracts.workflow import ToolExecutionResult
from app.indexing.store import connect_sqlite, initialize_index_db, list_pending_approval_records
from app.retrieval.hybrid import search_hybrid_chunks_in_db


def execute_search_notes(
    arguments: dict[str, object],
    *,
    settings: Settings,
) -> ToolExecutionResult:
    query = arguments.get("query")
    if not isinstance(query, str) or not query.strip():
        return ToolExecutionResult(
            tool_name="search_notes",
            ok=False,
            error="invalid_arguments",
        )

    limit = _coerce_positive_int(arguments.get("limit"), default=5, maximum=20)
    response = search_hybrid_chunks_in_db(
        settings.index_db_path,
        query.strip(),
        settings=settings,
        limit=limit,
    )
    results = [
        {
            "path": candidate.path,
            "chunk_id": candidate.chunk_id,
            "heading_path": candidate.heading_path,
            "text": candidate.snippet,
            "score": candidate.score,
        }
        for candidate in response.candidates
    ]
    return ToolExecutionResult(
        tool_name="search_notes",
        ok=True,
        data={"results": results},
        allow_context_reentry=False,
    )


def execute_load_note_excerpt(
    arguments: dict[str, object],
    *,
    settings: Settings,
) -> ToolExecutionResult:
    note_path_arg = arguments.get("note_path")
    if not isinstance(note_path_arg, str) or not note_path_arg.strip():
        return ToolExecutionResult(
            tool_name="load_note_excerpt",
            ok=False,
            error="invalid_arguments",
        )

    max_chars = _coerce_positive_int(arguments.get("max_chars"), default=600, maximum=4000)
    resolved_note = _resolve_note_path(settings.sample_vault_dir, note_path_arg.strip())
    if resolved_note is None:
        return ToolExecutionResult(
            tool_name="load_note_excerpt",
            ok=False,
            error="note_path_outside_vault",
        )
    if not resolved_note.exists() or not resolved_note.is_file():
        return ToolExecutionResult(
            tool_name="load_note_excerpt",
            ok=False,
            error="note_not_found",
        )

    content = resolved_note.read_text(encoding="utf-8")
    return ToolExecutionResult(
        tool_name="load_note_excerpt",
        ok=True,
        data={
            "note_path": note_path_arg.strip(),
            "excerpt": content[:max_chars],
            "line_count": content.count("\n") + (1 if content else 0),
        },
    )


def execute_list_pending_approvals(
    arguments: dict[str, object],
    *,
    settings: Settings,
) -> ToolExecutionResult:
    _ = arguments
    db_path = initialize_index_db(settings.index_db_path)
    connection = connect_sqlite(db_path)
    try:
        pending_records = list_pending_approval_records(connection)
    finally:
        connection.close()

    items = [
        {
            "thread_id": record.thread_id,
            "graph_name": record.graph_name,
            "proposal_id": record.persisted_proposal.proposal.proposal_id,
            "action_type": record.persisted_proposal.proposal.action_type.value,
            "summary": record.persisted_proposal.proposal.summary,
            "target_note_path": record.persisted_proposal.proposal.target_note_path,
            "risk_level": record.persisted_proposal.proposal.risk_level.value,
            "checkpoint_updated_at": record.checkpoint_updated_at,
        }
        for record in pending_records
    ]
    return ToolExecutionResult(
        tool_name="list_pending_approvals",
        ok=True,
        data={"items": items},
        allow_context_reentry=False,
    )


def _coerce_positive_int(value: object, *, default: int, maximum: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return max(1, min(value, maximum))
    return default


def _resolve_note_path(vault_root: Path, note_path: str) -> Path | None:
    resolved_root = vault_root.expanduser().resolve()
    resolved_note = (resolved_root / note_path).resolve()
    if not resolved_note.is_relative_to(resolved_root):
        return None
    return resolved_note
