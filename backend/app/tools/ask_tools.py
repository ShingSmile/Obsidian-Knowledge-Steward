from __future__ import annotations

import re
from pathlib import Path

from app.config import Settings
from app.contracts.workflow import ToolExecutionResult
from app.indexing.store import connect_sqlite, initialize_index_db, list_pending_approval_records
from app.indexing.parser import parse_markdown_note
from app.retrieval.hybrid import search_hybrid_chunks_in_db
from app.tools.backlinks import collect_verified_backlinks


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


def execute_get_note_outline(
    arguments: dict[str, object],
    *,
    settings: Settings,
) -> ToolExecutionResult:
    note_path_arg = arguments.get("note_path")
    if not isinstance(note_path_arg, str) or not note_path_arg.strip():
        return ToolExecutionResult(
            tool_name="get_note_outline",
            ok=False,
            error="invalid_arguments",
            diagnostics={"failure_code": "invalid_arguments"},
            allow_context_reentry=False,
        )

    resolved_note = _resolve_note_path(settings.sample_vault_dir, note_path_arg.strip())
    if resolved_note is None:
        return ToolExecutionResult(
            tool_name="get_note_outline",
            ok=False,
            error="note_path_outside_vault",
            diagnostics={"failure_code": "note_path_outside_vault"},
            allow_context_reentry=False,
        )
    if not resolved_note.exists() or not resolved_note.is_file():
        return ToolExecutionResult(
            tool_name="get_note_outline",
            ok=False,
            error="note_not_found",
            diagnostics={"failure_code": "note_not_found"},
            allow_context_reentry=False,
        )

    try:
        parsed_note = parse_markdown_note(resolved_note)
        raw_text = resolved_note.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ToolExecutionResult(
            tool_name="get_note_outline",
            ok=False,
            error="read_error",
            diagnostics={"failure_code": "read_error"},
            allow_context_reentry=False,
        )

    return ToolExecutionResult(
        tool_name="get_note_outline",
        ok=True,
        data={
            "note_path": note_path_arg.strip(),
            "title": parsed_note.title,
            "has_frontmatter": parsed_note.has_frontmatter,
            "frontmatter_summary": _summarize_frontmatter(raw_text),
            "headings": [heading.model_dump(mode="json") for heading in parsed_note.headings],
        },
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


def execute_find_backlinks(
    arguments: dict[str, object],
    *,
    settings: Settings,
) -> ToolExecutionResult:
    note_path_arg = arguments.get("note_path")
    if not isinstance(note_path_arg, str) or not note_path_arg.strip():
        return ToolExecutionResult(
            tool_name="find_backlinks",
            ok=False,
            error="invalid_arguments",
            diagnostics={"failure_code": "invalid_arguments"},
            allow_context_reentry=False,
        )

    resolved_note = _resolve_note_path(settings.sample_vault_dir, note_path_arg.strip())
    if resolved_note is None:
        return ToolExecutionResult(
            tool_name="find_backlinks",
            ok=False,
            error="note_path_outside_vault",
            diagnostics={"failure_code": "index_stale"},
            allow_context_reentry=False,
        )
    if not resolved_note.exists() or not resolved_note.is_file():
        return ToolExecutionResult(
            tool_name="find_backlinks",
            ok=False,
            error="index_stale",
            diagnostics={"failure_code": "index_stale", "target_missing": True},
            allow_context_reentry=False,
        )

    db_path = initialize_index_db(settings.index_db_path)
    connection = connect_sqlite(db_path)
    try:
        backlinks, diagnostics = collect_verified_backlinks(
            connection,
            vault_root=settings.sample_vault_dir,
            target_path=resolved_note,
        )
    finally:
        connection.close()

    if diagnostics.get("failure_code") == "index_stale":
        return ToolExecutionResult(
            tool_name="find_backlinks",
            ok=False,
            data={},
            error="index_stale",
            diagnostics=diagnostics,
            allow_context_reentry=False,
        )

    return ToolExecutionResult(
        tool_name="find_backlinks",
        ok=True,
        data={
            "target_path": str(resolved_note),
            "backlinks": [
                {
                    "source_path": backlink.source_path,
                    "chunk_id": backlink.chunk_id,
                    "heading_path": backlink.heading_path,
                    "start_line": backlink.start_line,
                    "end_line": backlink.end_line,
                    "link_text": backlink.link_text,
                }
                for backlink in backlinks
            ],
        },
        diagnostics=diagnostics,
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


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


def _summarize_frontmatter(text: str) -> dict[str, object]:
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return {}

    summary: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            items = summary.get(current_key)
            if not isinstance(items, list):
                items = [] if items is None else [items]
                summary[current_key] = items
            items.append(_coerce_frontmatter_scalar(line[4:].strip()))
            continue
        if ":" not in line:
            current_key = None
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            current_key = None
            continue
        if value:
            summary[key] = _coerce_frontmatter_scalar(value)
            current_key = None
        else:
            summary[key] = []
            current_key = key
    return summary


def _coerce_frontmatter_scalar(value: str) -> object:
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.isdigit():
        return int(value)
    return value
