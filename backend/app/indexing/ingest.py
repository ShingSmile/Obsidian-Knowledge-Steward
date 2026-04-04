from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from pathlib import Path
import sqlite3
from typing import Sequence

from app.config import Settings, get_settings
from app.indexing.parser import parse_markdown_note
from app.indexing.store import (
    ChunkRecord,
    build_chunk_embedding_records,
    build_chunk_records,
    build_note_record,
    connect_sqlite,
    initialize_index_db,
    rebuild_chunk_fts_index,
    sync_note_and_chunks,
    upsert_chunk_embeddings,
)
from app.path_semantics import PathContractError, normalize_to_vault_relative, resolve_vault_relative
from app.retrieval.embeddings import (
    EmbeddingProviderTarget,
    embed_texts,
    resolve_embedding_provider_targets,
)


@dataclass(frozen=True)
class IngestRunStats:
    vault_path: str
    db_path: str
    scanned_notes: int
    created_notes: int
    updated_notes: int
    current_chunk_count: int
    replaced_chunk_count: int


def _normalize_vault_path(vault_path: Path) -> Path:
    normalized_vault_path = vault_path.expanduser().resolve()
    if not normalized_vault_path.exists():
        raise FileNotFoundError(f"Vault path does not exist: {normalized_vault_path}")
    if not normalized_vault_path.is_dir():
        raise NotADirectoryError(f"Vault path is not a directory: {normalized_vault_path}")
    return normalized_vault_path


def list_markdown_notes(vault_path: Path) -> list[Path]:
    normalized_vault_path = _normalize_vault_path(vault_path)

    # 这里显式排序，是为了保证 ingest 顺序稳定，避免测试和审计统计随着文件系统遍历顺序漂移。
    return sorted(normalized_vault_path.rglob("*.md"))


def resolve_requested_markdown_notes(
    vault_path: Path,
    *,
    note_path: str | Path | None = None,
    note_paths: Sequence[str | Path] = (),
) -> list[Path]:
    normalized_vault_path = _normalize_vault_path(vault_path)
    requested_note_paths: list[str | Path] = []
    if note_path is not None:
        requested_note_paths.append(note_path)
    requested_note_paths.extend(note_paths)

    if not requested_note_paths:
        return list_markdown_notes(normalized_vault_path)

    resolved_notes: dict[str, Path] = {}
    for requested_note_path in requested_note_paths:
        resolved_note = _resolve_requested_note_path(
            normalized_vault_path,
            requested_note_path,
        )
        resolved_notes[str(resolved_note)] = resolved_note

    # 这里按规范化绝对路径排序，是为了让 scoped ingest 在重复请求、不同入参顺序下
    # 仍保持稳定的执行顺序和统计结果，便于 trace、checkpoint 与测试对齐。
    return sorted(resolved_notes.values(), key=lambda note: str(note))


def ingest_vault(
    vault_path: Path,
    db_path: Path,
    *,
    note_path: str | Path | None = None,
    note_paths: Sequence[str | Path] = (),
    settings: Settings | None = None,
) -> IngestRunStats:
    normalized_vault_path = _normalize_vault_path(vault_path)
    markdown_notes = resolve_requested_markdown_notes(
        normalized_vault_path,
        note_path=note_path,
        note_paths=note_paths,
    )
    runtime_settings = settings or get_settings()
    embedding_provider_targets = resolve_embedding_provider_targets(settings=runtime_settings)
    initialized_db_path = initialize_index_db(
        db_path,
        settings=replace(runtime_settings, sample_vault_dir=normalized_vault_path),
    )
    connection = connect_sqlite(initialized_db_path)

    created_notes = 0
    updated_notes = 0
    current_chunk_count = 0
    replaced_chunk_count = 0
    embedding_sync_disabled_reason = (
        "no_available_embedding_provider" if not embedding_provider_targets else None
    )

    try:
        for note_path in markdown_notes:
            parsed_note = parse_markdown_note(note_path)
            note_record = build_note_record(
                note_path,
                parsed_note,
                vault_root=normalized_vault_path,
            )
            chunk_records = build_chunk_records(note_record.note_id, parsed_note)
            sync_result = sync_note_and_chunks(
                connection=connection,
                note_record=note_record,
                chunk_records=chunk_records,
            )
            if sync_result.note_created:
                created_notes += 1
            else:
                updated_notes += 1
            current_chunk_count += sync_result.current_chunk_count
            replaced_chunk_count += sync_result.replaced_chunk_count

            if embedding_sync_disabled_reason is None and chunk_records:
                disabled_reason = _sync_chunk_embeddings_for_note(
                    connection=connection,
                    chunk_records=chunk_records,
                    settings=runtime_settings,
                    provider_targets=embedding_provider_targets,
                )
                if disabled_reason is not None:
                    # 这里一旦确认 embedding provider 已不可用，就停止本轮后续 note 的重试。
                    # 原因不是假装“向量同步成功”，而是避免整库 ingest 在已知 provider 故障时
                    # 对每篇笔记重复发起失败请求，把一次降级放大成整轮长时间阻塞。
                    embedding_sync_disabled_reason = disabled_reason

        # 即使当前是 scoped ingest，这里也仍然统一重建整张 FTS。
        # 这是有意保持“写库完成”和“检索可用”只有一个一致性边界，
        # 先避免局部更新把 FTS 漂移问题偷偷引进来；更细粒度同步留给后续 small。
        rebuild_chunk_fts_index(connection)
    finally:
        connection.close()

    return IngestRunStats(
        vault_path=str(normalized_vault_path),
        db_path=str(initialized_db_path),
        scanned_notes=len(markdown_notes),
        created_notes=created_notes,
        updated_notes=updated_notes,
        current_chunk_count=current_chunk_count,
        replaced_chunk_count=replaced_chunk_count,
    )


