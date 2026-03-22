from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Sequence

from app.config import Settings
from app.contracts.workflow import (
    IngestAnalysisFinding,
    IngestAnalysisResult,
    PatchOp,
    Proposal,
    ProposalEvidence,
    RetrievedChunkCandidate,
    RiskLevel,
    SafetyChecks,
    WorkflowAction,
)
from app.indexing.models import HeadingInfo, NoteChunk, ParsedNote
from app.indexing.parser import parse_markdown_note
from app.retrieval.hybrid import search_hybrid_chunks_in_db


REVIEW_HEADING_TITLE = "Knowledge Steward Review"
REVIEW_SCOPE_LABEL = "scoped_ingest_single_note"
MAX_EVIDENCE_COUNT = 3
MAX_RELATED_CANDIDATE_COUNT = 3
MAX_RETRIEVAL_QUERY_COUNT = 4
RELATED_RETRIEVAL_LIMIT = 8
SEARCHABLE_TERM_RE = re.compile(r"[0-9A-Za-z_\u4e00-\u9fff]+")


@dataclass(frozen=True)
class GovernanceIssue:
    code: str
    reason: str
    review_message: str


@dataclass(frozen=True)
class GovernanceFinding:
    finding_type: str
    reason: str
    review_message: str
    source: str
    evidence_path: str
    evidence_heading_path: str | None = None
    evidence_chunk_id: str | None = None


@dataclass(frozen=True)
class IngestProposalBuildResult:
    proposal: Proposal | None
    note_meta: dict[str, object]
    analysis_result: IngestAnalysisResult | None
    analysis_issues: list[dict[str, object]]
    skip_reason: str | None = None


