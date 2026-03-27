from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sqlite3
from typing import Any

from app.config import get_settings
from app.contracts.workflow import (
    ApprovalDecision,
    AuditEvent,
    PatchOp,
    Proposal,
    ProposalEvidence,
    SafetyChecks,
)
from app.indexing.models import ParsedNote
from app.services.proposal_validation import validate_proposal_for_persistence


SCHEMA_VERSION = 7

CHUNK_FTS_POPULATE_SQL = """
INSERT INTO chunk_fts (
    chunk_id,
    note_id,
    path,
    title,
    heading_path,
    text
)
SELECT
    chunk.chunk_id,
    chunk.note_id,
    note.path,
    note.title,
    COALESCE(chunk.heading_path, ''),
    chunk.text
FROM chunk
INNER JOIN note ON note.note_id = chunk.note_id
ORDER BY note.path ASC, chunk.ordinal ASC;
"""


def _sha1_hexdigest(content: str) -> str:
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


def normalize_note_path(note_path: Path) -> str:
    return str(note_path.expanduser().resolve())


@dataclass(frozen=True)
class NoteRecord:
    note_id: str
    path: str
    title: str
    note_type: str
    template_family: str
    daily_note_date: str | None
    content_hash: str
    source_ctime_ns: int | None
    source_mtime_ns: int
    source_size_bytes: int
    has_frontmatter: bool
    task_count: int
    tags: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    out_links: tuple[str, ...] = ()

    def as_db_params(self) -> dict[str, object]:
        return {
            "note_id": self.note_id,
            "path": self.path,
            "title": self.title,
            "note_type": self.note_type,
            "template_family": self.template_family,
            "daily_note_date": self.daily_note_date,
            "content_hash": self.content_hash,
            "source_ctime_ns": self.source_ctime_ns,
            "source_mtime_ns": self.source_mtime_ns,
            "source_size_bytes": self.source_size_bytes,
            "has_frontmatter": int(self.has_frontmatter),
            "task_count": self.task_count,
            # 这里先用 JSON 文本保存可选 metadata，避免在 schema 任务里提前扩成多张关联表。
            "tags_json": json.dumps(list(self.tags), ensure_ascii=False),
            "aliases_json": json.dumps(list(self.aliases), ensure_ascii=False),
            "out_links_json": json.dumps(list(self.out_links), ensure_ascii=False),
        }


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    note_id: str
    ordinal: int
    chunk_type: str
    heading_path: str | None
    parent_chunk_id: str | None
    block_id: str | None
    start_line: int
    end_line: int
    text: str
    content_hash: str
    task_count: int
    out_links: tuple[str, ...] = ()

    def as_db_params(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "note_id": self.note_id,
            "ordinal": self.ordinal,
            "chunk_type": self.chunk_type,
            "heading_path": self.heading_path,
            "parent_chunk_id": self.parent_chunk_id,
            "block_id": self.block_id,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
            "content_hash": self.content_hash,
            "task_count": self.task_count,
            "out_links_json": json.dumps(list(self.out_links), ensure_ascii=False),
        }


@dataclass(frozen=True)
class ChunkEmbeddingRecord:
    chunk_id: str
    note_id: str
    provider_key: str
    provider_name: str
    model_name: str
    embedding: tuple[float, ...]
    embedding_dim: int
    vector_norm: float
    content_hash: str

    def as_db_params(self) -> dict[str, object]:
        return {
            "chunk_id": self.chunk_id,
            "note_id": self.note_id,
            "provider_key": self.provider_key,
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "vector_norm": self.vector_norm,
            "embedding_json": json.dumps(list(self.embedding), ensure_ascii=False),
            "content_hash": self.content_hash,
        }


@dataclass(frozen=True)
class NoteSyncResult:
    note_id: str
    note_created: bool
    replaced_chunk_count: int
    current_chunk_count: int


@dataclass(frozen=True)
class PersistedProposal:
    thread_id: str
    proposal: Proposal
    approval_required: bool
    run_id: str | None = None
    idempotency_key: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class PendingApprovalRecord:
    thread_id: str
    graph_name: str
    checkpoint_updated_at: str
    persisted_proposal: PersistedProposal