def _sync_chunk_embeddings_for_note(
    *,
    connection: sqlite3.Connection,
    chunk_records: list[ChunkRecord],
    settings: Settings,
    provider_targets: Sequence[EmbeddingProviderTarget],
) -> str | None:
    embedding_result = embed_texts(
        [chunk_record.text for chunk_record in chunk_records],
        settings=settings,
        provider_targets=provider_targets,
    )
    if embedding_result.disabled:
        return embedding_result.disabled_reason

    # 这里把 embedding 写入放在 note/chunk 已成功落库之后，是为了把“内容事实”
    # 和“向量侧可选增强”分成主从关系：provider 不可用时只降级向量链路，不回滚主索引。
    chunk_embedding_records = build_chunk_embedding_records(
        chunk_records,
        embeddings=embedding_result.embeddings,
        provider_key=embedding_result.provider_key or "",
        provider_name=embedding_result.provider_name or "",
        model_name=embedding_result.model_name or "",
    )
    upsert_chunk_embeddings(connection, chunk_embedding_records)
    return None


def _resolve_requested_note_path(vault_path: Path, requested_note_path: str | Path) -> Path:
    raw_note_path = str(requested_note_path).strip()
    if not raw_note_path:
        raise ValueError("Scoped ingest note paths must be non-empty strings.")

    try:
        normalized_note_path = normalize_to_vault_relative(
            raw_note_path,
            vault_root=vault_path,
        )
        normalized_candidate_path = resolve_vault_relative(
            normalized_note_path,
            vault_root=vault_path,
        )
    except PathContractError as exc:
        raise ValueError(
            "Scoped ingest note paths must stay within the configured vault."
        ) from exc

    if not normalized_candidate_path.exists():
        raise ValueError(
            f"Scoped ingest note path does not exist: {normalized_candidate_path}"
        )
    if not normalized_candidate_path.is_file():
        raise ValueError(
            f"Scoped ingest note path is not a file: {normalized_candidate_path}"
        )
    if normalized_candidate_path.suffix.lower() != ".md":
        raise ValueError(
            "Scoped ingest only supports Markdown files ending with .md."
        )

    return normalized_candidate_path


def _build_arg_parser(default_vault_path: Path, default_db_path: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse Markdown notes from a vault and sync them into the Knowledge Steward SQLite index."
    )
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=default_vault_path,
        help="Vault directory that contains Markdown notes.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=default_db_path,
        help="Path to the SQLite database file.",
    )
    return parser


def main() -> None:
    settings = get_settings()
    parser = _build_arg_parser(settings.sample_vault_dir, settings.index_db_path)
    args = parser.parse_args()
    stats = ingest_vault(vault_path=args.vault_path, db_path=args.db_path)
    print(
        "Ingest completed: "
        f"{stats.scanned_notes} notes scanned, "
        f"{stats.created_notes} created, "
        f"{stats.updated_notes} updated, "
        f"{stats.current_chunk_count} current chunks written, "
        f"{stats.replaced_chunk_count} old chunks replaced, "
        f"db={stats.db_path}"
    )


if __name__ == "__main__":
    main()
