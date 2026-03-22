from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from enum import Enum
import hashlib
import json
from pathlib import Path
import sqlite3

from app.config import get_settings
from app.indexing.store import connect_sqlite, initialize_index_db


RuntimeTracePayload = Mapping[str, object]
TraceHook = Callable[[RuntimeTracePayload], None]


@dataclass(frozen=True)
class PersistedRunTraceEvent:
    trace_id: str
    run_id: str
    thread_id: str
    graph_name: str
    node_name: str
    event_type: str
    action_type: str
    timestamp: str
    details: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "thread_id": self.thread_id,
            "graph_name": self.graph_name,
            "node_name": self.node_name,
            "event_type": self.event_type,
            "action_type": self.action_type,
            "timestamp": self.timestamp,
            "details": self.details,
        }


def build_jsonl_trace_hook(trace_path: Path) -> TraceHook:
    def _write_event(event: RuntimeTracePayload) -> None:
        append_jsonl_trace_event(trace_path, event)

    return _write_event


def build_sqlite_trace_hook(db_path: Path) -> TraceHook:
    def _write_event(event: RuntimeTracePayload) -> None:
        append_sqlite_trace_event(db_path, event)

    return _write_event


def compose_trace_hooks(*hooks: TraceHook | None) -> TraceHook | None:
    active_hooks = [hook for hook in hooks if hook is not None]
    if not active_hooks:
        return None

    def _composed(event: RuntimeTracePayload) -> None:
        for hook in active_hooks:
            try:
                # 这里逐个吞掉单个 sink 的异常，避免一个坏 sink 顺手掐断
                # 其他 trace sink，或者影响 ask 主链路的可观测性补充路径。
                hook(event)
            except Exception:
                continue

    return _composed


def append_jsonl_trace_event(trace_path: Path, event: RuntimeTracePayload) -> None:
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                dict(event),
                ensure_ascii=False,
                default=_json_default,
            )
        )
        handle.write("\n")


def append_sqlite_trace_event(db_path: Path, event: RuntimeTracePayload) -> None:
    record = _build_sqlite_trace_record(event)
    # 这里复用主 SQLite 文件，而不是再拆一套 trace 专用库，
    # 是为了先把“检索数据”和“运行轨迹”落到同一份本地事实源里，避免首版就分裂成两套持久化入口。
    initialized_db_path = initialize_index_db(db_path)
    connection = connect_sqlite(initialized_db_path)
    try:
        with connection:
            connection.execute(
                """
                INSERT INTO run_trace (
                    trace_id,
                    run_id,
                    thread_id,
                    graph_name,
                    node_name,
                    event_type,
                    action_type,
                    event_timestamp,
                    details_json
                )
                VALUES (
                    :trace_id,
                    :run_id,
                    :thread_id,
                    :graph_name,
                    :node_name,
                    :event_type,
                    :action_type,
                    :event_timestamp,
                    :details_json
                )
                ON CONFLICT(trace_id) DO NOTHING;
                """,
                record,
            )
    finally:
        connection.close()


def query_run_trace_events(
    connection: sqlite3.Connection,
    *,
    run_id: str | None = None,
    thread_id: str | None = None,
    limit: int = 100,
) -> list[PersistedRunTraceEvent]:
    normalized_run_id = (run_id or "").strip()
    normalized_thread_id = (thread_id or "").strip()
    if not normalized_run_id and not normalized_thread_id:
        raise ValueError("At least one of run_id or thread_id is required.")
    if limit <= 0:
        raise ValueError("Trace query limit must be greater than 0.")

    where_clauses: list[str] = []
    params: list[object] = []
    if normalized_run_id:
        where_clauses.append("run_id = ?")
        params.append(normalized_run_id)
    if normalized_thread_id:
        where_clauses.append("thread_id = ?")
        params.append(normalized_thread_id)

    rows = connection.execute(
        f"""
        SELECT
            trace_id,
            run_id,
            thread_id,
            graph_name,
            node_name,
            event_type,
            action_type,
            event_timestamp,
            details_json
        FROM run_trace
        WHERE {' AND '.join(where_clauses)}
        ORDER BY event_timestamp ASC, created_at ASC, trace_id ASC
        LIMIT ?;
        """,
        [*params, limit],
    ).fetchall()

    return [_build_persisted_trace_event(row) for row in rows]