def build_scoped_ingest_approval_proposal(
    *,
    thread_id: str,
    note_paths: Sequence[str],
    db_path: Path,
    settings: Settings,
    provider_preference: str | None = None,
) -> IngestProposalBuildResult:
    normalized_note_paths = [
        str(Path(note_path).expanduser().resolve())
        for note_path in note_paths
    ]
    note_meta: dict[str, object] = {
        "proposal_scope": REVIEW_SCOPE_LABEL,
        "requested_note_count": len(normalized_note_paths),
        "requested_note_paths": normalized_note_paths,
    }

    # 首版 retrieval-backed ingest proposal 仍明确只覆盖“单 note scoped ingest”。
    # 多 note 合并会立即扩成跨 note 冲突裁决，不属于 TASK-035 的边界。
    if len(normalized_note_paths) != 1:
        skip_reason = "proposal_requires_single_scoped_note"
        return IngestProposalBuildResult(
            proposal=None,
            note_meta={
                **note_meta,
                "proposal_eligible": False,
                "skip_reason": skip_reason,
            },
            analysis_result=None,
            analysis_issues=[],
            skip_reason=skip_reason,
        )

    target_note_path = Path(normalized_note_paths[0])
    parsed_note = parse_markdown_note(target_note_path)
    anchor_heading = _select_anchor_heading(parsed_note)
    existing_review_heading = _has_existing_review_heading(parsed_note)
    note_meta.update(
        {
            "target_note_path": str(target_note_path),
            "title": parsed_note.title,
            "note_type": parsed_note.note_type,
            "template_family": parsed_note.template_family,
            "daily_note_date": parsed_note.daily_note_date,
            "has_frontmatter": parsed_note.has_frontmatter,
            "heading_count": len(parsed_note.headings),
            "wikilink_count": len(parsed_note.wikilinks),
            "task_count": parsed_note.task_count,
            "existing_review_heading": existing_review_heading,
        }
    )

    if anchor_heading is None:
        skip_reason = "missing_anchor_heading"
        return IngestProposalBuildResult(
            proposal=None,
            note_meta={
                **note_meta,
                "proposal_eligible": False,
                "skip_reason": skip_reason,
            },
            analysis_result=_build_analysis_result(
                note_path=target_note_path,
                parsed_note=parsed_note,
                retrieval_queries=[],
                related_candidates=[],
                findings=[],
                fallback_reason=skip_reason,
            ),
            analysis_issues=[],
            skip_reason=skip_reason,
        )

    anchor_heading_line = _format_heading_line(anchor_heading)
    review_heading = _build_review_heading(anchor_heading.level)
    note_meta.update(
        {
            "anchor_heading_path": anchor_heading.heading_path,
            "anchor_heading_line": anchor_heading_line,
            "review_heading": review_heading,
        }
    )

    if existing_review_heading:
        skip_reason = "review_section_already_exists"
        return IngestProposalBuildResult(
            proposal=None,
            note_meta={
                **note_meta,
                "proposal_eligible": False,
                "skip_reason": skip_reason,
            },
            analysis_result=_build_analysis_result(
                note_path=target_note_path,
                parsed_note=parsed_note,
                retrieval_queries=[],
                related_candidates=[],
                findings=[],
                fallback_reason=skip_reason,
            ),
            analysis_issues=[],
            skip_reason=skip_reason,
        )

    retrieval_queries, related_candidates = _retrieve_related_candidates(
        db_path=db_path,
        target_note_path=target_note_path,
        parsed_note=parsed_note,
        settings=settings,
        provider_preference=provider_preference,
    )
    findings = _collect_governance_findings(
        note_path=target_note_path,
        parsed_note=parsed_note,
        anchor_heading=anchor_heading,
        related_candidates=related_candidates,
    )
    analysis_result = _build_analysis_result(
        note_path=target_note_path,
        parsed_note=parsed_note,
        retrieval_queries=retrieval_queries,
        related_candidates=related_candidates,
        findings=findings,
        fallback_reason=None,
    )
    analysis_issues = [
        finding.model_dump(mode="json")
        for finding in analysis_result.findings
    ]
    note_meta.update(
        {
            "retrieval_queries": retrieval_queries,
            "related_candidate_count": len(related_candidates),
            "related_candidate_paths": [candidate.path for candidate in related_candidates],
            "detected_issue_codes": [finding.finding_type for finding in findings],
            "analysis_finding_types": [finding.finding_type for finding in findings],
        }
    )

    if not findings:
        skip_reason = "no_governance_issues_detected"
        return IngestProposalBuildResult(
            proposal=None,
            note_meta={
                **note_meta,
                "proposal_eligible": False,
                "skip_reason": skip_reason,
            },
            analysis_result=analysis_result.model_copy(
                update={
                    "fallback_used": True,
                    "fallback_reason": skip_reason,
                }
            ),
            analysis_issues=[],
            skip_reason=skip_reason,
        )

    review_markdown = _build_review_markdown(
        parsed_note=parsed_note,
        review_heading=review_heading,
        findings=findings,
        related_candidates=related_candidates,
    )
    proposal = Proposal(
        proposal_id=_build_ingest_proposal_id(
            thread_id=thread_id,
            target_note_path=str(target_note_path),
        ),
        action_type=WorkflowAction.INGEST_STEWARD,
        target_note_path=str(target_note_path),
        summary=_build_summary(
            parsed_note=parsed_note,
            findings=findings,
            related_candidates=related_candidates,
        ),
        risk_level=_select_risk_level(findings=findings),
        evidence=_build_proposal_evidence(findings=findings),
        patch_ops=[
            PatchOp(
                op="merge_frontmatter",
                target_path=str(target_note_path),
                payload={
                    "knowledge_steward": {
                        "governance_status": "needs_review",
                        "review_scope": REVIEW_SCOPE_LABEL,
                        "detected_note_type": parsed_note.note_type,
                        "detected_template_family": parsed_note.template_family,
                        "detected_issue_codes": [finding.finding_type for finding in findings],
                        "analysis_scope": "retrieval_backed",
                        "related_candidate_count": len(related_candidates),
                    }
                },
            ),
            PatchOp(
                op="insert_under_heading",
                target_path=str(target_note_path),
                payload={
                    "heading": anchor_heading_line,
                    "content": review_markdown,
                },
            ),
        ],
        safety_checks=SafetyChecks(
            before_hash=_compute_note_before_hash(target_note_path),
            max_changed_lines=len(review_markdown.splitlines()) + 8,
            contains_delete=False,
        ),
    )

    return IngestProposalBuildResult(
        proposal=proposal,
        note_meta={
            **note_meta,
            "proposal_eligible": True,
            "skip_reason": None,
        },
        analysis_result=analysis_result,
        analysis_issues=analysis_issues,
        skip_reason=None,
    )