MIGRATIONS: dict[int, str] = {
    1: """
    CREATE TABLE IF NOT EXISTS note (
        note_id TEXT PRIMARY KEY,
        path TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        note_type TEXT NOT NULL,
        template_family TEXT NOT NULL,
        daily_note_date TEXT,
        content_hash TEXT NOT NULL,
        source_ctime_ns INTEGER,
        source_mtime_ns INTEGER NOT NULL,
        source_size_bytes INTEGER NOT NULL,
        has_frontmatter INTEGER NOT NULL DEFAULT 0 CHECK (has_frontmatter IN (0, 1)),
        task_count INTEGER NOT NULL DEFAULT 0 CHECK (task_count >= 0),
        tags_json TEXT NOT NULL DEFAULT '[]',
        aliases_json TEXT NOT NULL DEFAULT '[]',
        out_links_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (length(path) > 0),
        CHECK (length(title) > 0),
        CHECK (length(content_hash) > 0),
        CHECK (source_size_bytes >= 0)
    );

    CREATE TABLE IF NOT EXISTS chunk (
        chunk_id TEXT PRIMARY KEY,
        note_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL,
        chunk_type TEXT NOT NULL,
        heading_path TEXT,
        parent_chunk_id TEXT,
        block_id TEXT,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        text TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        task_count INTEGER NOT NULL DEFAULT 0 CHECK (task_count >= 0),
        out_links_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (note_id) REFERENCES note(note_id) ON DELETE CASCADE,
        FOREIGN KEY (parent_chunk_id) REFERENCES chunk(chunk_id) ON DELETE SET NULL,
        UNIQUE (note_id, ordinal),
        CHECK (ordinal >= 0),
        CHECK (length(chunk_type) > 0),
        CHECK (start_line > 0),
        CHECK (end_line >= start_line),
        CHECK (length(text) > 0),
        CHECK (length(content_hash) > 0)
    );

    CREATE INDEX IF NOT EXISTS idx_note_content_hash ON note(content_hash);
    CREATE INDEX IF NOT EXISTS idx_note_note_type ON note(note_type);
    CREATE INDEX IF NOT EXISTS idx_note_daily_note_date ON note(daily_note_date);
    CREATE INDEX IF NOT EXISTS idx_note_source_mtime_ns ON note(source_mtime_ns);
    CREATE INDEX IF NOT EXISTS idx_chunk_note_id_chunk_type ON chunk(note_id, chunk_type);
    CREATE INDEX IF NOT EXISTS idx_chunk_heading_path ON chunk(heading_path);
    CREATE INDEX IF NOT EXISTS idx_chunk_parent_chunk_id ON chunk(parent_chunk_id);
    CREATE INDEX IF NOT EXISTS idx_chunk_content_hash ON chunk(content_hash);
    """,
    2: f"""
    -- 这里把 note 标题、heading_path 和 chunk 正文拍平成单独 FTS 文档，
    -- 是为了先用一张虚表覆盖“标题 + 正文”的最小全文召回，而不把 query 逻辑耦进多表 JOIN。
    CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
        chunk_id UNINDEXED,
        note_id UNINDEXED,
        path UNINDEXED,
        title,
        heading_path,
        text,
        tokenize = 'unicode61'
    );

    {CHUNK_FTS_POPULATE_SQL}
    """,
    3: """
    CREATE TABLE IF NOT EXISTS run_trace (
        trace_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL,
        thread_id TEXT NOT NULL,
        graph_name TEXT NOT NULL,
        node_name TEXT NOT NULL,
        event_type TEXT NOT NULL,
        action_type TEXT NOT NULL,
        event_timestamp TEXT NOT NULL,
        details_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (length(trace_id) > 0),
        CHECK (length(run_id) > 0),
        CHECK (length(thread_id) > 0),
        CHECK (length(graph_name) > 0),
        CHECK (length(node_name) > 0),
        CHECK (length(event_type) > 0),
        CHECK (length(action_type) > 0),
        CHECK (length(event_timestamp) > 0)
    );

    CREATE INDEX IF NOT EXISTS idx_run_trace_run_id
        ON run_trace(run_id, event_timestamp);
    CREATE INDEX IF NOT EXISTS idx_run_trace_thread_id
        ON run_trace(thread_id, event_timestamp);
    CREATE INDEX IF NOT EXISTS idx_run_trace_graph_name
        ON run_trace(graph_name, event_timestamp);
    """,
    4: """
    CREATE TABLE IF NOT EXISTS workflow_checkpoint (
        checkpoint_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        graph_name TEXT NOT NULL,
        action_type TEXT NOT NULL,
        last_run_id TEXT NOT NULL,
        checkpoint_status TEXT NOT NULL,
        last_completed_node TEXT,
        next_node_name TEXT,
        state_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (thread_id, graph_name),
        CHECK (length(checkpoint_id) > 0),
        CHECK (length(thread_id) > 0),
        CHECK (length(graph_name) > 0),
        CHECK (length(action_type) > 0),
        CHECK (length(last_run_id) > 0),
        CHECK (checkpoint_status IN ('in_progress', 'completed', 'failed')),
        CHECK (length(state_json) > 0)
    );

    CREATE INDEX IF NOT EXISTS idx_workflow_checkpoint_thread_graph
        ON workflow_checkpoint(thread_id, graph_name);
    CREATE INDEX IF NOT EXISTS idx_workflow_checkpoint_status
        ON workflow_checkpoint(checkpoint_status, updated_at);
    """,
    5: """
    CREATE TABLE IF NOT EXISTS proposal (
        proposal_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        run_id TEXT,
        action_type TEXT NOT NULL,
        target_note_path TEXT NOT NULL,
        summary TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        approval_required INTEGER NOT NULL DEFAULT 1 CHECK (approval_required IN (0, 1)),
        idempotency_key TEXT,
        before_hash TEXT,
        max_changed_lines INTEGER NOT NULL DEFAULT 0 CHECK (max_changed_lines >= 0),
        contains_delete INTEGER NOT NULL DEFAULT 0 CHECK (contains_delete IN (0, 1)),
        safety_checks_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (length(proposal_id) > 0),
        CHECK (length(thread_id) > 0),
        CHECK (run_id IS NULL OR length(run_id) > 0),
        CHECK (length(action_type) > 0),
        CHECK (length(target_note_path) > 0),
        CHECK (length(summary) > 0),
        CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
        CHECK (idempotency_key IS NULL OR length(idempotency_key) > 0),
        CHECK (length(safety_checks_json) > 0)
    );

    CREATE TABLE IF NOT EXISTS proposal_evidence (
        evidence_id TEXT PRIMARY KEY,
        proposal_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
        source_path TEXT NOT NULL,
        heading_path TEXT,
        chunk_id TEXT,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (proposal_id) REFERENCES proposal(proposal_id) ON DELETE CASCADE,
        UNIQUE (proposal_id, ordinal),
        CHECK (length(evidence_id) > 0),
        CHECK (length(source_path) > 0),
        CHECK (length(reason) > 0)
    );

    CREATE TABLE IF NOT EXISTS patch_op (
        patch_op_id TEXT PRIMARY KEY,
        proposal_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
        op TEXT NOT NULL,
        target_path TEXT NOT NULL,
        payload_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (proposal_id) REFERENCES proposal(proposal_id) ON DELETE CASCADE,
        UNIQUE (proposal_id, ordinal),
        CHECK (length(patch_op_id) > 0),
        CHECK (length(op) > 0),
        CHECK (length(target_path) > 0),
        CHECK (length(payload_json) > 0)
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        audit_event_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        run_id TEXT,
        proposal_id TEXT,
        action_type TEXT NOT NULL,
        target_note_path TEXT,
        approval_required INTEGER NOT NULL DEFAULT 0 CHECK (approval_required IN (0, 1)),
        approval_status TEXT CHECK (
            approval_status IS NULL
            OR approval_status IN ('approved', 'rejected', 'edited')
        ),
        reviewer TEXT,
        approval_comment TEXT,
        approval_decided_at TEXT,
        before_hash TEXT,
        after_hash TEXT,
        writeback_applied INTEGER NOT NULL DEFAULT 0 CHECK (writeback_applied IN (0, 1)),
        error TEXT,
        retrieved_chunk_ids_json TEXT NOT NULL DEFAULT '[]',
        model_info_json TEXT NOT NULL DEFAULT '{}',
        approval_payload_json TEXT NOT NULL DEFAULT '{}',
        writeback_result_json TEXT NOT NULL DEFAULT '{}',
        applied_patch_ops_json TEXT NOT NULL DEFAULT '[]',
        latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (proposal_id) REFERENCES proposal(proposal_id) ON DELETE SET NULL,
        CHECK (length(audit_event_id) > 0),
        CHECK (length(thread_id) > 0),
        CHECK (run_id IS NULL OR length(run_id) > 0),
        CHECK (proposal_id IS NULL OR length(proposal_id) > 0),
        CHECK (length(action_type) > 0),
        CHECK (length(retrieved_chunk_ids_json) > 0),
        CHECK (length(model_info_json) > 0),
        CHECK (length(approval_payload_json) > 0),
        CHECK (length(writeback_result_json) > 0),
        CHECK (length(applied_patch_ops_json) > 0)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_proposal_idempotency_key
        ON proposal(idempotency_key)
        WHERE idempotency_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_proposal_thread_id
        ON proposal(thread_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_proposal_run_id
        ON proposal(run_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_proposal_target_note_path
        ON proposal(target_note_path);
    CREATE INDEX IF NOT EXISTS idx_proposal_evidence_proposal_id
        ON proposal_evidence(proposal_id, ordinal);
    CREATE INDEX IF NOT EXISTS idx_proposal_evidence_chunk_id
        ON proposal_evidence(chunk_id);
    CREATE INDEX IF NOT EXISTS idx_patch_op_proposal_id
        ON patch_op(proposal_id, ordinal);
    CREATE INDEX IF NOT EXISTS idx_patch_op_target_path
        ON patch_op(target_path);
    CREATE INDEX IF NOT EXISTS idx_audit_log_thread_id
        ON audit_log(thread_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_audit_log_run_id
        ON audit_log(run_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_audit_log_proposal_id
        ON audit_log(proposal_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_audit_log_writeback_applied
        ON audit_log(writeback_applied, created_at);
    """,
    6: """
    ALTER TABLE workflow_checkpoint RENAME TO workflow_checkpoint_legacy_v5;

    CREATE TABLE workflow_checkpoint (
        checkpoint_id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        graph_name TEXT NOT NULL,
        action_type TEXT NOT NULL,
        last_run_id TEXT NOT NULL,
        checkpoint_status TEXT NOT NULL,
        last_completed_node TEXT,
        next_node_name TEXT,
        state_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (thread_id, graph_name),
        CHECK (length(checkpoint_id) > 0),
        CHECK (length(thread_id) > 0),
        CHECK (length(graph_name) > 0),
        CHECK (length(action_type) > 0),
        CHECK (length(last_run_id) > 0),
        CHECK (
            checkpoint_status IN (
                'in_progress',
                'waiting_for_approval',
                'completed',
                'failed'
            )
        ),
        CHECK (length(state_json) > 0)
    );

    INSERT INTO workflow_checkpoint (
        checkpoint_id,
        thread_id,
        graph_name,
        action_type,
        last_run_id,
        checkpoint_status,
        last_completed_node,
        next_node_name,
        state_json,
        created_at,
        updated_at
    )
    SELECT
        checkpoint_id,
        thread_id,
        graph_name,
        action_type,
        last_run_id,
        checkpoint_status,
        last_completed_node,
        next_node_name,
        state_json,
        created_at,
        updated_at
    FROM workflow_checkpoint_legacy_v5;

    DROP TABLE workflow_checkpoint_legacy_v5;

    CREATE INDEX IF NOT EXISTS idx_workflow_checkpoint_thread_graph
        ON workflow_checkpoint(thread_id, graph_name);
    CREATE INDEX IF NOT EXISTS idx_workflow_checkpoint_status
        ON workflow_checkpoint(checkpoint_status, updated_at);
    """,
    7: """
    CREATE TABLE IF NOT EXISTS chunk_embedding (
        chunk_id TEXT PRIMARY KEY,
        note_id TEXT NOT NULL,
        provider_key TEXT NOT NULL,
        provider_name TEXT NOT NULL,
        model_name TEXT NOT NULL,
        embedding_dim INTEGER NOT NULL CHECK (embedding_dim > 0),
        vector_norm REAL NOT NULL CHECK (vector_norm >= 0),
        embedding_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chunk_id) REFERENCES chunk(chunk_id) ON DELETE CASCADE,
        FOREIGN KEY (note_id) REFERENCES note(note_id) ON DELETE CASCADE,
        CHECK (length(provider_key) > 0),
        CHECK (length(provider_name) > 0),
        CHECK (length(model_name) > 0),
        CHECK (length(embedding_json) > 0),
        CHECK (length(content_hash) > 0)
    );

    CREATE INDEX IF NOT EXISTS idx_chunk_embedding_provider_model
        ON chunk_embedding(provider_key, model_name);
    CREATE INDEX IF NOT EXISTS idx_chunk_embedding_note_id
        ON chunk_embedding(note_id);
    """,
}


