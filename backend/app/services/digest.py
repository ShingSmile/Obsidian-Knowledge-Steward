from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path

from app.config import Settings
from app.context.assembly import build_digest_context_bundle
from app.contracts.workflow import (
    DigestSourceNote,
    DigestWorkflowResult,
    PatchOp,
    Proposal,
    ProposalEvidence,
    RiskLevel,
    SafetyChecks,
    WorkflowAction,
)
from app.indexing.store import connect_sqlite, initialize_index_db


DIGEST_SOURCE_LIMIT = 6
PREFERRED_DIGEST_NOTE_TYPES = ("daily_note", "summary_note")
DIGEST_CONTEXT_TOKEN_BUDGET = 2000


def run_minimal_digest(*, settings: Settings) -> DigestWorkflowResult:
    source_notes, fallback_reason = _select_digest_source_notes(
        settings.index_db_path,
        limit=DIGEST_SOURCE_LIMIT,
    )
    if not source_notes:
        return DigestWorkflowResult(
            digest_markdown=(
                "当前索引中还没有可用于生成 DAILY_DIGEST 的笔记。\n"
                "请先执行一次 INGEST_STEWARD，再重新触发 digest。"
            ),
            source_notes=[],
            source_note_count=0,
            fallback_used=True,
            fallback_reason="no_indexed_notes",
        )

    context_bundle = build_digest_context_bundle(
        source_notes=source_notes,
        token_budget=DIGEST_CONTEXT_TOKEN_BUDGET,
    )
    return DigestWorkflowResult(
        digest_markdown=_build_digest_markdown(
            source_notes=source_notes,
            fallback_reason=fallback_reason,
        ),
        source_notes=source_notes,
        source_note_count=len(source_notes),
        fallback_used=fallback_reason is not None,
        fallback_reason=fallback_reason,
        context_bundle_summary={
            "evidence_count": len(context_bundle.evidence_items),
            "assembly_notes": context_bundle.assembly_notes,
        },
    )


def build_digest_approval_proposal(
    *,
    settings: Settings,
    thread_id: str,
    digest_result: DigestWorkflowResult,
) -> Proposal | None:
    if not digest_result.source_notes:
        return None

    target_note = _select_digest_target_note(digest_result.source_notes)
    before_hash = _compute_note_before_hash(
        settings.sample_vault_dir / target_note.path,
    )
    digest_heading = "## Knowledge Steward Digest"
    patch_ops = [
        PatchOp(
            op="merge_frontmatter",
            target_path=target_note.path,
            payload={
                "ks_pending_digest_review": True,
                "ks_digest_thread_id": thread_id,
                "ks_digest_source_note_count": digest_result.source_note_count,
            },
        ),
        PatchOp(
            op="insert_under_heading",
            target_path=target_note.path,
            payload={
                "heading": digest_heading,
                "content": digest_result.digest_markdown,
            },
        ),
    ]

    # 首条真实 approval proposal 先限定成“在一篇已有笔记里合并 frontmatter + 插入 digest 文本”，
    # 这样能复用 TASK-019 计划中的受限写回边界，而不是提前扩成任意文件写入。
    return Proposal(
        proposal_id=_build_digest_proposal_id(
            thread_id=thread_id,
            target_note_path=target_note.path,
        ),
        action_type=WorkflowAction.DAILY_DIGEST,
        target_note_path=target_note.path,
        summary=(
            f"将本次 DAILY_DIGEST 写入 {target_note.title}，"
            f"并标记这次摘要需要人工审批。"
        ),
        risk_level=RiskLevel.MEDIUM,
        evidence=[
            ProposalEvidence(
                source_path=source_note.path,
                heading_path=None,
                chunk_id=None,
                reason=_build_digest_evidence_reason(
                    source_note=source_note,
                    target_note=target_note,
                ),
            )
            for source_note in digest_result.source_notes[:3]
        ],
        patch_ops=patch_ops,
        safety_checks=SafetyChecks(
            before_hash=before_hash,
            max_changed_lines=len(digest_result.digest_markdown.splitlines()) + 6,
            contains_delete=False,
        ),
    )


def _select_digest_source_notes(
    db_path: Path,
    *,
    limit: int,
) -> tuple[list[DigestSourceNote], str | None]:
    normalized_db_path = initialize_index_db(db_path)
    connection = connect_sqlite(normalized_db_path)
    try:
        preferred_notes = _query_digest_source_notes(
            connection,
            limit=limit,
            preferred_only=True,
        )
        if len(preferred_notes) >= limit:
            return preferred_notes, None

        # 优先 daily/summary 是为了让首版 digest 更贴近“复盘”语义；
        # 但当索引里暂时没有这两类笔记时，仍要退回最近更新的通用笔记，避免 workflow 直接失效。
        supplemental_notes = _query_digest_source_notes(
            connection,
            limit=limit - len(preferred_notes),
            preferred_only=False,
            excluded_note_ids={note.note_id for note in preferred_notes},
        )
    finally:
        connection.close()

    source_notes = preferred_notes + supplemental_notes
    if not preferred_notes and source_notes:
        return source_notes, "no_digest_like_notes"
    return source_notes, None


