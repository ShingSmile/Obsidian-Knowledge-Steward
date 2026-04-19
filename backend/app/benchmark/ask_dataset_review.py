from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from app.benchmark.ask_dataset import (
    ASK_BENCHMARK_DIR,
    AskBenchmarkBacklogItem,
    AskBenchmarkCase,
    AskBenchmarkDataset,
    AskBenchmarkReviewBacklog,
    load_ask_benchmark_backlog,
    load_ask_benchmark_dataset,
    write_ask_benchmark_backlog,
    write_ask_benchmark_dataset,
)
from app.benchmark.ask_dataset_candidates import (
    AskBenchmarkCandidate,
    _candidate_fingerprint,
    build_candidate_batch,
)
from app.benchmark.ask_dataset_validation import ValidationResult, validate_ask_benchmark_dataset
from app.config import get_settings


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    case_id: NonEmptyStr
    decision: Literal["approve", "revise", "reject"]
    review_notes: NonEmptyStr


class AskBenchmarkCandidateBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    candidates: list[AskBenchmarkCandidate]


@dataclass(frozen=True)
class ReviewApplyResult:
    approved_count: int
    backlog_count: int
    skipped_count: int
    approved_case_ids: list[str]
    backlog_case_ids: list[str]


def load_candidate_batch(path: Path) -> list[AskBenchmarkCandidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return AskBenchmarkCandidateBatch.model_validate(payload).candidates


def write_candidate_batch(candidates: list[AskBenchmarkCandidate], path: Path) -> None:
    payload = AskBenchmarkCandidateBatch.model_construct(
        schema_version=1,
        candidates=candidates,
    ).model_dump(mode="json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_review_decisions(path: Path) -> list[ReviewDecision]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("review file must contain a JSON list of decisions.")
    return [ReviewDecision.model_validate(item) for item in payload]


def validate_ask_benchmark_review_backlog(
    backlog: AskBenchmarkReviewBacklog,
    vault_root: Path,
    *,
    known_case_ids: set[str] | None = None,
) -> ValidationResult:
    result = ValidationResult()
    case_ids: set[str] = set(known_case_ids or set())
    stored_fingerprints: set[str] = set()
    effective_fingerprints: set[str] = set()

    for item_index, item in enumerate(backlog.items):
        item_prefix = f"items[{item_index}]"
        if item.review_status not in {"revise", "reject"}:
            result.errors.append(
                f"{item_prefix}.review_status={item.review_status!r} is not supported."
            )

        if item.case_id in case_ids:
            result.errors.append(f"{item_prefix}.case_id={item.case_id!r} is duplicated.")
        else:
            case_ids.add(item.case_id)

        case_result = validate_ask_benchmark_dataset(
            AskBenchmarkDataset.model_construct(
                schema_version=1,
                cases=[
                    AskBenchmarkCase.model_validate(
                        {
                            **item.model_dump(mode="json", exclude={"fingerprint"}),
                            "review_status": "approved",
                        }
                    )
                ],
            ),
            vault_root,
        )
        result.errors.extend(f"{item_prefix}.{message}" for message in case_result.errors)
        result.warnings.extend(f"{item_prefix}.{message}" for message in case_result.warnings)

        item_effective_fingerprints = _backlog_item_effective_fingerprints(item)
        item_effective_fingerprint = _single_effective_fingerprint(
            item_effective_fingerprints,
            prefix=f"{item_prefix}.fingerprint",
            kind="backlog item",
            result=result,
        )
        if item_effective_fingerprint is None:
            continue
        if item.fingerprint in stored_fingerprints:
            result.errors.append(f"{item_prefix}.fingerprint={item.fingerprint!r} is duplicated.")
        else:
            stored_fingerprints.add(item.fingerprint)

        if item.fingerprint != item_effective_fingerprint:
            result.errors.append(
                f"{item_prefix}.fingerprint does not match the content-derived fingerprint."
            )

        if item_effective_fingerprint in effective_fingerprints:
            result.errors.append(
                f"{item_prefix}.fingerprint overlaps with another backlog item."
            )
        effective_fingerprints.add(item_effective_fingerprint)

    return result


def apply_review_outcomes(
    *,
    candidate_batch: list[AskBenchmarkCandidate],
    review_decisions: list[ReviewDecision],
    dataset_path: Path,
    backlog_path: Path,
    vault_root: Path,
) -> ReviewApplyResult:
    if not candidate_batch:
        if review_decisions:
            raise ValueError("review decisions were provided but the candidate batch is empty.")
        return ReviewApplyResult(
            approved_count=0,
            backlog_count=0,
            skipped_count=0,
            approved_case_ids=[],
            backlog_case_ids=[],
        )

    approved_dataset = _load_dataset_required(dataset_path)
    review_backlog = _load_backlog_required(backlog_path)
    candidates_by_case_id = _group_candidates_by_case_id(candidate_batch)
    decision_by_case_id = _index_decisions(review_decisions)

    unexpected_decisions = sorted(set(decision_by_case_id) - set(candidates_by_case_id))
    if unexpected_decisions:
        raise ValueError(f"review decisions include unknown case_ids: {', '.join(unexpected_decisions)}")

    reviewed_candidates: list[AskBenchmarkCandidate] = []
    for decision in review_decisions:
        matched_candidates = candidates_by_case_id[decision.case_id]
        if len(matched_candidates) != 1:
            raise ValueError(f"duplicate case_id {decision.case_id!r} in candidate batch.")
        reviewed_candidates.append(matched_candidates[0])
    if not reviewed_candidates:
        return ReviewApplyResult(
            approved_count=0,
            backlog_count=0,
            skipped_count=len(candidate_batch),
            approved_case_ids=[],
            backlog_case_ids=[],
        )

    _reject_duplicate_candidates(reviewed_candidates)
    _reject_persisted_collisions(reviewed_candidates, approved_dataset, review_backlog)

    approved_cases: list[AskBenchmarkCase] = []
    backlog_items: list[AskBenchmarkBacklogItem] = []
    approved_case_ids: list[str] = []
    backlog_case_ids: list[str] = []

    for candidate, decision in zip(reviewed_candidates, review_decisions, strict=True):
        if decision.decision == "approve":
            approved_cases.append(_candidate_to_case(candidate, decision))
            approved_case_ids.append(decision.case_id)
            continue
        backlog_items.append(_candidate_to_backlog_item(candidate, decision))
        backlog_case_ids.append(decision.case_id)

    prospective_dataset = AskBenchmarkDataset.model_construct(
        schema_version=1,
        cases=[*approved_dataset.cases, *approved_cases],
    )
    validation = validate_ask_benchmark_dataset(prospective_dataset, vault_root)
    if validation.errors:
        raise ValueError("; ".join(validation.errors))

    prospective_backlog = AskBenchmarkReviewBacklog.model_construct(
        schema_version=1,
        items=[*review_backlog.items, *backlog_items],
    )

    backlog_validation = validate_ask_benchmark_review_backlog(
        prospective_backlog,
        vault_root,
        known_case_ids={case.case_id for case in approved_dataset.cases},
    )
    if backlog_validation.errors:
        raise ValueError("; ".join(backlog_validation.errors))

    _write_review_outputs_atomic(
        prospective_dataset=prospective_dataset,
        prospective_backlog=prospective_backlog,
        dataset_path=dataset_path,
        backlog_path=backlog_path,
    )

    return ReviewApplyResult(
        approved_count=len(approved_case_ids),
        backlog_count=len(backlog_case_ids),
        skipped_count=len(candidate_batch) - len(review_decisions),
        approved_case_ids=approved_case_ids,
        backlog_case_ids=backlog_case_ids,
    )


def validate_ask_benchmark_review_files(
    *,
    dataset_path: Path,
    backlog_path: Path,
    vault_root: Path,
) -> ValidationResult:
    result = ValidationResult()
    if not dataset_path.exists():
        result.errors.append(f"dataset_path {str(dataset_path)!r} does not exist.")
    if not backlog_path.exists():
        result.errors.append(f"backlog_path {str(backlog_path)!r} does not exist.")
    if result.errors:
        return result

    dataset = load_ask_benchmark_dataset(dataset_path)
    backlog = load_ask_benchmark_backlog(backlog_path)
    dataset_result = validate_ask_benchmark_dataset(dataset, vault_root)
    backlog_result = validate_ask_benchmark_review_backlog(
        backlog,
        vault_root,
        known_case_ids={case.case_id for case in dataset.cases},
    )

    result.errors.extend(dataset_result.errors)
    result.errors.extend(backlog_result.errors)
    result.warnings.extend(dataset_result.warnings)
    result.warnings.extend(backlog_result.warnings)

    dataset_fingerprints = _collect_case_fingerprints(dataset)
    backlog_fingerprints = _collect_backlog_fingerprints(backlog)
    overlap = sorted(dataset_fingerprints.intersection(backlog_fingerprints))
    if overlap:
        result.errors.append(
            f"backlog fingerprint content overlaps with approved dataset: {', '.join(overlap)}"
        )
    return result


def _candidate_to_case(candidate: AskBenchmarkCandidate, decision: ReviewDecision) -> AskBenchmarkCase:
    return AskBenchmarkCase.model_validate(
        {
            **candidate.model_dump(mode="json", exclude={"fingerprint"}),
            "review_status": "approved",
            "review_notes": decision.review_notes,
        }
    )


def _candidate_to_backlog_item(
    candidate: AskBenchmarkCandidate,
    decision: ReviewDecision,
) -> AskBenchmarkBacklogItem:
    return AskBenchmarkBacklogItem.model_validate(
        {
            **candidate.model_dump(mode="json"),
            "review_status": decision.decision,
            "review_notes": decision.review_notes,
        }
    )


def _load_dataset_or_empty(path: Path) -> AskBenchmarkDataset:
    if path.exists():
        return load_ask_benchmark_dataset(path)
    return AskBenchmarkDataset.model_construct(schema_version=1, cases=[])


def _load_backlog_or_empty(path: Path) -> AskBenchmarkReviewBacklog:
    if path.exists():
        return load_ask_benchmark_backlog(path)
    return AskBenchmarkReviewBacklog.model_construct(schema_version=1, items=[])


def _group_candidates_by_case_id(candidates: list[AskBenchmarkCandidate]) -> dict[str, list[AskBenchmarkCandidate]]:
    grouped: dict[str, list[AskBenchmarkCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.case_id, []).append(candidate)
    return grouped


def _index_decisions(decisions: list[ReviewDecision]) -> dict[str, ReviewDecision]:
    indexed: dict[str, ReviewDecision] = {}
    for decision in decisions:
        if decision.case_id in indexed:
            raise ValueError(f"duplicate review decision for case_id {decision.case_id!r}.")
        indexed[decision.case_id] = decision
    return indexed


def _reject_duplicate_candidates(candidates: list[AskBenchmarkCandidate]) -> None:
    case_ids: set[str] = set()
    stored_fingerprints: set[str] = set()
    effective_fingerprints: set[str] = set()
    for candidate in candidates:
        if candidate.case_id in case_ids:
            raise ValueError(f"duplicate case_id {candidate.case_id!r} in candidate batch.")
        candidate_effective_fingerprints = _candidate_effective_fingerprints(candidate)
        candidate_effective_fingerprint = _single_effective_fingerprint(
            candidate_effective_fingerprints,
            prefix=f"{candidate.case_id}.fingerprint",
            kind="candidate",
        )
        if candidate_effective_fingerprint is None:
            raise ValueError(
                f"fingerprint identity is ambiguous for candidate {candidate.case_id!r}."
            )
        if candidate.fingerprint != candidate_effective_fingerprint:
            raise ValueError(
                f"fingerprint {candidate.fingerprint!r} does not match the content-derived fingerprint."
            )
        if candidate.fingerprint in stored_fingerprints:
            raise ValueError(f"duplicate fingerprint {candidate.fingerprint!r} in candidate batch.")
        if candidate_effective_fingerprint in effective_fingerprints:
            duplicate_fingerprint = candidate_effective_fingerprint
            raise ValueError(f"duplicate fingerprint {duplicate_fingerprint!r} in candidate batch.")
        case_ids.add(candidate.case_id)
        stored_fingerprints.add(candidate.fingerprint)
        effective_fingerprints.add(candidate_effective_fingerprint)


def _reject_persisted_collisions(
    candidates: list[AskBenchmarkCandidate],
    dataset: AskBenchmarkDataset,
    backlog: AskBenchmarkReviewBacklog,
) -> None:
    existing_fingerprints = _collect_persisted_fingerprints(dataset, backlog)
    existing_case_ids = {item.case_id for item in backlog.items}
    for candidate in candidates:
        if candidate.case_id in existing_case_ids:
            raise ValueError(f"case_id {candidate.case_id!r} already exists in benchmark data.")
        candidate_effective_fingerprint = _single_effective_fingerprint(
            _candidate_effective_fingerprints(candidate),
            prefix=f"{candidate.case_id}.fingerprint",
            kind="candidate",
        )
        if candidate_effective_fingerprint is None:
            raise ValueError(
                f"fingerprint identity is ambiguous for candidate {candidate.case_id!r}."
            )
        if candidate_effective_fingerprint in existing_fingerprints:
            raise ValueError(
                f"fingerprint {candidate_effective_fingerprint!r} already exists in benchmark data."
            )


def _collect_persisted_fingerprints(
    dataset: AskBenchmarkDataset,
    backlog: AskBenchmarkReviewBacklog,
) -> set[str]:
    fingerprints: set[str] = set()
    for case in dataset.cases:
        fingerprints.update(_case_effective_fingerprints(case))
    for item in backlog.items:
        fingerprints.update(_backlog_item_effective_fingerprints(item))
    return fingerprints


def _candidate_effective_fingerprints(candidate: AskBenchmarkCandidate) -> set[str]:
    fingerprints: set[str] = set()
    for locator in candidate.expected_relevant_locators:
        fingerprints.add(
            _candidate_fingerprint(
                note_path=locator.note_path,
                heading_path=locator.heading_path,
                user_query=candidate.user_query,
            )
        )
    return fingerprints


def _case_effective_fingerprints(case: AskBenchmarkCase) -> set[str]:
    fingerprints: set[str] = set()
    for locator in case.expected_relevant_locators:
        fingerprints.add(
            _candidate_fingerprint(
                note_path=locator.note_path,
                heading_path=locator.heading_path,
                user_query=case.user_query,
            )
        )
    return fingerprints


def _backlog_item_effective_fingerprints(item: AskBenchmarkBacklogItem) -> set[str]:
    fingerprints: set[str] = set()
    for locator in item.expected_relevant_locators:
        fingerprints.add(
            _candidate_fingerprint(
                note_path=locator.note_path,
                heading_path=locator.heading_path,
                user_query=item.user_query,
            )
        )
    return fingerprints


def _collect_case_fingerprints(dataset: AskBenchmarkDataset) -> set[str]:
    fingerprints: set[str] = set()
    for case in dataset.cases:
        fingerprints.update(_case_effective_fingerprints(case))
    return fingerprints


def _collect_backlog_fingerprints(backlog: AskBenchmarkReviewBacklog) -> set[str]:
    fingerprints: set[str] = set()
    for item in backlog.items:
        fingerprints.update(_backlog_item_effective_fingerprints(item))
    return fingerprints


def _single_effective_fingerprint(
    fingerprints: set[str],
    *,
    prefix: str,
    kind: str,
    result: ValidationResult | None = None,
) -> str | None:
    if len(fingerprints) == 1:
        return next(iter(fingerprints))
    message = f"{prefix} fingerprint identity is ambiguous for the resolved locators."
    if result is not None:
        result.errors.append(message)
        return None
    raise ValueError(f"fingerprint identity is ambiguous for {kind}.")


def _load_dataset_required(path: Path) -> AskBenchmarkDataset:
    if not path.exists():
        raise FileNotFoundError(f"dataset_path {str(path)!r} does not exist.")
    return load_ask_benchmark_dataset(path)


def _load_backlog_required(path: Path) -> AskBenchmarkReviewBacklog:
    if not path.exists():
        raise FileNotFoundError(f"backlog_path {str(path)!r} does not exist.")
    return load_ask_benchmark_backlog(path)


def _write_review_outputs_atomic(
    *,
    prospective_dataset: AskBenchmarkDataset,
    prospective_backlog: AskBenchmarkReviewBacklog,
    dataset_path: Path,
    backlog_path: Path,
) -> None:
    original_dataset_text = dataset_path.read_text(encoding="utf-8")
    original_backlog_text = backlog_path.read_text(encoding="utf-8")
    try:
        write_ask_benchmark_dataset(prospective_dataset, dataset_path)
        write_ask_benchmark_backlog(prospective_backlog, backlog_path)
    except Exception:
        dataset_path.write_text(original_dataset_text, encoding="utf-8")
        backlog_path.write_text(original_backlog_text, encoding="utf-8")
        raise


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manage_ask_benchmark.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-batch", help="generate a candidate batch")
    generate_parser.add_argument("--count", type=int, default=5)
    generate_parser.add_argument("--output", type=Path, required=True)
    generate_parser.add_argument("--dataset", type=Path, default=ASK_BENCHMARK_DIR / "ask_benchmark_cases.json")
    generate_parser.add_argument(
        "--backlog",
        type=Path,
        default=ASK_BENCHMARK_DIR / "ask_benchmark_review_backlog.json",
    )
    generate_parser.add_argument("--vault-root", type=Path, default=get_settings().sample_vault_dir)
    generate_parser.set_defaults(func=_run_generate_batch)

    apply_parser = subparsers.add_parser("apply-review", help="apply review decisions")
    apply_parser.add_argument("--batch", type=Path, required=True)
    apply_parser.add_argument("--review", type=Path, required=True)
    apply_parser.add_argument("--dataset", type=Path, default=ASK_BENCHMARK_DIR / "ask_benchmark_cases.json")
    apply_parser.add_argument(
        "--backlog",
        type=Path,
        default=ASK_BENCHMARK_DIR / "ask_benchmark_review_backlog.json",
    )
    apply_parser.add_argument("--vault-root", type=Path, default=get_settings().sample_vault_dir)
    apply_parser.set_defaults(func=_run_apply_review)

    validate_parser = subparsers.add_parser("validate", help="validate the benchmark dataset")
    validate_parser.add_argument("--dataset", type=Path, default=ASK_BENCHMARK_DIR / "ask_benchmark_cases.json")
    validate_parser.add_argument(
        "--backlog",
        type=Path,
        default=ASK_BENCHMARK_DIR / "ask_benchmark_review_backlog.json",
    )
    validate_parser.add_argument("--vault-root", type=Path, default=get_settings().sample_vault_dir)
    validate_parser.set_defaults(func=_run_validate)

    return parser


def _run_generate_batch(args: argparse.Namespace) -> int:
    approved_dataset = _load_dataset_required(args.dataset)
    review_backlog = _load_backlog_required(args.backlog)
    candidates = build_candidate_batch(
        vault_root=args.vault_root,
        approved_dataset=approved_dataset,
        backlog=review_backlog,
        count=args.count,
    )
    write_candidate_batch(candidates, args.output)
    print(f"wrote {len(candidates)} candidates to {args.output}")
    return 0


def _run_apply_review(args: argparse.Namespace) -> int:
    candidates = load_candidate_batch(args.batch)
    decisions = load_review_decisions(args.review)
    result = apply_review_outcomes(
        candidate_batch=candidates,
        review_decisions=decisions,
        dataset_path=args.dataset,
        backlog_path=args.backlog,
        vault_root=args.vault_root,
    )
    print(
        "applied review outcomes: "
        f"{result.approved_count} approved, {result.backlog_count} routed to backlog, "
        f"{result.skipped_count} skipped from batch"
    )
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    result = validate_ask_benchmark_review_files(
        dataset_path=args.dataset,
        backlog_path=args.backlog,
        vault_root=args.vault_root,
    )
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("ask benchmark dataset and backlog are valid.")
    if result.warnings:
        for warning in result.warnings:
            print(f"WARNING: {warning}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    try:
        args = parser.parse_args(argv)
        return args.func(args)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
