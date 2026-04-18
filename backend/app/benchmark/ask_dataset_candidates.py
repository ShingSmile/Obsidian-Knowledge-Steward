from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

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
CandidateKind = Literal["heading", "task", "date", "fact", "summary"]

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
    kind: CandidateKind
    bucket: AskBenchmarkBucket
    user_query: str
    note_path: str
    heading_path: str
    expected_facts: list[str]
    excerpt_anchor: str


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
    existing_source_keys = _collect_existing_source_keys(approved_dataset, backlog)
    seen_candidate_keys: set[str] = set()
    batch: list[AskBenchmarkCandidate] = []

    for note_path in sorted(resolved_vault_root.rglob("*.md")):
        if not note_path.is_file():
            continue

        parsed_note = parse_markdown_note(note_path)
        note_relative_path = note_path.relative_to(resolved_vault_root).as_posix()

        for seed in _build_candidate_seeds(parsed_note, note_relative_path):
            source_key = _source_key(seed.note_path, seed.heading_path)
            if source_key in existing_source_keys:
                continue

            candidate_key = _candidate_key(seed.note_path, seed.heading_path, seed.kind)
            if candidate_key in seen_candidate_keys:
                continue

            candidate = _build_candidate(seed=seed, fingerprint=candidate_key)
            if candidate is None:
                continue

            seen_candidate_keys.add(candidate_key)
            batch.append(candidate)
            if len(batch) == count:
                return batch

    return batch


def _build_candidate_seeds(parsed_note: ParsedNote, note_path: str) -> list[_CandidateSeed]:
    heading_chunk = _select_primary_heading_chunk(parsed_note)
    task_chunk = _select_task_chunk(parsed_note)
    summary_chunk = _select_summary_chunk(parsed_note)
    fact_chunk = _select_fact_chunk(parsed_note)

    seeds: list[_CandidateSeed] = []

    if heading_chunk is not None:
        heading_excerpt = _extract_fact_excerpt(heading_chunk.text)
        heading_facts = _extract_meaningful_facts(heading_chunk.text)
        if heading_excerpt and heading_facts:
            heading_label = _normalize_heading_label(
                _leaf_heading_label(heading_chunk.heading_path or "")
            )
            if heading_label:
                seeds.append(
                    _CandidateSeed(
                        kind="heading",
                        bucket="single_hop",
                        user_query=f"这篇笔记的{heading_label}部分讲了什么？",
                        note_path=note_path,
                        heading_path=heading_chunk.heading_path or note_path,
                        expected_facts=heading_facts,
                        excerpt_anchor=heading_excerpt,
                    )
                )

    if task_chunk is not None:
        task_facts = _extract_task_facts(task_chunk.text)
        if task_facts:
            seeds.append(
                _CandidateSeed(
                    kind="task",
                    bucket="single_hop",
                    user_query="这篇笔记列了哪些待办？",
                    note_path=note_path,
                    heading_path=task_chunk.heading_path or note_path,
                    expected_facts=task_facts,
                    excerpt_anchor=task_facts[0],
                )
            )

    if parsed_note.daily_note_date:
        date_chunk = summary_chunk or heading_chunk or task_chunk
        if date_chunk is not None:
            date_excerpt = _extract_fact_excerpt(date_chunk.text)
            date_facts = _extract_meaningful_facts(date_chunk.text)
            if date_excerpt and date_facts:
                seeds.append(
                    _CandidateSeed(
                        kind="date",
                        bucket="metadata_filter",
                        user_query=f"{parsed_note.daily_note_date} 这天做了什么？",
                        note_path=note_path,
                        heading_path=date_chunk.heading_path or note_path,
                        expected_facts=date_facts,
                        excerpt_anchor=date_excerpt,
                    )
                )

    if fact_chunk is not None:
        fact_excerpt = _extract_fact_excerpt(fact_chunk.text)
        if fact_excerpt:
            seeds.append(
                _CandidateSeed(
                    kind="fact",
                    bucket="single_hop",
                    user_query=_compose_fact_query(fact_excerpt),
                    note_path=note_path,
                    heading_path=fact_chunk.heading_path or note_path,
                    expected_facts=[fact_excerpt],
                    excerpt_anchor=fact_excerpt,
                )
            )

    if summary_chunk is not None:
        summary_excerpt = _extract_fact_excerpt(summary_chunk.text)
        if summary_excerpt:
            seeds.append(
                _CandidateSeed(
                    kind="summary",
                    bucket="single_hop",
                    user_query="这篇笔记主要讲了什么？",
                    note_path=note_path,
                    heading_path=summary_chunk.heading_path or note_path,
                    expected_facts=[summary_excerpt],
                    excerpt_anchor=summary_excerpt,
                )
            )

    return seeds