def _collect_governance_issues(
    parsed_note: ParsedNote,
    *,
    include_no_wikilinks: bool,
) -> list[GovernanceIssue]:
    issues: list[GovernanceIssue] = []
    if not parsed_note.has_frontmatter:
        issues.append(
            GovernanceIssue(
                code="missing_frontmatter",
                reason="当前笔记没有 frontmatter，后续治理状态缺少稳定的结构化落点。",
                review_message="建议补最小 frontmatter 字段，给后续治理状态和筛选规则留稳定落点。",
            )
        )
    if include_no_wikilinks and not parsed_note.wikilinks:
        issues.append(
            GovernanceIssue(
                code="no_wikilinks",
                reason="当前笔记未检测到任何 wikilink，关联上下文较弱。",
                review_message="建议补至少一条相关双链，避免这条笔记继续孤立。",
            )
        )
    if parsed_note.task_count > 0:
        issues.append(
            GovernanceIssue(
                code="has_open_tasks",
                reason=f"当前笔记检测到 {parsed_note.task_count} 个任务项，可能需要单独整理行动区。",
                review_message=(
                    f"当前笔记包含 {parsed_note.task_count} 个任务项，"
                    "建议确认是否需要整理到明确的行动区或后续计划中。"
                ),
            )
        )
    if parsed_note.note_type == "generic_note":
        issues.append(
            GovernanceIssue(
                code="unclassified_note_type",
                reason="当前笔记未命中稳定模板，note_type 仍是 generic_note。",
                review_message="当前笔记未命中稳定模板，建议人工确认标题结构和 note_type 是否合理。",
            )
        )
    return issues


def _collect_governance_findings(
    *,
    note_path: Path,
    parsed_note: ParsedNote,
    anchor_heading: HeadingInfo,
    related_candidates: list[RetrievedChunkCandidate],
) -> list[GovernanceFinding]:
    findings: list[GovernanceFinding] = []
    duplicate_candidate = _select_duplicate_candidate(
        parsed_note=parsed_note,
        related_candidates=related_candidates,
    )
    if duplicate_candidate is not None:
        findings.append(
            GovernanceFinding(
                finding_type="duplicate_hint",
                reason=(
                    f"已召回到标题高度相似的旧笔记《{duplicate_candidate.title}》，"
                    "当前笔记存在重复沉淀风险。"
                ),
                review_message=(
                    f"related retrieve 命中《{duplicate_candidate.title}》，"
                    "建议人工确认是否应合并、互链或改写，避免重复知识继续分叉。"
                ),
                source="related_retrieval",
                evidence_path=duplicate_candidate.path,
                evidence_heading_path=duplicate_candidate.heading_path,
                evidence_chunk_id=duplicate_candidate.chunk_id,
            )
        )

    orphan_hint_emitted = False
    if not parsed_note.wikilinks and related_candidates:
        primary_candidate = related_candidates[0]
        findings.append(
            GovernanceFinding(
                finding_type="orphan_hint",
                reason=(
                    f"当前笔记没有 wikilink，但 related retrieve 已命中《{primary_candidate.title}》，"
                    "说明主题上下文已存在，只是尚未显式连回知识库。"
                ),
                review_message=(
                    f"当前笔记未建立双链，但已召回《{primary_candidate.title}》等相关上下文，"
                    "建议至少补一条显式关联，避免后续问答和复盘只能靠隐式检索兜底。"
                ),
                source="related_retrieval",
                evidence_path=primary_candidate.path,
                evidence_heading_path=primary_candidate.heading_path,
                evidence_chunk_id=primary_candidate.chunk_id,
            )
        )
        orphan_hint_emitted = True

    local_issues = _collect_governance_issues(
        parsed_note,
        include_no_wikilinks=not orphan_hint_emitted,
    )
    for issue in local_issues:
        chunk = _select_issue_chunk(parsed_note=parsed_note, issue_code=issue.code)
        findings.append(
            GovernanceFinding(
                finding_type=issue.code,
                reason=issue.reason,
                review_message=issue.review_message,
                source="local_structure",
                evidence_path=str(note_path),
                evidence_heading_path=(
                    chunk.heading_path
                    if chunk and chunk.heading_path
                    else anchor_heading.heading_path
                ),
                evidence_chunk_id=chunk.chunk_id if chunk else None,
            )
        )

    return findings


