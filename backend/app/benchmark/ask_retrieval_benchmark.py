from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from app.benchmark.ask_dataset import AskBenchmarkCase, AskBenchmarkDataset, load_ask_benchmark_dataset
from app.benchmark.ask_retrieval_metrics import compute_case_mode_metrics, compute_mode_summary
from app.benchmark.ask_retrieval_modes import (
    RETRIEVAL_BENCHMARK_LIMIT,
    RetrievalBenchmarkMode,
    RetrievalBenchmarkModeError,
    run_retrieval_mode,
)
from app.config import ROOT_DIR, Settings
from app.indexing.store import connect_sqlite, initialize_index_db


TASK_058_V1_SCHEMA_VERSION = 1
TASK_058_V1_BENCHMARK_KIND = "ask_retrieval"
_TASK_058_V1_ALLOWED_BUCKETS = {
    "single_hop",
    "multi_hop",
    "metadata_filter",
}
_TASK_058_V1_MODES = (
    RetrievalBenchmarkMode.FTS_ONLY,
    RetrievalBenchmarkMode.VECTOR_ONLY,
    RetrievalBenchmarkMode.HYBRID_RRF,
)


def select_task_058_v1_cases(
    dataset: AskBenchmarkDataset,
) -> tuple[list[AskBenchmarkCase], list[dict[str, str]]]:
    selected_cases: list[AskBenchmarkCase] = []
    excluded_cases: list[dict[str, str]] = []

    for case in dataset.cases:
        if case.allow_tool:
            excluded_cases.append(
                {
                    "case_id": case.case_id,
                    "bucket": case.bucket,
                    "exclusion_reason": "allow_tool=true",
                }
            )
            continue
        if case.bucket not in _TASK_058_V1_ALLOWED_BUCKETS:
            excluded_cases.append(
                {
                    "case_id": case.case_id,
                    "bucket": case.bucket,
                    "exclusion_reason": "bucket_not_in_task_058_v1",
                }
            )
            continue
        selected_cases.append(case)

    return selected_cases, excluded_cases


def build_default_output_path(results_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return results_dir / f"retrieval-benchmark-{timestamp}.json"


def write_retrieval_benchmark_result(result: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def run_ask_retrieval_benchmark(
    settings: Settings,
    dataset_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    dataset = load_ask_benchmark_dataset(dataset_path)
    selected_cases, excluded_cases = select_task_058_v1_cases(dataset)
    if not selected_cases:
        raise RuntimeError("Task 058 retrieval benchmark selected zero eligible cases.")

    selected_case_count = len(selected_cases)
    result: dict[str, Any] = {
        "schema_version": TASK_058_V1_SCHEMA_VERSION,
        "benchmark_kind": TASK_058_V1_BENCHMARK_KIND,
        "run_status": "passed",
        "dataset_schema_version": dataset.schema_version,
        "selected_case_count": selected_case_count,
        "selected_case_ids": [case.case_id for case in selected_cases],
        "excluded_cases": excluded_cases,
        "modes": {
            mode.value: {
                "status": "pending",
                "selected_case_count": selected_case_count,
            }
            for mode in _TASK_058_V1_MODES
        },
        "cases": [
            {
                "case_id": case.case_id,
                "bucket": case.bucket,
                "user_query": case.user_query,
                "expected_locators": [locator.to_dict() for locator in case.expected_relevant_locators],
                "mode_results": [],
            }
            for case in selected_cases
        ],
    }

    completed_modes: list[str] = []
    case_metrics_by_mode: dict[str, list[dict[str, object]]] = {}
    initialized_db_path = initialize_index_db(settings.index_db_path, settings=settings)
    connection = connect_sqlite(initialized_db_path)

    try:
        for mode_index, mode in enumerate(_TASK_058_V1_MODES):
            mode_key = mode.value
            mode_case_metrics: list[dict[str, object]] = []
            pending_mode_results: list[dict[str, object]] = []
            try:
                for case in selected_cases:
                    candidates = run_retrieval_mode(
                        connection=connection,
                        query=case.user_query,
                        settings=settings,
                        mode=mode,
                    )
                    case_metrics = compute_case_mode_metrics(case.expected_relevant_locators, candidates)
                    mode_case_metrics.append(case_metrics)
                    pending_mode_results.append(
                        {
                            "mode": mode_key,
                            "top_k": RETRIEVAL_BENCHMARK_LIMIT,
                            "retrieved_candidates": [
                                candidate.model_dump(mode="json", exclude_none=True) for candidate in candidates
                            ],
                            **case_metrics,
                        }
                    )
            except RetrievalBenchmarkModeError as exc:
                result["run_status"] = "failed"
                for completed_mode in completed_modes:
                    result["modes"][completed_mode]["status"] = "completed_before_failure"
                    result["modes"][completed_mode]["failure_reason"] = (
                        f"mode completed before benchmark stopped on {mode_key} failure"
                    )
                result["modes"][mode_key]["status"] = "failed"
                result["modes"][mode_key]["failure_reason"] = str(exc)
                for remaining_mode in _TASK_058_V1_MODES[mode_index + 1 :]:
                    result["modes"][remaining_mode.value]["status"] = "not_run"
                    result["modes"][remaining_mode.value][
                        "failure_reason"
                    ] = "benchmark stopped after mode failure"
                break

            for case_record, mode_result in zip(result["cases"], pending_mode_results, strict=True):
                case_record["mode_results"].append(mode_result)

            completed_modes.append(mode_key)
            case_metrics_by_mode[mode_key] = mode_case_metrics

        if result["run_status"] == "passed":
            for mode_key, case_metrics in case_metrics_by_mode.items():
                result["modes"][mode_key]["status"] = "passed"
                result["modes"][mode_key]["summary_metrics"] = compute_mode_summary(case_metrics)
    finally:
        connection.close()

    artifact_path = output_path or build_default_output_path(ROOT_DIR / "eval" / "results")
    write_retrieval_benchmark_result(result, artifact_path)
    return result
