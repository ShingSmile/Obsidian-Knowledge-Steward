from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from app.benchmark.ask_answer_benchmark import (
    ANSWER_BENCHMARK_KIND,
    write_answer_benchmark_result,
)
from app.benchmark.ask_answer_benchmark_judge import (
    JUDGE_PROMPT_VERSION,
    JudgeCitation,
    JudgeInput,
    JudgeProviderConfig,
    JudgeScore,
    aggregate_judge_scores,
    build_non_scored_judge_score,
    judge_score_to_payload,
    score_answer_with_judge,
)
from app.benchmark.ask_dataset import AskBenchmarkCase, load_ask_benchmark_dataset


_REQUIRED_RECORD_FIELDS = ("case_id", "variant_id", "answer_text", "citations")


@dataclass(frozen=True)
class _NormalizedRecord:
    case_id: str | None
    variant_id: str | None
    answer_text: str | None
    citations: list[Any] | None
    has_required_values: bool


def load_answer_benchmark_artifact(path: Path) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        raise ValueError("answer benchmark artifact must be a JSON object")
    if artifact.get("benchmark_kind") != ANSWER_BENCHMARK_KIND:
        raise ValueError(f"answer benchmark artifact must have benchmark_kind={ANSWER_BENCHMARK_KIND!r}")
    return artifact


def write_answer_benchmark_artifact(result: dict[str, Any], path: Path) -> Path:
    return write_answer_benchmark_result(result, path)


def judge_answer_benchmark_artifact(
    input_path: Path,
    output_path: Path,
    settings: object,
    *,
    dataset_path: Path | None = None,
    judge_provider_config: JudgeProviderConfig,
) -> dict[str, Any]:
    del settings
    artifact = load_answer_benchmark_artifact(input_path)
    dataset = load_ask_benchmark_dataset(dataset_path)
    result = deepcopy(artifact)

    records = result.get("case_variant_records")
    if not isinstance(records, list):
        raise ValueError("answer benchmark artifact must contain case_variant_records list")
    variant_aggregates = result.setdefault("variant_aggregates", {})
    if not isinstance(variant_aggregates, dict):
        raise ValueError("answer benchmark artifact variant_aggregates must be an object")

    warnings: list[dict[str, Any]] = []
    artifact_dataset_version = result.get("dataset_version")
    if artifact_dataset_version != dataset.schema_version:
        warnings.append(
            {
                "code": "dataset_version_mismatch",
                "artifact_dataset_version": artifact_dataset_version,
                "current_dataset_version": dataset.schema_version,
            }
        )

    result["judge_run_metadata"] = {
        "judge_enabled": True,
        "judge_provider_name": judge_provider_config.provider_name,
        "judge_model_name": judge_provider_config.model_name,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "judge_run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "source_artifact_path": str(input_path),
        "warnings": warnings,
    }

    cases_by_id = {case.case_id: case for case in dataset.cases}
    judge_scores_by_variant: dict[str, list[JudgeScore]] = {}

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("answer benchmark case_variant_records entries must be objects")

        normalized_record = _normalize_record(record)
        score = _judge_record(
            record=record,
            normalized_record=normalized_record,
            cases_by_id=cases_by_id,
            judge_provider_config=judge_provider_config,
        )
        record["judge_score"] = judge_score_to_payload(score)

        if normalized_record.variant_id is not None:
            judge_scores_by_variant.setdefault(normalized_record.variant_id, []).append(score)

    for variant_id in judge_scores_by_variant:
        variant_aggregates.setdefault(variant_id, {})

    for variant_id, aggregate in variant_aggregates.items():
        if not isinstance(aggregate, dict):
            raise ValueError("answer benchmark variant aggregate entries must be objects")
        _backfill_rule_aggregate_aliases(aggregate)
        aggregate.update(aggregate_judge_scores(judge_scores_by_variant.get(str(variant_id), [])))

    write_answer_benchmark_artifact(result, output_path)
    return result


def _judge_record(
    *,
    record: dict[str, Any],
    normalized_record: _NormalizedRecord,
    cases_by_id: dict[str, AskBenchmarkCase],
    judge_provider_config: JudgeProviderConfig,
) -> JudgeScore:
    if not normalized_record.has_required_values:
        return build_non_scored_judge_score(
            "skipped_missing_record_fields",
            "missing_record_fields",
        )

    case_id = normalized_record.case_id
    variant_id = normalized_record.variant_id
    answer_text = normalized_record.answer_text
    citations = normalized_record.citations
    if case_id is None or variant_id is None or answer_text is None or citations is None:
        return build_non_scored_judge_score(
            "skipped_missing_record_fields",
            "missing_record_fields",
        )

    case = cases_by_id.get(case_id)
    if case is None:
        return build_non_scored_judge_score(
            "skipped_missing_dataset_case",
            "missing_dataset_case",
        )

    judge_input = JudgeInput(
        case_id=case_id,
        variant_id=variant_id,
        user_query=case.user_query,
        expected_facts=list(case.expected_facts),
        forbidden_claims=list(case.forbidden_claims),
        answer_text=answer_text,
        citations=_build_judge_citations(citations),
        ask_result_mode=str(record.get("ask_result_mode", "")),
        runtime_faithfulness=record.get("runtime_faithfulness"),
    )
    return score_answer_with_judge(judge_input, judge_provider_config)


def _normalize_record(record: dict[str, Any]) -> _NormalizedRecord:
    case_id = _normalized_non_blank_string(record.get("case_id"))
    variant_id = _normalized_non_blank_string(record.get("variant_id"))
    answer_text_value = record.get("answer_text")
    citations_value = record.get("citations")
    answer_text = answer_text_value if isinstance(answer_text_value, str) else None
    citations = citations_value if isinstance(citations_value, list) else None
    return _NormalizedRecord(
        case_id=case_id,
        variant_id=variant_id,
        answer_text=answer_text,
        citations=citations,
        has_required_values=(
            all(field in record for field in _REQUIRED_RECORD_FIELDS)
            and case_id is not None
            and variant_id is not None
            and answer_text is not None
            and citations is not None
        ),
    )


def _normalized_non_blank_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _build_judge_citations(citations_payload: object) -> list[JudgeCitation]:
    if not isinstance(citations_payload, list):
        return []

    citations: list[JudgeCitation] = []
    for index, citation_payload in enumerate(citations_payload, start=1):
        citation = citation_payload if isinstance(citation_payload, dict) else {}
        citations.append(
            JudgeCitation(
                citation_id=str(citation.get("citation_id") or citation.get("chunk_id") or index),
                source_path=str(citation.get("source_path") or citation.get("path") or ""),
                snippet=str(citation.get("snippet") or ""),
            )
        )
    return citations


def _backfill_rule_aggregate_aliases(aggregate: dict[str, Any]) -> None:
    if "rule_answer_correctness" not in aggregate and "answer_correctness" in aggregate:
        aggregate["rule_answer_correctness"] = aggregate["answer_correctness"]
    if "rule_unsupported_claim_rate" not in aggregate and "unsupported_claim_rate" in aggregate:
        aggregate["rule_unsupported_claim_rate"] = aggregate["unsupported_claim_rate"]
