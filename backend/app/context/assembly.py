from __future__ import annotations

from collections.abc import Iterable
import json

from app.context.safety import detect_safety_flags
from app.contracts.workflow import (
    ContextBundle,
    ContextEvidenceItem,
    DigestSourceNote,
    ProposalEvidence,
    RetrievedChunkCandidate,
    ToolExecutionResult,
    WorkflowAction,
)


def _dedupe_candidates(
    candidates: list[RetrievedChunkCandidate],
) -> tuple[list[RetrievedChunkCandidate], int]:
    seen_chunk_ids: set[str] = set()
    deduped: list[RetrievedChunkCandidate] = []
    removed_count = 0
    for candidate in candidates:
        if candidate.chunk_id in seen_chunk_ids:
            removed_count += 1
            continue
        seen_chunk_ids.add(candidate.chunk_id)
        deduped.append(candidate)
    return deduped, removed_count


def _estimate_candidate_chars(candidate: RetrievedChunkCandidate) -> int:
    heading = candidate.heading_path or ""
    return len(candidate.path) + len(heading) + len(candidate.text)


def _trim_candidates_to_budget(
    candidates: list[RetrievedChunkCandidate],
    token_budget: int,
) -> tuple[list[RetrievedChunkCandidate], int]:
    if token_budget <= 0:
        return [], len(candidates)
    kept: list[RetrievedChunkCandidate] = []
    consumed = 0
    dropped = 0
    for candidate in candidates:
        candidate_chars = _estimate_candidate_chars(candidate)
        if consumed + candidate_chars > token_budget:
            dropped += 1
            continue
        kept.append(candidate)
        consumed += candidate_chars
    return kept, dropped


def _collect_flags(candidates: list[RetrievedChunkCandidate]) -> list[str]:
    return _collect_text_flags(candidate.text for candidate in candidates)


def _collect_text_flags(texts: Iterable[str]) -> list[str]:
    flags: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for flag in detect_safety_flags(text):
            if flag in seen:
                continue
            seen.add(flag)
            flags.append(flag)
    return flags


def build_ask_context_bundle(
    *,
    user_query: str,
    candidates: list[RetrievedChunkCandidate],
    tool_results: list[ToolExecutionResult],
    token_budget: int,
    allowed_tool_names: list[str],
) -> ContextBundle:
    deduped, deduped_removed = _dedupe_candidates(candidates)
    trimmed, trimmed_removed = _trim_candidates_to_budget(deduped, token_budget)
    suspicious_trimmed = [
        item for item in trimmed if detect_safety_flags(item.text)
    ]

    evidence_items = [
        ContextEvidenceItem(
            source_path=item.path,
            chunk_id=item.chunk_id,
            heading_path=item.heading_path,
            text=item.text,
            score=item.score,
            source_kind="retrieval",
        )
        for item in trimmed
        if not detect_safety_flags(item.text)
    ]

    assembly_notes: list[str] = []
    if deduped_removed:
        assembly_notes.append(f"deduplicated:{deduped_removed}")
    if trimmed_removed:
        assembly_notes.append(f"trimmed_for_budget:{trimmed_removed}")
    if suspicious_trimmed:
        assembly_notes.append(f"filtered_suspicious:{len(suspicious_trimmed)}")

    return ContextBundle(
        user_intent=user_query,
        workflow_action=WorkflowAction.ASK_QA,
        evidence_items=evidence_items,
        tool_results=tool_results,
        allowed_tool_names=allowed_tool_names,
        token_budget=token_budget,
        safety_flags=_collect_text_flags(
            [
                *(item.text for item in suspicious_trimmed),
                *(
                    json.dumps(result.data, ensure_ascii=False, sort_keys=True)
                    for result in tool_results
                    if result.allow_context_reentry and result.ok and result.data
                ),
            ]
        ),
        assembly_notes=assembly_notes,
    )


def build_ingest_context_bundle(
    *,
    target_note_path: str,
    proposal_evidence: list[ProposalEvidence],
    related_candidates: list[RetrievedChunkCandidate],
    token_budget: int,
) -> ContextBundle:
    proposal_items = [
        ContextEvidenceItem(
            source_path=evidence.source_path,
            chunk_id=evidence.chunk_id,
            heading_path=evidence.heading_path,
            text=evidence.reason,
            score=None,
            source_kind="proposal",
        )
        for evidence in proposal_evidence
    ]

    deduped_related, deduped_removed = _dedupe_candidates(related_candidates)
    trimmed_related, trimmed_removed = _trim_candidates_to_budget(
        deduped_related,
        token_budget,
    )
    retrieval_items = [
        ContextEvidenceItem(
            source_path=item.path,
            chunk_id=item.chunk_id,
            heading_path=item.heading_path,
            text=item.text,
            score=item.score,
            source_kind="retrieval",
        )
        for item in trimmed_related
    ]

    assembly_notes = [
        "ordered:proposal_then_related",
        f"proposal_evidence:{len(proposal_items)}",
        f"related_candidates:{len(trimmed_related)}",
    ]
    if deduped_removed:
        assembly_notes.append(f"deduplicated:{deduped_removed}")
    if trimmed_removed:
        assembly_notes.append(f"trimmed_for_budget:{trimmed_removed}")

    return ContextBundle(
        user_intent=f"Review governance signals for {target_note_path}",
        workflow_action=WorkflowAction.INGEST_STEWARD,
        evidence_items=[*proposal_items, *retrieval_items],
        tool_results=[],
        allowed_tool_names=[],
        token_budget=token_budget,
        safety_flags=_collect_text_flags(
            [
                *(item.reason for item in proposal_evidence),
                *(candidate.text for candidate in deduped_related),
            ]
        ),
        assembly_notes=assembly_notes,
    )


def build_digest_context_bundle(
    *,
    source_notes: list[DigestSourceNote],
    token_budget: int,
) -> ContextBundle:
    evidence_items: list[ContextEvidenceItem] = []
    consumed = 0
    trimmed_removed = 0

    for note in source_notes:
        evidence_text = (
            f"title={note.title}; "
            f"note_type={note.note_type}; "
            f"daily_note_date={note.daily_note_date or ''}; "
            f"task_count={note.task_count}"
        )
        evidence_chars = len(note.path) + len(evidence_text)
        if token_budget > 0 and consumed + evidence_chars > token_budget:
            trimmed_removed += 1
            continue
        evidence_items.append(
            ContextEvidenceItem(
                source_path=note.path,
                chunk_id=note.note_id,
                heading_path=None,
                text=evidence_text,
                score=None,
                source_kind="digest",
            )
        )
        consumed += evidence_chars

    assembly_notes = [
        "ordered:source_notes",
        f"source_notes:{len(source_notes)}",
        f"digest_evidence:{len(evidence_items)}",
    ]
    if trimmed_removed:
        assembly_notes.append(f"trimmed_for_budget:{trimmed_removed}")

    return ContextBundle(
        user_intent="Assemble digest context from selected source notes",
        workflow_action=WorkflowAction.DAILY_DIGEST,
        evidence_items=evidence_items,
        tool_results=[],
        allowed_tool_names=[],
        token_budget=token_budget,
        safety_flags=_collect_text_flags(item.text for item in evidence_items),
        assembly_notes=assembly_notes,
    )
