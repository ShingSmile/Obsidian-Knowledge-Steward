from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.benchmark.ask_dataset import (
    AskBenchmarkBucket,
    AskBenchmarkDataset,
    AskBenchmarkLocator,
    AskBenchmarkReviewBacklog,
    AskBenchmarkSourceOrigin,
)
from app.indexing.models import NoteChunk, ParsedNote
from app.indexing.parser import parse_markdown_note


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
DEFAULT_FORBIDDEN_CLAIMS = ["不要编造笔记中没有出现的细节。"]
_HEADINGS_WITH_SUMMARY_SIGNAL = ("summary", "总结", "复盘", "highlights")


class AskBenchmarkCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    case_id: NonEmptyStr
    fingerprint: NonEmptyStr
    bucket: AskBenchmarkBucket
    user_query: NonEmptyStr
    source_origin: AskBenchmarkSourceOrigin = "sample_vault"
    expected_relevant_paths: list[NonEmptyStr]
    expected_relevant_locators: list[AskBenchmarkLocator]
    expected_facts: list[NonEmptyStr]
    forbidden_claims: list[NonEmptyStr] = Field(default_factory=lambda: list(DEFAULT_FORBIDDEN_CLAIMS))
    allow_tool: bool = False
    expected_tool_names: list[NonEmptyStr] = Field(default_factory=list)
    allow_retrieval_only: bool = True
    should_generate_answer: bool = True


@dataclass(frozen=True)
class _CandidateSeed:
    bucket: AskBenchmarkBucket
    user_query: str
    note_path: str
    chunk: NoteChunk


def build_candidate_batch(
    *,
    vault_root: Path,
    approved_dataset: AskBenchmarkDataset,
    backlog: AskBenchmarkReviewBacklog,
    count: int = 5,
) -> list[AskBenchmarkCandidate]:
    if count <= 0:
        return []

    resolved_vault_root = vault_root.expanduser().resolve()
    existing_fingerprints = _collect_existing_fingerprints(approved_dataset, backlog)
    batch: list[AskBenchmarkCandidate] = []

    for note_path in sorted(resolved_vault_root.rglob("*.md")):
        if not note_path.is_file():
            continue

        parsed_note = parse_markdown_note(note_path)
        note_relative_path = note_path.relative_to(resolved_vault_root).as_posix()

        for seed in _build_candidate_seeds(parsed_note, note_relative_path):
            fingerprint = _candidate_fingerprint(
                note_path=seed.note_path,
                heading_path=seed.chunk.heading_path or seed.note_path,
                user_query=seed.user_query,
            )
            if fingerprint in existing_fingerprints:
                continue

            candidate = _build_candidate(seed=seed, fingerprint=fingerprint)
            existing_fingerprints.add(fingerprint)
            batch.append(candidate)
            if len(batch) == count:
                return batch

    return batch


def _build_candidate_seeds(parsed_note: ParsedNote, note_path: str) -> list[_CandidateSeed]:
    heading_chunk = _select_primary_heading_chunk(parsed_note)
    task_chunk = _select_task_chunk(parsed_note)
    summary_chunk = _select_summary_chunk(parsed_note) or heading_chunk or task_chunk
    fact_chunk = _select_fact_chunk(parsed_note) or summary_chunk or heading_chunk or task_chunk

    seeds: list[_CandidateSeed] = []

    if heading_chunk is not None:
        seeds.append(
            _CandidateSeed(
                bucket="single_hop",
                user_query=f"这篇笔记的{_normalize_heading_label(_leaf_heading_label(heading_chunk.heading_path or ''))}部分讲了什么？",
                note_path=note_path,
                chunk=heading_chunk,
            )
        )

    if task_chunk is not None:
        seeds.append(
            _CandidateSeed(
                bucket="single_hop",
                user_query="这篇笔记列了哪些待办？",
                note_path=note_path,
                chunk=task_chunk,
            )
        )

    if parsed_note.daily_note_date:
        date_chunk = summary_chunk or heading_chunk or task_chunk
        if date_chunk is not None:
            seeds.append(
                _CandidateSeed(
                    bucket="metadata_filter",
                    user_query=f"{parsed_note.daily_note_date} 这天做了什么？",
                    note_path=note_path,
                    chunk=date_chunk,
                )
            )

    if fact_chunk is not None:
        fact_excerpt = _extract_fact_excerpt(fact_chunk.text)
        if fact_excerpt:
            seeds.append(
                _CandidateSeed(
                    bucket="single_hop",
                    user_query=_compose_fact_query(fact_excerpt),
                    note_path=note_path,
                    chunk=fact_chunk,
                )
            )

    if summary_chunk is not None:
        seeds.append(
            _CandidateSeed(
                bucket="single_hop",
                user_query="这篇笔记主要讲了什么？",
                note_path=note_path,
                chunk=summary_chunk,
            )
        )

    return seeds


