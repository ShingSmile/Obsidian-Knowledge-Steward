from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any, cast

from pydantic import BaseModel

from app.contracts.workflow import (
    ApprovalDecision,
    AskWorkflowResult,
    DigestWorkflowResult,
    IngestWorkflowResult,
    PostWritebackSyncResult,
    Proposal,
    RetrievalMetadataFilter,
    WorkflowAction,
    WritebackResult,
)
from app.graphs.state import StewardState
from app.indexing.store import connect_sqlite, initialize_index_db


class WorkflowCheckpointStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PersistedGraphCheckpoint:
    checkpoint_id: str
    thread_id: str
    graph_name: str
    action_type: WorkflowAction
    last_run_id: str
    checkpoint_status: WorkflowCheckpointStatus
    last_completed_node: str | None
    next_node_name: str | None
    state: StewardState
    created_at: str
    updated_at: str


PERSISTED_STATE_FIELDS = {
    "thread_id",
    "run_id",
    "action_type",
    "note_path",
    "note_paths",
    "user_query",
    "provider_preference",
    "retrieval_filter",
    "request_metadata",
    "note_meta",
    "retrieved_chunks",
    "ask_result",
    "ingest_result",
    "digest_result",
    "analysis_issues",
    "proposal",
    "approval_required",
    "approval_decision",
    "patch_plan",
    "before_hash",
    "writeback_result",
    "rollback_result",
    "post_writeback_sync",
    "audit_event_id",
    "rollback_audit_event_id",
    "errors",
}
# 这里只持久化恢复真正需要的结构化状态，避免把 trace、临时 prompt 上下文
# 或大块原文一起塞进 checkpoint，导致恢复语义和观测语义重新耦死。


def save_graph_checkpoint(
    db_path: Path,
    *,
    graph_name: str,
    checkpoint_status: WorkflowCheckpointStatus,
    last_completed_node: str | None,
    next_node_name: str | None,
    state: StewardState,
) -> None:
    normalized_db_path = initialize_index_db(db_path)
    connection = connect_sqlite(normalized_db_path)
    try:
        with connection:
            save_graph_checkpoint_record(
                connection,
                graph_name=graph_name,
                checkpoint_status=checkpoint_status,
                last_completed_node=last_completed_node,
                next_node_name=next_node_name,
                state=state,
            )
    finally:
        connection.close()


def save_graph_checkpoint_record(
    connection: sqlite3.Connection,
    *,
    graph_name: str,
    checkpoint_status: WorkflowCheckpointStatus,
    last_completed_node: str | None,
    next_node_name: str | None,
    state: StewardState,
) -> str:
    serialized_state = serialize_state_for_checkpoint(state)
    checkpoint_id = _build_checkpoint_id(
        thread_id=cast(str, serialized_state["thread_id"]),
        graph_name=graph_name,
    )
    timestamp = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """
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
        VALUES (
            :checkpoint_id,
            :thread_id,
            :graph_name,
            :action_type,
            :last_run_id,
            :checkpoint_status,
            :last_completed_node,
            :next_node_name,
            :state_json,
            :created_at,
            :updated_at
        )
        ON CONFLICT(thread_id, graph_name) DO UPDATE SET
            action_type = excluded.action_type,
            last_run_id = excluded.last_run_id,
            checkpoint_status = excluded.checkpoint_status,
            last_completed_node = excluded.last_completed_node,
            next_node_name = excluded.next_node_name,
            state_json = excluded.state_json,
            updated_at = excluded.updated_at;
        """,
        {
            "checkpoint_id": checkpoint_id,
            "thread_id": serialized_state["thread_id"],
            "graph_name": graph_name,
            "action_type": serialized_state["action_type"],
            "last_run_id": serialized_state["run_id"],
            "checkpoint_status": checkpoint_status.value,
            "last_completed_node": last_completed_node,
            "next_node_name": next_node_name,
            "state_json": json.dumps(
                serialized_state,
                ensure_ascii=False,
                default=_json_default,
                sort_keys=True,
            ),
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )
    return checkpoint_id