def connect_sqlite(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_index_db(db_path: Path) -> Path:
    normalized_path = db_path.expanduser().resolve()
    connection = connect_sqlite(normalized_path)
    try:
        _apply_migrations(connection)
    finally:
        connection.close()
    return normalized_path


def _apply_migrations(connection: sqlite3.Connection) -> None:
    current_version = connection.execute("PRAGMA user_version;").fetchone()[0]
    if current_version > SCHEMA_VERSION:
        raise RuntimeError(
            f"SQLite schema version {current_version} is newer than supported version {SCHEMA_VERSION}."
        )

    for target_version in range(current_version + 1, SCHEMA_VERSION + 1):
        migration_sql = MIGRATIONS[target_version]
        # 这里只用 SQLite 自带的 user_version 做版本推进，先把迁移机制压到最小，
        # 避免在 schema 任务里提前引入额外的 migration framework。
        connection.executescript(migration_sql)
        connection.execute(f"PRAGMA user_version = {target_version};")
        connection.commit()


def _chunk_fts_exists(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = 'chunk_fts';
        """
    ).fetchone()
    return row is not None


def build_note_record(note_path: Path, parsed_note: ParsedNote) -> NoteRecord:
    normalized_path = normalize_note_path(note_path)
    raw_text = note_path.read_text(encoding="utf-8")
    stat = note_path.stat()
    note_id = f"note_{_sha1_hexdigest(normalized_path)[:16]}"

    return NoteRecord(
        note_id=note_id,
        path=normalized_path,
        title=parsed_note.title,
        note_type=parsed_note.note_type,
        template_family=parsed_note.template_family,
        daily_note_date=parsed_note.daily_note_date,
        content_hash=_sha1_hexdigest(raw_text),
        source_ctime_ns=getattr(stat, "st_ctime_ns", None),
        source_mtime_ns=stat.st_mtime_ns,
        source_size_bytes=stat.st_size,
        has_frontmatter=parsed_note.has_frontmatter,
        task_count=parsed_note.task_count,
        out_links=tuple(parsed_note.wikilinks),
    )


def build_chunk_records(note_id: str, parsed_note: ParsedNote) -> list[ChunkRecord]:
    records: list[ChunkRecord] = []
    for ordinal, chunk in enumerate(parsed_note.chunks):
        records.append(
            ChunkRecord(
                chunk_id=chunk.chunk_id,
                note_id=note_id,
                ordinal=ordinal,
                chunk_type=chunk.chunk_type,
                heading_path=chunk.heading_path,
                parent_chunk_id=None,
                block_id=None,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                text=chunk.text,
                content_hash=_sha1_hexdigest(chunk.text),
                task_count=chunk.task_count,
                out_links=tuple(chunk.wikilinks),
            )
        )
    return records


def build_chunk_embedding_records(
    chunk_records: list[ChunkRecord],
    *,
    embeddings: list[list[float]],
    provider_key: str,
    provider_name: str,
    model_name: str,
) -> list[ChunkEmbeddingRecord]:
    if len(chunk_records) != len(embeddings):
        raise ValueError("Chunk embedding count must match chunk record count.")

    records: list[ChunkEmbeddingRecord] = []
    for chunk_record, raw_embedding in zip(chunk_records, embeddings, strict=True):
        normalized_embedding = tuple(float(value) for value in raw_embedding)
        if not normalized_embedding:
            raise ValueError(f"Chunk {chunk_record.chunk_id} produced an empty embedding.")
        records.append(
            ChunkEmbeddingRecord(
                chunk_id=chunk_record.chunk_id,
                note_id=chunk_record.note_id,
                provider_key=provider_key,
                provider_name=provider_name,
                model_name=model_name,
                embedding=normalized_embedding,
                embedding_dim=len(normalized_embedding),
                vector_norm=_vector_norm(normalized_embedding),
                content_hash=chunk_record.content_hash,
            )
        )
    return records


def upsert_note(connection: sqlite3.Connection, note_record: NoteRecord) -> None:
    connection.execute(
        """
        INSERT INTO note (
            note_id,
            path,
            title,
            note_type,
            template_family,
            daily_note_date,
            content_hash,
            source_ctime_ns,
            source_mtime_ns,
            source_size_bytes,
            has_frontmatter,
            task_count,
            tags_json,
            aliases_json,
            out_links_json
        )
        VALUES (
            :note_id,
            :path,
            :title,
            :note_type,
            :template_family,
            :daily_note_date,
            :content_hash,
            :source_ctime_ns,
            :source_mtime_ns,
            :source_size_bytes,
            :has_frontmatter,
            :task_count,
            :tags_json,
            :aliases_json,
            :out_links_json
        )
        ON CONFLICT(note_id) DO UPDATE SET
            path = excluded.path,
            title = excluded.title,
            note_type = excluded.note_type,
            template_family = excluded.template_family,
            daily_note_date = excluded.daily_note_date,
            content_hash = excluded.content_hash,
            source_ctime_ns = excluded.source_ctime_ns,
            source_mtime_ns = excluded.source_mtime_ns,
            source_size_bytes = excluded.source_size_bytes,
            has_frontmatter = excluded.has_frontmatter,
            task_count = excluded.task_count,
            tags_json = excluded.tags_json,
            aliases_json = excluded.aliases_json,
            out_links_json = excluded.out_links_json,
            updated_at = CURRENT_TIMESTAMP;
        """,
        note_record.as_db_params(),
    )


def replace_chunks_for_note(
    connection: sqlite3.Connection,
    note_id: str,
    chunk_records: list[ChunkRecord],
) -> int:
    for chunk_record in chunk_records:
        if chunk_record.note_id != note_id:
            raise ValueError(
                f"Chunk {chunk_record.chunk_id} does not belong to note {note_id}."
            )

    existing_chunk_count = connection.execute(
        "SELECT COUNT(*) FROM chunk WHERE note_id = ?;",
        (note_id,),
    ).fetchone()[0]
    connection.execute("DELETE FROM chunk WHERE note_id = ?;", (note_id,))

    if chunk_records:
        connection.executemany(
            """
            INSERT INTO chunk (
                chunk_id,
                note_id,
                ordinal,
                chunk_type,
                heading_path,
                parent_chunk_id,
                block_id,
                start_line,
                end_line,
                text,
                content_hash,
                task_count,
                out_links_json
            )
            VALUES (
                :chunk_id,
                :note_id,
                :ordinal,
                :chunk_type,
                :heading_path,
                :parent_chunk_id,
                :block_id,
                :start_line,
                :end_line,
                :text,
                :content_hash,
                :task_count,
                :out_links_json
            );
            """,
            [chunk_record.as_db_params() for chunk_record in chunk_records],
        )

    return existing_chunk_count


def upsert_chunk_embeddings(
    connection: sqlite3.Connection,
    chunk_embedding_records: list[ChunkEmbeddingRecord],
) -> None:
    if not chunk_embedding_records:
        return

    with connection:
        connection.executemany(
            """
            INSERT INTO chunk_embedding (
                chunk_id,
                note_id,
                provider_key,
                provider_name,
                model_name,
                embedding_dim,
                vector_norm,
                embedding_json,
                content_hash
            )
            VALUES (
                :chunk_id,
                :note_id,
                :provider_key,
                :provider_name,
                :model_name,
                :embedding_dim,
                :vector_norm,
                :embedding_json,
                :content_hash
            )
            ON CONFLICT(chunk_id) DO UPDATE SET
                note_id = excluded.note_id,
                provider_key = excluded.provider_key,
                provider_name = excluded.provider_name,
                model_name = excluded.model_name,
                embedding_dim = excluded.embedding_dim,
                vector_norm = excluded.vector_norm,
                embedding_json = excluded.embedding_json,
                content_hash = excluded.content_hash,
                updated_at = CURRENT_TIMESTAMP;
            """,
            [chunk_embedding_record.as_db_params() for chunk_embedding_record in chunk_embedding_records],
        )


def sync_note_and_chunks(
    connection: sqlite3.Connection,
    note_record: NoteRecord,
    chunk_records: list[ChunkRecord],
) -> NoteSyncResult:
    note_exists = (
        connection.execute(
            "SELECT 1 FROM note WHERE note_id = ?;",
            (note_record.note_id,),
        ).fetchone()
        is not None
    )

    # 这里按单 note 事务做“整 note 替换”，是为了先把幂等边界压清楚：
    # 当标题重排、段落改写或 chunk 数量变化时，旧 chunk 不会残留成脏数据。
    with connection:
        upsert_note(connection, note_record)
        replaced_chunk_count = replace_chunks_for_note(
            connection=connection,
            note_id=note_record.note_id,
            chunk_records=chunk_records,
        )

    return NoteSyncResult(
        note_id=note_record.note_id,
        note_created=not note_exists,
        replaced_chunk_count=replaced_chunk_count,
        current_chunk_count=len(chunk_records),
    )


def rebuild_chunk_fts_index(connection: sqlite3.Connection) -> None:
    if not _chunk_fts_exists(connection):
        raise RuntimeError("chunk_fts is not initialized; run initialize_index_db() first.")

    # 当前 ingest 仍是“全量遍历 + note 级 replace”，因此这里也显式做整库重建。
    # 这样可以避免在 TASK-006 阶段提前引入触发器同步，把漂移恢复路径保持成一个清晰入口。
    with connection:
        connection.execute("DELETE FROM chunk_fts;")
        connection.execute(CHUNK_FTS_POPULATE_SQL)


def save_proposal(
    connection: sqlite3.Connection,
    *,
    thread_id: str,
    proposal: Proposal,
    approval_required: bool,
    run_id: str | None = None,
    idempotency_key: str | None = None,
) -> None:
    with connection:
        save_proposal_record(
            connection,
            thread_id=thread_id,
            proposal=proposal,
            approval_required=approval_required,
            run_id=run_id,
            idempotency_key=idempotency_key,
        )


def save_proposal_record(
    connection: sqlite3.Connection,
    *,
    thread_id: str,
    proposal: Proposal,
    approval_required: bool,
    run_id: str | None = None,
    idempotency_key: str | None = None,
) -> None:
    if not thread_id:
        raise ValueError("thread_id must not be empty when saving a proposal.")

    validate_proposal_for_persistence(
        proposal,
        settings=get_settings(),
    )

    proposal_params = {
        "proposal_id": proposal.proposal_id,
        "thread_id": thread_id,
        "run_id": run_id,
        "action_type": proposal.action_type.value,
        "target_note_path": proposal.target_note_path,
        "summary": proposal.summary,
        "risk_level": proposal.risk_level.value,
        "approval_required": int(approval_required),
        "idempotency_key": idempotency_key,
        "before_hash": proposal.safety_checks.before_hash,
        "max_changed_lines": proposal.safety_checks.max_changed_lines,
        "contains_delete": int(proposal.safety_checks.contains_delete),
        "safety_checks_json": _json_dumps(proposal.safety_checks.model_dump(mode="json")),
    }
    evidence_params = [
        {
            "evidence_id": _build_child_row_id(
                prefix="evid",
                proposal_id=proposal.proposal_id,
                ordinal=ordinal,
            ),
            "proposal_id": proposal.proposal_id,
            "ordinal": ordinal,
            "source_path": evidence.source_path,
            "heading_path": evidence.heading_path,
            "chunk_id": evidence.chunk_id,
            "reason": evidence.reason,
        }
        for ordinal, evidence in enumerate(proposal.evidence)
    ]
    patch_op_params = [
        {
            "patch_op_id": _build_child_row_id(
                prefix="patch",
                proposal_id=proposal.proposal_id,
                ordinal=ordinal,
            ),
            "proposal_id": proposal.proposal_id,
            "ordinal": ordinal,
            "op": patch_op.op,
            "target_path": patch_op.target_path,
            "payload_json": _json_dumps(patch_op.payload),
        }
        for ordinal, patch_op in enumerate(proposal.patch_ops)
    ]

    # proposal 允许在同一个 thread 内被重新生成或重算，因此这里显式做
    # “主表 upsert + 子表整 proposal 替换”，避免旧 evidence / patch op 残留。
    connection.execute(
        """
        INSERT INTO proposal (
            proposal_id,
            thread_id,
            run_id,
            action_type,
            target_note_path,
            summary,
            risk_level,
            approval_required,
            idempotency_key,
            before_hash,
            max_changed_lines,
            contains_delete,
            safety_checks_json
        )
        VALUES (
            :proposal_id,
            :thread_id,
            :run_id,
            :action_type,
            :target_note_path,
            :summary,
            :risk_level,
            :approval_required,
            :idempotency_key,
            :before_hash,
            :max_changed_lines,
            :contains_delete,
            :safety_checks_json
        )
        ON CONFLICT(proposal_id) DO UPDATE SET
            thread_id = excluded.thread_id,
            run_id = excluded.run_id,
            action_type = excluded.action_type,
            target_note_path = excluded.target_note_path,
            summary = excluded.summary,
            risk_level = excluded.risk_level,
            approval_required = excluded.approval_required,
            idempotency_key = excluded.idempotency_key,
            before_hash = excluded.before_hash,
            max_changed_lines = excluded.max_changed_lines,
            contains_delete = excluded.contains_delete,
            safety_checks_json = excluded.safety_checks_json,
            updated_at = CURRENT_TIMESTAMP;
        """,
        proposal_params,
    )
    connection.execute(
        "DELETE FROM proposal_evidence WHERE proposal_id = ?;",
        (proposal.proposal_id,),
    )
    connection.execute(
        "DELETE FROM patch_op WHERE proposal_id = ?;",
        (proposal.proposal_id,),
    )
    if evidence_params:
        connection.executemany(
            """
            INSERT INTO proposal_evidence (
                evidence_id,
                proposal_id,
                ordinal,
                source_path,
                heading_path,
                chunk_id,
                reason
            )
            VALUES (
                :evidence_id,
                :proposal_id,
                :ordinal,
                :source_path,
                :heading_path,
                :chunk_id,
                :reason
            );
            """,
            evidence_params,
        )
    if patch_op_params:
        connection.executemany(
            """
            INSERT INTO patch_op (
                patch_op_id,
                proposal_id,
                ordinal,
                op,
                target_path,
                payload_json
            )
            VALUES (
                :patch_op_id,
                :proposal_id,
                :ordinal,
                :op,
                :target_path,
                :payload_json
            );
            """,
            patch_op_params,
        )


def load_proposal(
    connection: sqlite3.Connection,
    *,
    proposal_id: str,
) -> PersistedProposal | None:
    row = connection.execute(
        """
        SELECT
            proposal_id,
            thread_id,
            run_id,
            action_type,
            target_note_path,
            summary,
            risk_level,
            approval_required,
            idempotency_key,
            before_hash,
            max_changed_lines,
            contains_delete,
            safety_checks_json,
            created_at,
            updated_at
        FROM proposal
        WHERE proposal_id = ?
        LIMIT 1;
        """,
        (proposal_id,),
    ).fetchone()
    if row is None:
        return None

    evidence_rows = connection.execute(
        """
        SELECT
            source_path,
            heading_path,
            chunk_id,
            reason
        FROM proposal_evidence
        WHERE proposal_id = ?
        ORDER BY ordinal ASC;
        """,
        (proposal_id,),
    ).fetchall()
    patch_op_rows = connection.execute(
        """
        SELECT
            op,
            target_path,
            payload_json
        FROM patch_op
        WHERE proposal_id = ?
        ORDER BY ordinal ASC;
        """,
        (proposal_id,),
    ).fetchall()

    proposal = Proposal(
        proposal_id=row["proposal_id"],
        action_type=row["action_type"],
        target_note_path=row["target_note_path"],
        summary=row["summary"],
        risk_level=row["risk_level"],
        evidence=[
            ProposalEvidence(
                source_path=evidence_row["source_path"],
                heading_path=evidence_row["heading_path"],
                chunk_id=evidence_row["chunk_id"],
                reason=evidence_row["reason"],
            )
            for evidence_row in evidence_rows
        ],
        patch_ops=[
            PatchOp(
                op=patch_op_row["op"],
                target_path=patch_op_row["target_path"],
                payload=json.loads(patch_op_row["payload_json"]),
            )
            for patch_op_row in patch_op_rows
        ],
        safety_checks=SafetyChecks.model_validate(json.loads(row["safety_checks_json"])),
    )
    return PersistedProposal(
        thread_id=row["thread_id"],
        run_id=row["run_id"],
        approval_required=bool(row["approval_required"]),
        idempotency_key=row["idempotency_key"],
        proposal=proposal,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_pending_approval_records(
    connection: sqlite3.Connection,
) -> list[PendingApprovalRecord]:
    checkpoint_rows = connection.execute(
        """
        SELECT
            thread_id,
            graph_name,
            state_json,
            updated_at
        FROM workflow_checkpoint
        WHERE checkpoint_status = 'waiting_for_approval'
        ORDER BY updated_at DESC, thread_id ASC, graph_name ASC;
        """
    ).fetchall()

    pending_records: list[PendingApprovalRecord] = []
    for row in checkpoint_rows:
        state_payload = json.loads(row["state_json"])
        proposal_payload = state_payload.get("proposal")
        if not isinstance(proposal_payload, dict):
            continue

        proposal_id = proposal_payload.get("proposal_id")
        if not isinstance(proposal_id, str) or not proposal_id:
            continue

        persisted_proposal = load_proposal(connection, proposal_id=proposal_id)
        if persisted_proposal is None:
            continue
        if persisted_proposal.thread_id != row["thread_id"]:
            continue

        # waiting checkpoint 才代表“这条 proposal 现在仍待审批”，proposal 主表只负责
        # 持久化业务事实。这里显式同时命中 checkpoint 与 proposal，避免把已审批或旧 proposal
        # 误放回收件箱。
        pending_records.append(
            PendingApprovalRecord(
                thread_id=row["thread_id"],
                graph_name=row["graph_name"],
                checkpoint_updated_at=row["updated_at"],
                persisted_proposal=persisted_proposal,
            )
        )

    return pending_records


def append_audit_log_event(
    connection: sqlite3.Connection,
    *,
    audit_event: AuditEvent,
    run_id: str | None = None,
) -> None:
    approval_decision = audit_event.approval_decision
    writeback_result = audit_event.writeback_result
    # audit_log 必须是 append-only，避免恢复或重放时把旧审批结果覆盖掉。
    with connection:
        connection.execute(
            """
            INSERT INTO audit_log (
                audit_event_id,
                thread_id,
                run_id,
                proposal_id,
                action_type,
                target_note_path,
                approval_required,
                approval_status,
                reviewer,
                approval_comment,
                approval_decided_at,
                before_hash,
                after_hash,
                writeback_applied,
                error,
                retrieved_chunk_ids_json,
                model_info_json,
                approval_payload_json,
                writeback_result_json,
                applied_patch_ops_json,
                latency_ms,
                created_at
            )
            VALUES (
                :audit_event_id,
                :thread_id,
                :run_id,
                :proposal_id,
                :action_type,
                :target_note_path,
                :approval_required,
                :approval_status,
                :reviewer,
                :approval_comment,
                :approval_decided_at,
                :before_hash,
                :after_hash,
                :writeback_applied,
                :error,
                :retrieved_chunk_ids_json,
                :model_info_json,
                :approval_payload_json,
                :writeback_result_json,
                :applied_patch_ops_json,
                :latency_ms,
                :created_at
            );
            """,
            {
                "audit_event_id": audit_event.audit_event_id,
                "thread_id": audit_event.thread_id,
                "run_id": run_id,
                "proposal_id": audit_event.proposal_id,
                "action_type": audit_event.action_type.value,
                "target_note_path": audit_event.target_note_path,
                "approval_required": int(audit_event.approval_required),
                "approval_status": _derive_approval_status(approval_decision),
                "reviewer": approval_decision.reviewer if approval_decision else None,
                "approval_comment": approval_decision.comment if approval_decision else None,
                "approval_decided_at": (
                    approval_decision.decided_at.isoformat() if approval_decision else None
                ),
                "before_hash": writeback_result.before_hash if writeback_result else None,
                "after_hash": writeback_result.after_hash if writeback_result else None,
                "writeback_applied": int(writeback_result.applied) if writeback_result else 0,
                "error": writeback_result.error if writeback_result else None,
                "retrieved_chunk_ids_json": _json_dumps(audit_event.retrieved_chunk_ids),
                "model_info_json": _json_dumps(audit_event.model_info),
                "approval_payload_json": _json_dumps(
                    approval_decision.model_dump(mode="json") if approval_decision else {}
                ),
                "writeback_result_json": _json_dumps(
                    writeback_result.model_dump(mode="json") if writeback_result else {}
                ),
                "applied_patch_ops_json": _json_dumps(
                    [
                        patch_op.model_dump(mode="json")
                        for patch_op in (
                            writeback_result.applied_patch_ops if writeback_result else []
                        )
                    ]
                ),
                "latency_ms": audit_event.latency_ms,
                "created_at": audit_event.created_at.isoformat(),
            },
        )


def _derive_approval_status(approval_decision: ApprovalDecision | None) -> str | None:
    if approval_decision is None:
        return None
    # 当前代码事实只支持 approve / reject；schema 仍预留 edited，
    # 是为了不给后续“审批后用户手改 patch 再恢复”再做一次迁移。
    return "approved" if approval_decision.approved else "rejected"


def _build_child_row_id(*, prefix: str, proposal_id: str, ordinal: int) -> str:
    return f"{prefix}_{_sha1_hexdigest(f'{proposal_id}:{ordinal}')[:16]}"


def _vector_norm(values: tuple[float, ...]) -> float:
    return math.sqrt(sum(value * value for value in values))


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _build_arg_parser(default_db_path: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize or migrate the Knowledge Steward SQLite index schema."
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
    parser = _build_arg_parser(settings.index_db_path)
    args = parser.parse_args()
    initialized_path = initialize_index_db(args.db_path)
    print(f"Initialized SQLite index schema at {initialized_path}")


if __name__ == "__main__":
    main()
