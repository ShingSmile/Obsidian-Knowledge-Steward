from __future__ import annotations

from app.context.safety import detect_safety_flags
from app.contracts.workflow import (
    ContextBundle,
    ContextEvidenceItem,
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
    flags: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        for flag in detect_safety_flags(candidate.text):
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

    return ContextBundle(
        user_intent=user_query,
        workflow_action=WorkflowAction.ASK_QA,
        evidence_items=evidence_items,
        tool_results=tool_results,
        allowed_tool_names=allowed_tool_names,
        token_budget=token_budget,
        safety_flags=_collect_flags(deduped),
        assembly_notes=assembly_notes,
    )
