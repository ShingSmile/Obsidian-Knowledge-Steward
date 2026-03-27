from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3


@dataclass(frozen=True)
class BacklinkRecord:
    source_path: str
    chunk_id: str
    heading_path: str | None
    start_line: int
    end_line: int
    link_text: str


def build_target_match_keys(
    connection: sqlite3.Connection,
    *,
    vault_root: Path,
    target_path: Path,
) -> set[str]:
    resolved_root = vault_root.expanduser().resolve()
    resolved_target = target_path.expanduser().resolve()
    target_keys: set[str] = set()

    try:
        target_keys.add(resolved_target.relative_to(resolved_root).with_suffix("").as_posix())
    except ValueError:
        pass

    if _is_unique_stem(connection, resolved_target.stem):
        target_keys.add(resolved_target.stem)

    return target_keys


def collect_verified_backlinks(
    connection: sqlite3.Connection,
    *,
    vault_root: Path,
    target_path: Path,
) -> tuple[list[BacklinkRecord], dict[str, object]]:
    resolved_target = target_path.expanduser().resolve()
    target_row = _load_note_row(connection, resolved_target)
    if target_row is None:
        return [], {"failure_code": "index_stale", "target_missing": True}
    if not _is_fresh(resolved_target, int(target_row["source_mtime_ns"])):
        return [], {"failure_code": "index_stale", "target_stale": True}

    target_keys = build_target_match_keys(
        connection,
        vault_root=vault_root,
        target_path=resolved_target,
    )
    if not target_keys:
        return [], {"failure_code": "index_stale", "target_ambiguous": True}

    candidate_rows = _load_candidate_rows(connection, target_keys)
    verified: list[BacklinkRecord] = []
    stale_candidate_count = 0

    for row in candidate_rows:
        source_path = Path(str(row["source_path"]))
        if not _is_fresh(source_path, int(row["source_mtime_ns"])):
            stale_candidate_count += 1
            continue
        verified.append(
            BacklinkRecord(
                source_path=str(source_path),
                chunk_id=str(row["chunk_id"]),
                heading_path=row["heading_path"],
                start_line=int(row["start_line"]),
                end_line=int(row["end_line"]),
                link_text=str(row["link_text"]),
            )
        )

    if stale_candidate_count:
        return [], {
            "failure_code": "index_stale",
            "stale_candidate_count": stale_candidate_count,
            "candidate_count": len(candidate_rows),
        }

    return verified, {
        "candidate_count": len(candidate_rows),
        "verified_candidate_count": len(verified),
    }


def normalize_wikilink_target(raw_link_text: str) -> str:
    cleaned = raw_link_text.strip()
    if "|" in cleaned:
        cleaned = cleaned.split("|", 1)[0].strip()
    if "#" in cleaned:
        cleaned = cleaned.split("#", 1)[0].strip()
    cleaned = cleaned.replace("\\", "/")
    if cleaned.casefold().endswith(".md"):
        cleaned = cleaned[:-3]

    parts: list[str] = []
    for part in cleaned.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def _load_note_row(
    connection: sqlite3.Connection,
    resolved_target: Path,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            path,
            source_mtime_ns,
            title
        FROM note
        WHERE path = ?
        LIMIT 1;
        """,
        (str(resolved_target),),
    ).fetchone()


def _load_candidate_rows(
    connection: sqlite3.Connection,
    target_keys: set[str],
) -> list[sqlite3.Row]:
    rows = connection.execute(
        """
        SELECT
            note.path AS source_path,
            note.source_mtime_ns AS source_mtime_ns,
            chunk.chunk_id AS chunk_id,
            chunk.heading_path AS heading_path,
            chunk.start_line AS start_line,
            chunk.end_line AS end_line,
            chunk.out_links_json AS out_links_json
        FROM chunk
        INNER JOIN note ON note.note_id = chunk.note_id
        WHERE chunk.out_links_json != '[]'
        ORDER BY note.path ASC, chunk.start_line ASC, chunk.end_line ASC, chunk.chunk_id ASC;
        """
    ).fetchall()

    matches: list[sqlite3.Row] = []
    for row in rows:
        try:
            raw_links = json.loads(row["out_links_json"])
        except json.JSONDecodeError:
            continue
        if not isinstance(raw_links, list):
            continue
        for raw_link in raw_links:
            if not isinstance(raw_link, str):
                continue
            normalized_link = normalize_wikilink_target(raw_link)
            if normalized_link and normalized_link in target_keys:
                matches.append(
                    {
                        "source_path": row["source_path"],
                        "source_mtime_ns": row["source_mtime_ns"],
                        "chunk_id": row["chunk_id"],
                        "heading_path": row["heading_path"],
                        "start_line": row["start_line"],
                        "end_line": row["end_line"],
                        "link_text": normalized_link,
                    }
                )
                break
    return matches


def _is_unique_stem(connection: sqlite3.Connection, stem: str) -> bool:
    if not stem:
        return False
    count = 0
    for row in connection.execute("SELECT path FROM note;").fetchall():
        note_path = Path(str(row["path"]))
        if note_path.stem == stem:
            count += 1
            if count > 1:
                return False
    return count == 1


def _is_fresh(candidate_path: Path, source_mtime_ns: int) -> bool:
    try:
        stat_result = candidate_path.stat()
    except OSError:
        return False
    return stat_result.st_mtime_ns == source_mtime_ns