def load_graph_checkpoint(
    db_path: Path,
    *,
    thread_id: str,
    graph_name: str,
) -> PersistedGraphCheckpoint | None:
    normalized_db_path = initialize_index_db(db_path)
    connection = connect_sqlite(normalized_db_path)
    try:
        row = connection.execute(
            """
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
            FROM workflow_checkpoint
            WHERE thread_id = ? AND graph_name = ?
            LIMIT 1;
            """,
            (thread_id, graph_name),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return _build_persisted_graph_checkpoint(row)


def list_graph_checkpoints_for_thread(
    db_path: Path,
    *,
    thread_id: str,
) -> list[PersistedGraphCheckpoint]:
    normalized_db_path = initialize_index_db(db_path)
    connection = connect_sqlite(normalized_db_path)
    try:
        rows = connection.execute(
            """
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
            FROM workflow_checkpoint
            WHERE thread_id = ?
            ORDER BY updated_at DESC, graph_name ASC;
            """,
            (thread_id,),
        ).fetchall()
    finally:
        connection.close()

    return [_build_persisted_graph_checkpoint(row) for row in rows]


def serialize_state_for_checkpoint(state: StewardState) -> dict[str, Any]:
    serialized_state: dict[str, Any] = {}
    for field_name in sorted(PERSISTED_STATE_FIELDS):
        if field_name not in state:
            continue
        serialized_state[field_name] = _serialize_value(state[field_name])
    return serialized_state


def deserialize_state_from_checkpoint(payload: dict[str, Any]) -> StewardState:
    state: dict[str, Any] = {}
    for field_name, field_value in payload.items():
        if field_name == "action_type" and field_value is not None:
            state[field_name] = WorkflowAction(field_value)
            continue
        if field_name == "retrieval_filter" and field_value is not None:
            state[field_name] = RetrievalMetadataFilter.model_validate(field_value)
            continue
        if field_name == "ask_result" and field_value is not None:
            state[field_name] = AskWorkflowResult.model_validate(field_value)
            continue
        if field_name == "ingest_result" and field_value is not None:
            state[field_name] = IngestWorkflowResult.model_validate(field_value)
            continue
        if field_name == "digest_result" and field_value is not None:
            state[field_name] = DigestWorkflowResult.model_validate(field_value)
            continue
        if field_name == "proposal" and field_value is not None:
            state[field_name] = Proposal.model_validate(field_value)
            continue
        if field_name == "approval_decision" and field_value is not None:
            state[field_name] = ApprovalDecision.model_validate(field_value)
            continue
        if field_name == "writeback_result" and field_value is not None:
            state[field_name] = WritebackResult.model_validate(field_value)
            continue
        if field_name == "rollback_result" and field_value is not None:
            state[field_name] = WritebackResult.model_validate(field_value)
            continue
        if field_name == "post_writeback_sync" and field_value is not None:
            state[field_name] = PostWritebackSyncResult.model_validate(field_value)
            continue
        state[field_name] = field_value
    return cast(StewardState, state)


def hydrate_business_checkpoint_state(
    *,
    current_state: StewardState,
    restored_state: StewardState,
) -> StewardState:
    hydrated_state = cast(StewardState, dict(restored_state))
    # 恢复的是“业务状态”，不是把上一次 run 原封不动复制回来；
    # 当前 run_id 和本次 trace 必须重新生成，否则一次恢复会和历史执行混成同一轮。
    hydrated_state["thread_id"] = current_state["thread_id"]
    hydrated_state["run_id"] = current_state["run_id"]
    hydrated_state["action_type"] = current_state["action_type"]
    hydrated_state["trace_events"] = []
    hydrated_state["transient_prompt_context"] = {}
    return hydrated_state


def _build_checkpoint_id(*, thread_id: str, graph_name: str) -> str:
    digest = hashlib.sha1(f"{thread_id}:{graph_name}".encode("utf-8")).hexdigest()
    return f"ckpt_{digest[:16]}"


def _build_persisted_graph_checkpoint(row: sqlite3.Row) -> PersistedGraphCheckpoint:
    return PersistedGraphCheckpoint(
        checkpoint_id=row["checkpoint_id"],
        thread_id=row["thread_id"],
        graph_name=row["graph_name"],
        action_type=WorkflowAction(row["action_type"]),
        last_run_id=row["last_run_id"],
        checkpoint_status=WorkflowCheckpointStatus(row["checkpoint_status"]),
        last_completed_node=row["last_completed_node"],
        next_node_name=row["next_node_name"],
        state=deserialize_state_from_checkpoint(json.loads(row["state_json"])),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _serialize_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {
            str(key): _serialize_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    return value


def _json_default(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return repr(value)
