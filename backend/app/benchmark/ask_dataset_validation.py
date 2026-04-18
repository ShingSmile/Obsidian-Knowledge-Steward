from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from app.benchmark.ask_dataset import AskBenchmarkCase, AskBenchmarkDataset
from app.indexing.models import NoteChunk, ParsedNote
from app.indexing.parser import parse_markdown_note
from app.path_semantics import PathContractError, resolve_vault_relative


FINAL_BUCKET_CAPS: dict[str, int] = {
    "single_hop": 20,
    "multi_hop": 10,
    "metadata_filter": 8,
    "abstain_or_no_hit": 6,
    "tool_allowed": 6,
}
FINAL_CASE_COUNT = 50
MIN_SAMPLE_VAULT_CASES = 40
MAX_FIXTURE_CASES = 10


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_ask_benchmark_case(case: AskBenchmarkCase, vault_root: Path) -> ValidationResult:
    result = ValidationResult()
    _validate_expected_paths(case, vault_root, result)

    for locator_index, locator in enumerate(case.expected_relevant_locators):
        locator_prefix = f"{case.case_id}.expected_relevant_locators[{locator_index}]"
        if not isinstance(locator.note_path, str) or not locator.note_path.strip():
            result.errors.append(f"{locator_prefix}.note_path must be a non-empty string.")
            continue
        if not isinstance(locator.heading_path, str) or not locator.heading_path.strip():
            result.errors.append(f"{locator_prefix}.heading_path must be a non-empty string.")
            continue

        try:
            _, _, heading_chunks = resolve_heading_locator(
                locator.note_path,
                locator.heading_path,
                vault_root,
            )
        except (FileNotFoundError, PathContractError, ValueError) as exc:
            result.errors.append(f"{locator_prefix}: {exc}")
            continue

        if not isinstance(locator.excerpt_anchor, str) or not locator.excerpt_anchor.strip():
            result.errors.append(f"{locator_prefix}.excerpt_anchor must be a non-empty string.")
            continue

        selected_chunk, line_range_warning, line_range_error = _assess_locator_scope(
            heading_chunks,
            locator.line_range,
        )
        if line_range_error is not None:
            result.errors.append(f"{locator_prefix}.line_range: {line_range_error}")
            continue

        if line_range_warning is not None:
            anchor_error = check_excerpt_anchor(
                locator.excerpt_anchor,
                heading_chunks,
            )
            if anchor_error is None:
                result.warnings.append(f"{locator_prefix}.line_range: {line_range_warning}")
                continue
            result.warnings.append(f"{locator_prefix}.line_range: {line_range_warning}")
            result.errors.append(
                f"{locator_prefix}.line_range: {line_range_warning} {anchor_error}"
            )
            continue

        anchor_error = check_excerpt_anchor(
            locator.excerpt_anchor,
            [selected_chunk] if selected_chunk is not None else heading_chunks,
        )
        if anchor_error is not None:
            result.errors.append(f"{locator_prefix}.excerpt_anchor: {anchor_error}")

    return result


def validate_ask_benchmark_dataset(
    dataset: AskBenchmarkDataset,
    vault_root: Path,
) -> ValidationResult:
    result = ValidationResult()
    case_ids: set[str] = set()
    bucket_counts: Counter[str] = Counter()
    sample_vault_count = 0
    fixture_count = 0

    for case_index, case in enumerate(dataset.cases):
        if case.case_id in case_ids:
            result.errors.append(f"cases[{case_index}].case_id={case.case_id!r} is duplicated.")
        else:
            case_ids.add(case.case_id)

        bucket_counts[case.bucket] += 1
        if case.source_origin == "sample_vault":
            sample_vault_count += 1
        elif case.source_origin == "fixture":
            fixture_count += 1
        else:
            result.errors.append(
                f"cases[{case_index}].source_origin={case.source_origin!r} is not supported."
            )

        case_result = validate_ask_benchmark_case(case, vault_root)
        result.errors.extend(
            f"cases[{case_index}].{message}"
            for message in case_result.errors
        )
        result.warnings.extend(
            f"cases[{case_index}].{message}"
            for message in case_result.warnings
        )

    _validate_progressive_distribution(
        bucket_counts=bucket_counts,
        total_cases=len(dataset.cases),
        sample_vault_count=sample_vault_count,
        fixture_count=fixture_count,
        result=result,
    )
    return result