def query_run_trace_events_in_db(
    db_path: Path,
    *,
    run_id: str | None = None,
    thread_id: str | None = None,
    limit: int = 100,
) -> list[PersistedRunTraceEvent]:
    initialized_db_path = initialize_index_db(db_path)
    connection = connect_sqlite(initialized_db_path)
    try:
        return query_run_trace_events(
            connection,
            run_id=run_id,
            thread_id=thread_id,
            limit=limit,
        )
    finally:
        connection.close()


def _build_sqlite_trace_record(event: RuntimeTracePayload) -> dict[str, str]:
    normalized_event = _normalize_trace_event(event)
    details_json = json.dumps(
        normalized_event["details"],
        ensure_ascii=False,
        default=_json_default,
        sort_keys=True,
    )
    trace_id = _build_trace_id(
        run_id=normalized_event["run_id"],
        thread_id=normalized_event["thread_id"],
        graph_name=normalized_event["graph_name"],
        node_name=normalized_event["node_name"],
        event_type=normalized_event["event_type"],
        action_type=normalized_event["action_type"],
        timestamp=normalized_event["timestamp"],
        details_json=details_json,
    )
    return {
        "trace_id": trace_id,
        "run_id": normalized_event["run_id"],
        "thread_id": normalized_event["thread_id"],
        "graph_name": normalized_event["graph_name"],
        "node_name": normalized_event["node_name"],
        "event_type": normalized_event["event_type"],
        "action_type": normalized_event["action_type"],
        "event_timestamp": normalized_event["timestamp"],
        "details_json": details_json,
    }


def _normalize_trace_event(event: RuntimeTracePayload) -> dict[str, object]:
    normalized_event: dict[str, object] = {}
    for field_name in (
        "run_id",
        "thread_id",
        "graph_name",
        "node_name",
        "event_type",
        "action_type",
        "timestamp",
    ):
        field_value = str(event.get(field_name, "")).strip()
        if not field_value:
            raise ValueError(f"Runtime trace event is missing required field: {field_name}.")
        normalized_event[field_name] = field_value

    details = event.get("details", {})
    if isinstance(details, Mapping):
        normalized_event["details"] = dict(details)
    else:
        # 这里把异常形态兜成结构化字典，而不是直接丢原对象，
        # 是为了保证 SQLite 聚合层永远可 JSON 序列化，避免坏 details 把整条 trace 写入打崩。
        normalized_event["details"] = {
            "unstructured_details_repr": repr(details),
        }
    return normalized_event


def _build_trace_id(
    *,
    run_id: str,
    thread_id: str,
    graph_name: str,
    node_name: str,
    event_type: str,
    action_type: str,
    timestamp: str,
    details_json: str,
) -> str:
    raw_key = "|".join(
        (
            run_id,
            thread_id,
            graph_name,
            node_name,
            event_type,
            action_type,
            timestamp,
            details_json,
        )
    )
    return f"trace_{hashlib.sha1(raw_key.encode('utf-8')).hexdigest()[:24]}"


def _build_persisted_trace_event(row: sqlite3.Row) -> PersistedRunTraceEvent:
    return PersistedRunTraceEvent(
        trace_id=row["trace_id"],
        run_id=row["run_id"],
        thread_id=row["thread_id"],
        graph_name=row["graph_name"],
        node_name=row["node_name"],
        event_type=row["event_type"],
        action_type=row["action_type"],
        timestamp=row["event_timestamp"],
        details=_load_details_json(row["details_json"]),
    )


def _load_details_json(raw_details_json: object) -> dict[str, object]:
    if not isinstance(raw_details_json, str) or not raw_details_json.strip():
        return {}

    loaded = json.loads(raw_details_json)
    if isinstance(loaded, dict):
        return loaded
    return {"details_value": loaded}


def _json_default(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (set, tuple)):
        return list(value)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _build_arg_parser(default_db_path: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query persisted Knowledge Steward runtime trace events from SQLite."
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=default_db_path,
        help="Path to the SQLite database file.",
    )
    parser.add_argument(
        "--run-id",
        help="Query trace events for a specific run_id.",
    )
    parser.add_argument(
        "--thread-id",
        help="Query trace events for a specific thread_id.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of trace events to return.",
    )
    return parser


def main() -> None:
    settings = get_settings()
    parser = _build_arg_parser(settings.index_db_path)
    args = parser.parse_args()
    if not ((args.run_id or "").strip() or (args.thread_id or "").strip()):
        parser.error("At least one of --run-id or --thread-id is required.")

    events = query_run_trace_events_in_db(
        args.db_path,
        run_id=args.run_id,
        thread_id=args.thread_id,
        limit=args.limit,
    )
    print(
        json.dumps(
            [event.as_dict() for event in events],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
