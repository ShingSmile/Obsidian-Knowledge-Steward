from __future__ import annotations

from collections.abc import Iterable
import json

from app.context.safety import detect_safety_flags
from app.contracts.workflow import (
    ContextAssemblyMetadata,
    ContextBundle,
    ContextEvidenceItem,
    ContextSourceNote,
    DigestSourceNote,
    ProposalEvidence,
    RetrievedChunkCandidate,
    ToolExecutionResult,
    WorkflowAction,
)

ASK_RELEVANCE_RATIO = 0.35
ASK_PER_SOURCE_LIMIT = 2
ASK_FULL_TEXT_CHAR_BUDGET = 900
ASK_SUMMARY_CHAR_BUDGET = 280
ASK_FULL_TEXT_EVIDENCE_COUNT = 2


def _title_from_source_path(source_path: str) -> str:
    return source_path.rsplit("/", 1)[-1].removesuffix(".md")


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


def _filter_candidates_by_relevance(
    candidates: list[RetrievedChunkCandidate],
) -> tuple[list[RetrievedChunkCandidate], int, float]:
    if not candidates:
        return [], 0, 0.0

    top_score = max(candidate.score for candidate in candidates)
    relevance_threshold = top_score * ASK_RELEVANCE_RATIO
    filtered = [candidate for candidate in candidates if candidate.score >= relevance_threshold]
    if not filtered:
        filtered = [max(candidates, key=lambda candidate: candidate.score)]
    return filtered, len(candidates) - len(filtered), relevance_threshold


def _limit_candidates_per_source(
    candidates: list[RetrievedChunkCandidate],
) -> tuple[list[RetrievedChunkCandidate], int]:
    kept_chunk_ids: set[str] = set()
    counts_by_path: dict[str, int] = {}
    for candidate in sorted(candidates, key=lambda item: (-item.score, item.path, item.start_line)):
        path_count = counts_by_path.get(candidate.path, 0)
        if path_count >= ASK_PER_SOURCE_LIMIT:
            continue
        counts_by_path[candidate.path] = path_count + 1
        kept_chunk_ids.add(candidate.chunk_id)

    kept = [candidate for candidate in candidates if candidate.chunk_id in kept_chunk_ids]
    return kept, len(candidates) - len(kept)


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


def _apply_weighted_budget(
    candidates: list[RetrievedChunkCandidate],
    token_budget: int,
) -> tuple[list[tuple[RetrievedChunkCandidate, str]], int]:
    if token_budget <= 0:
        return [], len(candidates)

    kept: list[tuple[RetrievedChunkCandidate, str]] = []
    consumed = 0
    dropped = 0
    for index, candidate in enumerate(candidates):
        char_limit = (
            ASK_FULL_TEXT_CHAR_BUDGET
            if index < ASK_FULL_TEXT_EVIDENCE_COUNT
            else ASK_SUMMARY_CHAR_BUDGET
        )
        visible_text = candidate.text[:char_limit]
        candidate_chars = len(candidate.path) + len(candidate.heading_path or "") + len(
            visible_text
        )
        if token_budget > 0 and consumed + candidate_chars > token_budget:
            dropped += 1
            continue
        kept.append((candidate, visible_text))
        consumed += candidate_chars
    return kept, dropped


def _build_source_notes(
    evidence_items: list[ContextEvidenceItem],
) -> list[ContextSourceNote]:
    source_notes_by_path: dict[str, ContextSourceNote] = {}
    source_notes: list[ContextSourceNote] = []

    for item in evidence_items:
        source_note = source_notes_by_path.get(item.source_path)
        if source_note is None:
            source_note = ContextSourceNote(
                source_path=item.source_path,
                title=item.source_note_title or _title_from_source_path(item.source_path),
                chunk_count=0,
                max_score=item.score,
            )
            source_notes_by_path[item.source_path] = source_note
            source_notes.append(source_note)

        source_note.chunk_count += 1
        if item.score is not None and (
            source_note.max_score is None or item.score > source_note.max_score
        ):
            source_note.max_score = item.score

    return source_notes


def _assign_position_hints(evidence_items: list[ContextEvidenceItem]) -> None:
    total_by_source_path: dict[str, int] = {}
    for item in evidence_items:
        total_by_source_path[item.source_path] = (
            total_by_source_path.get(item.source_path, 0) + 1
        )

    seen_by_source_path: dict[str, int] = {}
    for item in evidence_items:
        seen_by_source_path[item.source_path] = (
            seen_by_source_path.get(item.source_path, 0) + 1
        )
        item.position_hint = (
            f"第 {seen_by_source_path[item.source_path]} 条 / "
            f"共 {total_by_source_path[item.source_path]} 条"
        )


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
    shadow_trimmed, _ = _trim_candidates_to_budget(deduped, token_budget)
    suspicious_trimmed = [
        item for item in shadow_trimmed if detect_safety_flags(item.text)
    ]
    safe_candidates = [
        item for item in deduped if not detect_safety_flags(item.text)
    ]
    relevant, relevance_removed, relevance_threshold = _filter_candidates_by_relevance(
        safe_candidates
    )
    diversified, diversity_removed = _limit_candidates_per_source(relevant)
    weighted_candidates, weighted_removed = _apply_weighted_budget(
        diversified,
        token_budget,
    )

    evidence_items = [
        ContextEvidenceItem(
            source_path=item.path,
            chunk_id=item.chunk_id,
            source_note_title=item.title,
            heading_path=item.heading_path,
            text=visible_text,
            score=item.score,
            source_kind="retrieval",
        )
        for item, visible_text in weighted_candidates
    ]
    _assign_position_hints(evidence_items)

    assembly_notes: list[str] = []
    if deduped_removed:
        assembly_notes.append(f"deduplicated:{deduped_removed}")
    if relevance_removed:
        assembly_notes.append(f"relevance_filtered:{relevance_removed}")
    if diversity_removed:
        assembly_notes.append(f"diversity_filtered:{diversity_removed}")
    if weighted_removed:
        assembly_notes.append(f"trimmed_for_budget:{weighted_removed}")
    if suspicious_trimmed:
        assembly_notes.append(f"filtered_suspicious:{len(suspicious_trimmed)}")

    return ContextBundle(
        user_intent=user_query,
        workflow_action=WorkflowAction.ASK_QA,
        evidence_items=evidence_items,
        source_notes=_build_source_notes(evidence_items),
        assembly_metadata=ContextAssemblyMetadata(
            initial_candidate_count=len(candidates),
            relevance_filtered_count=relevance_removed,
            diversity_filtered_count=diversity_removed,
            budget_filtered_count=weighted_removed,
            suspicious_filtered_count=len(suspicious_trimmed),
            final_evidence_count=len(evidence_items),
            relevance_threshold=relevance_threshold,
            per_source_limit=ASK_PER_SOURCE_LIMIT,
            full_text_char_budget=ASK_FULL_TEXT_CHAR_BUDGET,
            summary_char_budget=ASK_SUMMARY_CHAR_BUDGET,
        ),
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
        source_notes=[],
        assembly_metadata=ContextAssemblyMetadata(),
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
        source_notes=[],
        assembly_metadata=ContextAssemblyMetadata(),
        tool_results=[],
        allowed_tool_names=[],
        token_budget=token_budget,
        safety_flags=_collect_text_flags(item.text for item in evidence_items),
        assembly_notes=assembly_notes,
    )