def _build_review_markdown(
    *,
    parsed_note: ParsedNote,
    review_heading: str,
    findings: list[GovernanceFinding],
    related_candidates: list[RetrievedChunkCandidate],
) -> str:
    lines = [
        review_heading,
        "",
        f"- 当前检测范围：{REVIEW_SCOPE_LABEL}。",
        (
            f"- 检测摘要：note_type=`{parsed_note.note_type}`，"
            f"template=`{parsed_note.template_family}`，"
            f"wikilinks={len(parsed_note.wikilinks)}，"
            f"tasks={parsed_note.task_count}。"
        ),
    ]
    if parsed_note.daily_note_date:
        lines.append(f"- 日期线索：{parsed_note.daily_note_date}。")
    if related_candidates:
        related_briefs = "；".join(
            _format_related_candidate_brief(candidate)
            for candidate in related_candidates[:MAX_RELATED_CANDIDATE_COUNT]
        )
        lines.append(f"- related_retrieve 命中：{related_briefs}。")
    for finding in findings:
        lines.append(f"- {finding.review_message}")
    lines.append(
        "- 说明：本节已结合当前笔记结构信号与最小 related retrieve，"
        "仍未引入向量检索、GraphRAG 或自动冲突裁决。"
    )
    return "\n".join(lines)


def _build_summary(
    *,
    parsed_note: ParsedNote,
    findings: list[GovernanceFinding],
    related_candidates: list[RetrievedChunkCandidate],
) -> str:
    finding_labels = "、".join(finding.finding_type for finding in findings[:3])
    if related_candidates:
        return (
            f"为 {parsed_note.title} 补最小治理标记与审查小节，"
            f"结合 {len(related_candidates)} 条 related retrieve 上下文，"
            f"聚焦 {len(findings)} 个治理信号（{finding_labels}）。"
        )
    return (
        f"为 {parsed_note.title} 补最小治理标记与审查小节，"
        f"聚焦 {len(findings)} 个已检测结构信号（{finding_labels}）。"
    )


def _build_proposal_evidence(
    *,
    findings: list[GovernanceFinding],
) -> list[ProposalEvidence]:
    evidence_items: list[ProposalEvidence] = []
    seen: set[tuple[str, str | None, str]] = set()
    for finding in findings:
        evidence_key = (
            finding.evidence_path,
            finding.evidence_chunk_id,
            finding.finding_type,
        )
        if evidence_key in seen:
            continue
        seen.add(evidence_key)
        evidence_items.append(
            ProposalEvidence(
                source_path=finding.evidence_path,
                heading_path=finding.evidence_heading_path,
                chunk_id=finding.evidence_chunk_id,
                reason=finding.reason,
            )
        )
        if len(evidence_items) >= MAX_EVIDENCE_COUNT:
            break
    return evidence_items


def _build_analysis_result(
    *,
    note_path: Path,
    parsed_note: ParsedNote,
    retrieval_queries: list[str],
    related_candidates: list[RetrievedChunkCandidate],
    findings: list[GovernanceFinding],
    fallback_reason: str | None,
) -> IngestAnalysisResult:
    return IngestAnalysisResult(
        scope=REVIEW_SCOPE_LABEL,
        target_note_path=str(note_path),
        target_note_title=parsed_note.title,
        retrieval_queries=retrieval_queries,
        related_candidates=related_candidates,
        findings=[
            IngestAnalysisFinding(
                finding_type=finding.finding_type,
                summary=finding.reason,
                source=finding.source,
                source_paths=[finding.evidence_path],
                related_chunk_ids=(
                    [finding.evidence_chunk_id]
                    if finding.evidence_chunk_id
                    else []
                ),
            )
            for finding in findings
        ],
        fallback_used=fallback_reason is not None,
        fallback_reason=fallback_reason,
    )


def _select_issue_chunk(
    *,
    parsed_note: ParsedNote,
    issue_code: str,
) -> NoteChunk | None:
    if issue_code == "has_open_tasks":
        for chunk in parsed_note.chunks:
            if chunk.task_count > 0:
                return chunk
    return parsed_note.chunks[0] if parsed_note.chunks else None