def _select_digest_target_note(source_notes: list[DigestSourceNote]) -> DigestSourceNote:
    for source_note in source_notes:
        if source_note.note_type == "daily_note":
            return source_note
    return source_notes[0]


def _query_digest_source_notes(
    connection,
    *,
    limit: int,
    preferred_only: bool,
    excluded_note_ids: set[str] | None = None,
) -> list[DigestSourceNote]:
    conditions: list[str] = []
    params: list[object] = []
    excluded_note_ids = excluded_note_ids or set()

    if preferred_only:
        conditions.append(
            "note_type IN ('daily_note', 'summary_note')"
        )
    else:
        conditions.append(
            "note_type NOT IN ('daily_note', 'summary_note')"
        )

    if excluded_note_ids:
        placeholders = ",".join("?" for _ in excluded_note_ids)
        conditions.append(f"note_id NOT IN ({placeholders})")
        params.extend(sorted(excluded_note_ids))

    where_clause = " AND ".join(conditions)
    order_by_clause = (
        """
        ORDER BY
            CASE
                WHEN daily_note_date IS NULL THEN 1
                ELSE 0
            END,
            daily_note_date DESC,
            source_mtime_ns DESC,
            path ASC
        """
        if preferred_only
        else """
        ORDER BY
            source_mtime_ns DESC,
            path ASC
        """
    )

    rows = connection.execute(
        f"""
        SELECT
            note_id,
            path,
            title,
            note_type,
            template_family,
            daily_note_date,
            source_mtime_ns,
            task_count
        FROM note
        WHERE {where_clause}
        {order_by_clause}
        LIMIT ?;
        """,
        (*params, limit),
    ).fetchall()

    return [
        DigestSourceNote(
            note_id=row["note_id"],
            path=row["path"],
            title=row["title"],
            note_type=row["note_type"],
            template_family=row["template_family"],
            daily_note_date=row["daily_note_date"],
            source_mtime_ns=row["source_mtime_ns"],
            task_count=row["task_count"],
        )
        for row in rows
    ]


def _build_digest_markdown(
    *,
    source_notes: list[DigestSourceNote],
    fallback_reason: str | None,
) -> str:
    note_type_counts = Counter(note.note_type for note in source_notes)
    total_task_count = sum(note.task_count for note in source_notes)
    daily_dates = sorted(
        {
            note.daily_note_date
            for note in source_notes
            if note.daily_note_date
        }
    )

    lines = [
        f"本次 DAILY_DIGEST 基于最近 {len(source_notes)} 篇已索引笔记生成。",
        f"来源分布：{_format_note_type_counts(note_type_counts)}。",
    ]
    if daily_dates:
        if len(daily_dates) == 1:
            lines.append(f"覆盖日期：{daily_dates[0]}。")
        else:
            lines.append(f"覆盖日期：{daily_dates[0]} 至 {daily_dates[-1]}。")

    if total_task_count > 0:
        lines.append(f"待跟进任务：来源笔记中共检测到 {total_task_count} 项任务。")
    else:
        lines.append("待跟进任务：当前来源笔记中未检测到任务项。")

    if fallback_reason == "no_digest_like_notes":
        lines.append("说明：当前没有识别到 daily_note / summary_note，本次退回最近更新的通用笔记。")

    lines.append("")
    lines.append("## 重点来源")
    for note in source_notes[:4]:
        note_label = note.daily_note_date or Path(note.path).name
        lines.append(
            f"- {note.title}（{note.note_type}，{note_label}，任务 {note.task_count} 项）"
        )

    if len(source_notes) > 4:
        lines.append("")
        lines.append(f"其余 {len(source_notes) - 4} 篇笔记已保留在 source_notes 中，可供后续扩展节点继续消费。")

    return "\n".join(lines)


def _format_note_type_counts(note_type_counts: Counter[str]) -> str:
    parts: list[str] = []
    for note_type in ("daily_note", "summary_note", "generic_note"):
        count = note_type_counts.get(note_type, 0)
        if count:
            parts.append(f"{note_type} {count} 篇")
    for note_type in sorted(note_type_counts):
        if note_type in {"daily_note", "summary_note", "generic_note"}:
            continue
        parts.append(f"{note_type} {note_type_counts[note_type]} 篇")
    return "，".join(parts) if parts else "无"


def _compute_note_before_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _build_digest_proposal_id(
    *,
    thread_id: str,
    target_note_path: str,
) -> str:
    suffix = hashlib.sha1(
        f"{thread_id}:{target_note_path}".encode("utf-8")
    ).hexdigest()[:16]
    return f"prop_digest_{suffix}"


def _build_digest_evidence_reason(
    *,
    source_note: DigestSourceNote,
    target_note: DigestSourceNote,
) -> str:
    if source_note.path == target_note.path:
        return "目标笔记本身就是本次 digest 的主要来源，适合作为首条真实审批写入目标。"
    return (
        f"{source_note.title} 是本次 digest 的来源笔记之一，"
        f"需要在 {target_note.title} 中留下可审查的汇总结果。"
    )