def resolve_heading_locator(
    note_path: str,
    heading_path: str,
    vault_root: Path,
) -> tuple[Path, ParsedNote, list[NoteChunk]]:
    resolved_note_path = resolve_vault_relative(note_path, vault_root=vault_root)
    if not resolved_note_path.exists():
        raise FileNotFoundError(f"note_path {note_path!r} does not exist.")

    parsed_note = parse_markdown_note(resolved_note_path)
    matching_chunks = [
        chunk for chunk in parsed_note.chunks if chunk.heading_path == heading_path
    ]
    if not matching_chunks:
        raise ValueError(
            f"heading_path {heading_path!r} does not resolve inside note_path {note_path!r}."
        )
    matching_chunks.sort(key=lambda item: (item.start_line, item.end_line, item.chunk_id))
    return resolved_note_path, parsed_note, matching_chunks


def check_line_range_within_heading(
    line_range: dict[str, int] | None,
    heading_chunks: Sequence[NoteChunk],
) -> tuple[NoteChunk | None, str | None, str | None]:
    return _assess_locator_scope(heading_chunks, line_range)


def _assess_locator_scope(
    heading_chunks: Sequence[NoteChunk],
    line_range: dict[str, int] | None,
) -> tuple[NoteChunk | None, str | None, str | None]:
    if line_range is None:
        if len(heading_chunks) == 1:
            return heading_chunks[0], None, None
        if len(heading_chunks) > 1:
            return None, None, "heading_path is ambiguous; line_range is required."
        return None, None, "heading_path does not resolve to a unique section."

    start_line = line_range.get("start_line")
    end_line = line_range.get("end_line")
    if not isinstance(start_line, int) or not isinstance(end_line, int):
        return None, None, "line_range must include integer start_line and end_line values."
    if start_line > end_line:
        return None, None, "line_range.start_line must be less than or equal to line_range.end_line."

    matching_chunks = [
        chunk
        for chunk in heading_chunks
        if chunk.start_line <= start_line and end_line <= chunk.end_line
    ]
    if len(matching_chunks) == 1:
        return matching_chunks[0], None, None
    if len(matching_chunks) == 0:
        return None, "line_range drifted outside the resolved heading scope.", None
    return None, None, "line_range is ambiguous for the resolved heading_path."


def check_excerpt_anchor(
    excerpt_anchor: str,
    heading_chunks: Sequence[NoteChunk],
    *,
    selected_chunk: NoteChunk | None = None,
) -> str | None:
    if selected_chunk is None:
        if any(excerpt_anchor in chunk.text for chunk in heading_chunks):
            return None
        return "excerpt_anchor no longer matches the resolved heading content."
    if excerpt_anchor not in selected_chunk.text:
        return "excerpt_anchor no longer matches the resolved heading content."
    return None


def _validate_expected_paths(
    case: AskBenchmarkCase,
    vault_root: Path,
    result: ValidationResult,
) -> None:
    for path_index, raw_path in enumerate(case.expected_relevant_paths):
        try:
            resolved_path = resolve_vault_relative(raw_path, vault_root=vault_root)
        except PathContractError as exc:
            result.errors.append(
                f"{case.case_id}.expected_relevant_paths[{path_index}]: {exc}"
            )
            continue
        if not resolved_path.exists():
            result.errors.append(
                f"{case.case_id}.expected_relevant_paths[{path_index}]={raw_path!r} does not exist."
            )


def _validate_progressive_distribution(
    *,
    bucket_counts: Counter[str],
    total_cases: int,
    sample_vault_count: int,
    fixture_count: int,
    result: ValidationResult,
) -> None:
    for bucket, cap in FINAL_BUCKET_CAPS.items():
        bucket_count = bucket_counts.get(bucket, 0)
        if bucket_count > cap:
            result.errors.append(
                f"bucket {bucket!r} has {bucket_count} cases but the cap is {cap}."
            )

    if fixture_count > MAX_FIXTURE_CASES:
        result.errors.append(
            f"fixture cases must not exceed {MAX_FIXTURE_CASES}; found {fixture_count}."
        )

    if total_cases > FINAL_CASE_COUNT:
        result.errors.append(
            f"dataset has {total_cases} cases but the final dataset size is {FINAL_CASE_COUNT}."
        )
        return

    if total_cases == FINAL_CASE_COUNT:
        for bucket, cap in FINAL_BUCKET_CAPS.items():
            bucket_count = bucket_counts.get(bucket, 0)
            if bucket_count != cap:
                result.errors.append(
                    f"final dataset requires {cap} {bucket} cases; found {bucket_count}."
                )
        if sample_vault_count < MIN_SAMPLE_VAULT_CASES:
            result.errors.append(
                f"final dataset requires at least {MIN_SAMPLE_VAULT_CASES} sample_vault cases; "
                f"found {sample_vault_count}."
            )