def _retrieve_related_candidates(
    *,
    db_path: Path,
    target_note_path: Path,
    parsed_note: ParsedNote,
    settings: Settings,
    provider_preference: str | None,
) -> tuple[list[str], list[RetrievedChunkCandidate]]:
    retrieval_queries = _build_related_retrieval_queries(parsed_note)
    if not retrieval_queries:
        return [], []

    related_candidates_by_chunk: dict[str, RetrievedChunkCandidate] = {}
    normalized_target_path = str(target_note_path.expanduser().resolve())
    for query in retrieval_queries:
        try:
            response = search_hybrid_chunks_in_db(
                db_path,
                query,
                settings=settings,
                limit=RELATED_RETRIEVAL_LIMIT,
                provider_preference=provider_preference,
                allow_filter_fallback=False,
            )
        except ValueError:
            continue

        for candidate in response.candidates:
            candidate_path = str(Path(candidate.path).expanduser().resolve())
            # 显式排除当前目标 note，避免 analysis 把“自己被检索到”误当成 related evidence。
            if candidate_path == normalized_target_path:
                continue
            related_candidates_by_chunk.setdefault(candidate.chunk_id, candidate)

    related_candidates = sorted(
        related_candidates_by_chunk.values(),
        key=lambda candidate: (-candidate.score, candidate.path, candidate.start_line),
    )
    return retrieval_queries, related_candidates[:MAX_RELATED_CANDIDATE_COUNT]


def _build_related_retrieval_queries(parsed_note: ParsedNote) -> list[str]:
    query_candidates: list[str] = []
    if parsed_note.note_type != "daily_note" and _contains_searchable_term(parsed_note.title):
        query_candidates.append(parsed_note.title)

    query_candidates.extend(parsed_note.wikilinks[:MAX_RETRIEVAL_QUERY_COUNT])

    for heading in parsed_note.headings:
        if len(query_candidates) >= MAX_RETRIEVAL_QUERY_COUNT:
            break
        if heading.text == parsed_note.title:
            continue
        if not _contains_searchable_term(heading.text):
            continue
        query_candidates.append(heading.text)

    deduplicated_queries: list[str] = []
    seen: set[str] = set()
    for query in query_candidates:
        normalized_query = query.strip()
        if not normalized_query:
            continue
        query_key = normalized_query.casefold()
        if query_key in seen:
            continue
        seen.add(query_key)
        deduplicated_queries.append(normalized_query)
    return deduplicated_queries[:MAX_RETRIEVAL_QUERY_COUNT]


def _contains_searchable_term(value: str) -> bool:
    return bool(SEARCHABLE_TERM_RE.search(value.strip()))


def _select_duplicate_candidate(
    *,
    parsed_note: ParsedNote,
    related_candidates: list[RetrievedChunkCandidate],
) -> RetrievedChunkCandidate | None:
    normalized_target_title = _normalize_title_token(parsed_note.title)
    if not normalized_target_title:
        return None

    for candidate in related_candidates:
        if _normalize_title_token(candidate.title) == normalized_target_title:
            return candidate
        if _normalize_title_token(Path(candidate.path).stem) == normalized_target_title:
            return candidate
    return None


def _normalize_title_token(value: str) -> str:
    return "".join(SEARCHABLE_TERM_RE.findall(value)).casefold()


def _format_related_candidate_brief(candidate: RetrievedChunkCandidate) -> str:
    note_name = Path(candidate.path).stem
    if candidate.heading_path:
        return f"{note_name}（{candidate.heading_path}）"
    return note_name


def _select_anchor_heading(parsed_note: ParsedNote) -> HeadingInfo | None:
    for heading in parsed_note.headings:
        if heading.level == 1:
            return heading
    return parsed_note.headings[0] if parsed_note.headings else None


def _has_existing_review_heading(parsed_note: ParsedNote) -> bool:
    expected_heading = REVIEW_HEADING_TITLE.casefold()
    return any(heading.text.strip().casefold() == expected_heading for heading in parsed_note.headings)


def _build_review_heading(anchor_heading_level: int) -> str:
    review_level = min(anchor_heading_level + 1, 6)
    return f"{'#' * review_level} {REVIEW_HEADING_TITLE}"


def _format_heading_line(heading: HeadingInfo) -> str:
    return f"{'#' * heading.level} {heading.text}"


def _select_risk_level(*, findings: list[GovernanceFinding]) -> RiskLevel:
    finding_types = {finding.finding_type for finding in findings}
    if (
        "duplicate_hint" in finding_types
        or "has_open_tasks" in finding_types
        or len(findings) >= 3
    ):
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _compute_note_before_hash(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _build_ingest_proposal_id(
    *,
    thread_id: str,
    target_note_path: str,
) -> str:
    suffix = hashlib.sha1(
        f"{thread_id}:{target_note_path}".encode("utf-8")
    ).hexdigest()[:16]
    return f"prop_ingest_{suffix}"