def _build_candidate(seed: _CandidateSeed, fingerprint: str) -> AskBenchmarkCandidate:
    note_path = seed.note_path
    locator = _build_locator(note_path=note_path, chunk=seed.chunk)
    excerpt_anchor = locator.excerpt_anchor
    return AskBenchmarkCandidate(
        case_id=f"ask_candidate_{fingerprint[:12]}",
        fingerprint=fingerprint,
        bucket=seed.bucket,
        user_query=seed.user_query,
        source_origin="sample_vault",
        expected_relevant_paths=[note_path],
        expected_relevant_locators=[locator],
        expected_facts=[excerpt_anchor],
        forbidden_claims=list(DEFAULT_FORBIDDEN_CLAIMS),
        allow_tool=False,
        expected_tool_names=[],
        allow_retrieval_only=True,
        should_generate_answer=True,
    )


def _build_locator(*, note_path: str, chunk: NoteChunk) -> AskBenchmarkLocator:
    payload: dict[str, object] = {
        "note_path": note_path,
        "heading_path": chunk.heading_path or note_path,
        "excerpt_anchor": _extract_fact_excerpt(chunk.text),
    }
    return AskBenchmarkLocator.model_construct(**payload)


def _select_primary_heading_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    for chunk in parsed_note.chunks:
        if chunk.heading_path and _has_substantive_content(chunk):
            return chunk
    for chunk in parsed_note.chunks:
        if chunk.heading_path:
            return chunk
    return None


def _select_task_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    task_chunks = [chunk for chunk in parsed_note.chunks if chunk.task_count > 0 and chunk.heading_path]
    if task_chunks:
        return task_chunks[0]
    return None


def _select_summary_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    summary_chunks = [
        chunk
        for chunk in parsed_note.chunks
        if chunk.heading_path and any(signal in (chunk.heading_path or "").lower() for signal in _HEADINGS_WITH_SUMMARY_SIGNAL)
    ]
    for chunk in summary_chunks:
        if _has_substantive_content(chunk):
            return chunk
    return summary_chunks[0] if summary_chunks else None


def _select_fact_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    summary_chunk = _select_summary_chunk(parsed_note)
    if summary_chunk is not None:
        excerpt = _extract_fact_excerpt(summary_chunk.text)
        if excerpt:
            return summary_chunk

    for chunk in parsed_note.chunks:
        if chunk.heading_path and _has_substantive_content(chunk):
            excerpt = _extract_fact_excerpt(chunk.text)
            if excerpt and excerpt != _heading_only_text(chunk.text):
                return chunk
    return None


def _leaf_heading_label(heading_path: str) -> str:
    if " > " in heading_path:
        return heading_path.rsplit(" > ", 1)[-1]
    return heading_path


def _normalize_heading_label(label: str) -> str:
    cleaned = label.strip()
    cleaned = re.sub(r"^[一二三四五六七八九十0-9]+[、.．\s]*", "", cleaned)
    return cleaned or label.strip()


def _heading_only_text(text: str) -> str:
    stripped_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not stripped_lines:
        return ""
    if stripped_lines[0].startswith("#"):
        return stripped_lines[0]
    return stripped_lines[0]


def _has_substantive_content(chunk: NoteChunk) -> bool:
    body_lines = [line.strip() for line in chunk.text.splitlines() if line.strip()]
    if not body_lines:
        return False
    return any(not line.startswith("#") for line in body_lines)


def _extract_fact_excerpt(text: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        cleaned = re.sub(r"^[-*]\s+\[[ xX]\]\s*", "", line)
        cleaned = re.sub(r"^[-*]\s*", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            return cleaned
    return ""


def _compose_fact_query(fact_excerpt: str) -> str:
    if fact_excerpt.endswith(("。", "！", "？", ".", "!", "?")):
        return f"{fact_excerpt}这段在说什么？"
    return f"{fact_excerpt} 这段在说什么？"


def _collect_existing_fingerprints(
    approved_dataset: AskBenchmarkDataset,
    backlog: AskBenchmarkReviewBacklog,
) -> set[str]:
    fingerprints: set[str] = set()

    for case in approved_dataset.cases:
        fingerprints.update(_fingerprints_for_case_like(case.expected_relevant_locators, case.user_query))

    for item in backlog.items:
        fingerprints.update(_fingerprints_for_case_like(item.expected_relevant_locators, item.user_query))

    return fingerprints


def _fingerprints_for_case_like(
    locators: list[AskBenchmarkLocator],
    user_query: str,
) -> set[str]:
    fingerprints: set[str] = set()
    for locator in locators:
        fingerprints.add(
            _candidate_fingerprint(
                note_path=locator.note_path,
                heading_path=locator.heading_path,
                user_query=user_query,
            )
        )
    return fingerprints


def _candidate_fingerprint(*, note_path: str, heading_path: str, user_query: str) -> str:
    raw = "\n".join(
        [
            note_path.strip().replace("\\", "/"),
            heading_path.strip(),
            user_query.strip(),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


__all__ = [
    "AskBenchmarkCandidate",
    "build_candidate_batch",
]