def _build_candidate(seed: _CandidateSeed, fingerprint: str) -> AskBenchmarkCandidate | None:
    if not seed.expected_facts or not seed.excerpt_anchor:
        return None

    locator = AskBenchmarkLocator.model_construct(
        note_path=seed.note_path,
        heading_path=seed.heading_path,
        excerpt_anchor=seed.excerpt_anchor,
    )
    return AskBenchmarkCandidate(
        case_id=f"ask_candidate_{fingerprint[:12]}",
        fingerprint=fingerprint,
        bucket=seed.bucket,
        user_query=seed.user_query,
        source_origin="sample_vault",
        expected_relevant_paths=[seed.note_path],
        expected_relevant_locators=[locator],
        expected_facts=list(seed.expected_facts),
        forbidden_claims=list(DEFAULT_FORBIDDEN_CLAIMS),
        allow_tool=False,
        expected_tool_names=[],
        allow_retrieval_only=True,
        should_generate_answer=True,
    )


def _select_primary_heading_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    for chunk in parsed_note.chunks:
        if chunk.heading_path and _has_substantive_content(chunk):
            return chunk
    return None


def _select_task_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    for chunk in parsed_note.chunks:
        if chunk.heading_path and _extract_task_facts(chunk.text):
            return chunk
    return None


def _select_summary_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    for chunk in parsed_note.chunks:
        if not chunk.heading_path:
            continue
        if not _has_substantive_content(chunk):
            continue
        heading_lower = chunk.heading_path.lower()
        if any(signal in heading_lower for signal in _HEADINGS_WITH_SUMMARY_SIGNAL):
            return chunk
    return None


def _select_fact_chunk(parsed_note: ParsedNote) -> NoteChunk | None:
    summary_chunk = _select_summary_chunk(parsed_note)
    if summary_chunk is not None and _extract_fact_excerpt(summary_chunk.text):
        return summary_chunk

    for chunk in parsed_note.chunks:
        if chunk.heading_path and _has_substantive_content(chunk) and _extract_fact_excerpt(chunk.text):
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


def _has_substantive_content(chunk: NoteChunk) -> bool:
    for raw_line in chunk.text.splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            return True
    return False


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


def _extract_meaningful_facts(text: str) -> list[str]:
    facts: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        cleaned = re.sub(r"^[-*]\s+\[[ xX]\]\s*", "", line)
        cleaned = re.sub(r"^[-*]\s*", "", cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            facts.append(cleaned)
    return facts


def _extract_task_facts(text: str) -> list[str]:
    pending: list[str] = []
    completed: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^[-*]\s+\[(?P<mark>[ xX])\]\s*(?P<body>.*\S)\s*$", line)
        if match is None:
            continue
        body = match.group("body").strip()
        if not body:
            continue
        if match.group("mark").lower() == "x":
            completed.append(body)
        else:
            pending.append(body)
    return pending or completed


def _compose_fact_query(fact_excerpt: str) -> str:
    if fact_excerpt.endswith(("。", "！", "？", ".", "!", "?")):
        return f"{fact_excerpt}这段在说什么？"
    return f"{fact_excerpt} 这段在说什么？"


def _collect_existing_source_keys(
    approved_dataset: AskBenchmarkDataset,
    backlog: AskBenchmarkReviewBacklog,
) -> set[str]:
    source_keys: set[str] = set()
    for case in approved_dataset.cases:
        for locator in case.expected_relevant_locators:
            source_keys.add(_source_key(locator.note_path, locator.heading_path))
    for item in backlog.items:
        for locator in item.expected_relevant_locators:
            source_keys.add(_source_key(locator.note_path, locator.heading_path))
    return source_keys


def _source_key(note_path: str, heading_path: str) -> str:
    return "\n".join(
        [
            note_path.strip().replace("\\", "/"),
            heading_path.strip(),
        ]
    )


def _candidate_key(note_path: str, heading_path: str, kind: CandidateKind) -> str:
    return hashlib.sha1(
        "\n".join(
            [
                note_path.strip().replace("\\", "/"),
                heading_path.strip(),
                kind,
            ]
        ).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AskBenchmarkCandidate",
    "build_candidate_batch",
]
