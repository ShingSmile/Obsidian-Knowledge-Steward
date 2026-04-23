from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime
import json
import subprocess
from pathlib import Path
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from app.benchmark.ask_answer_benchmark_scoring import (
    aggregate_answer_benchmark_variant_scores,
    score_answer_benchmark_case,
)
from app.benchmark.ask_answer_benchmark_variants import (
    ANSWER_BENCHMARK_VARIANTS,
    build_answer_benchmark_metadata,
    load_answer_benchmark_smoke_case_ids,
    resolve_answer_benchmark_prompt_version,
)
from app.benchmark.ask_dataset import AskBenchmarkCase, AskBenchmarkDataset, load_ask_benchmark_dataset
from app.config import ROOT_DIR, Settings
from app.contracts.workflow import WorkflowAction, WorkflowInvokeRequest
from app.graphs.ask_graph import invoke_ask_graph


ANSWER_BENCHMARK_SCHEMA_VERSION = 1
ANSWER_BENCHMARK_KIND = "ask_answer"
ANSWER_BENCHMARK_MODES = ("smoke", "full")
ANSWER_BENCHMARK_SMOKE_SUBSET_VERSION = 1
ANSWER_BENCHMARK_CANONICAL_MODEL = "qwen3.6-flash-2026-04-16"


def build_default_output_path(results_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return results_dir / f"answer-benchmark-{timestamp}.json"


def write_answer_benchmark_result(result: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def run_ask_answer_benchmark(
    settings: Settings,
    mode: Literal["smoke", "full"],
    dataset_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    if mode not in ANSWER_BENCHMARK_MODES:
        raise ValueError(f"unsupported answer benchmark mode: {mode!r}")

    dataset = load_ask_benchmark_dataset(dataset_path)
    selected_cases = _select_cases(dataset, mode)
    benchmark_settings = replace(
        settings,
        cloud_chat_model=ANSWER_BENCHMARK_CANONICAL_MODEL,
        local_chat_model="",
    )

    selected_case_ids = [case.case_id for case in selected_cases]
    smoke_subset = mode == "smoke"
    run_timestamp = datetime.now().isoformat(timespec="seconds")
    git_commit = _get_git_commit()
    worktree_dirty = _is_worktree_dirty()

    case_variant_records: list[dict[str, Any]] = []
    variant_scores: dict[str, list[Any]] = {variant.variant_id: [] for variant in ANSWER_BENCHMARK_VARIANTS}
    provider_name: str | None = None
    model_name: str | None = None

    for case in selected_cases:
        for variant in ANSWER_BENCHMARK_VARIANTS:
            request = WorkflowInvokeRequest(
                action_type=WorkflowAction.ASK_QA,
                user_query=case.user_query,
                provider_preference="cloud",
                metadata=build_answer_benchmark_metadata(
                    case_id=case.case_id,
                    variant=variant,
                    smoke_subset=smoke_subset,
                ),
            )
            execution_token = uuid4().hex
            thread_id = (
                f"task059_{case.case_id}_{variant.variant_id}_{execution_token}"
            )
            run_id = f"{thread_id}_run"
            start_time = perf_counter()
            execution = invoke_ask_graph(
                request,
                settings=benchmark_settings,
                thread_id=thread_id,
                run_id=run_id,
            )
            latency_ms = max(0, int((perf_counter() - start_time) * 1000))
            ask_result = execution.ask_result

            if provider_name is None:
                provider_name = ask_result.provider_name or benchmark_settings.cloud_provider_name
            if model_name is None:
                model_name = ask_result.model_name or benchmark_settings.cloud_chat_model

            case_score = score_answer_benchmark_case(
                case=case,
                ask_result=ask_result,
                latency_ms=latency_ms,
                variant_id=variant.variant_id,
            )
            variant_scores[variant.variant_id].append(case_score)
            case_variant_records.append(
                {
                    "case_id": case.case_id,
                    "bucket": case.bucket,
                    "allow_tool": case.allow_tool,
                    "variant_id": variant.variant_id,
                    "ask_result_mode": ask_result.mode.value,
                    "answer_text": ask_result.answer,
                    "citations": [
                        citation.model_dump(mode="json", exclude_none=True)
                        for citation in ask_result.citations
                    ],
                    "guardrail_action": (
                        ask_result.guardrail_action.value if ask_result.guardrail_action is not None else None
                    ),
                    "runtime_faithfulness": (
                        ask_result.runtime_faithfulness.model_dump(mode="json", exclude_none=True)
                        if ask_result.runtime_faithfulness is not None
                        else None
                    ),
                    "provider_name": ask_result.provider_name,
                    "model_name": ask_result.model_name,
                    "latency_ms": latency_ms,
                    "matched_expected_facts": case_score.matched_expected_facts,
                    "missed_expected_facts": case_score.missed_expected_facts,
                    "forbidden_claim_hits": case_score.forbidden_claim_hits,
                    "final_verdict": case_score.verdict,
                }
            )

    variant_aggregates: dict[str, dict[str, Any]] = {}
    for variant in ANSWER_BENCHMARK_VARIANTS:
        aggregate = aggregate_answer_benchmark_variant_scores(
            variant_id=variant.variant_id,
            case_scores=variant_scores[variant.variant_id],
        )
        aggregate_payload = asdict(aggregate)
        if smoke_subset:
            aggregate_payload.pop("tool_trigger_rate", None)
            aggregate_payload.pop("expected_tool_hit_rate", None)
            aggregate_payload.pop("tool_case_answer_correctness", None)
        else:
            tool_case_scores = [
                case_score
                for case_score in variant_scores[variant.variant_id]
                if case_score.allow_tool
            ]
            aggregate_payload["tool_allowed"] = {
                "tool_trigger_rate": _rounded_ratio(
                    sum(1 for case_score in tool_case_scores if case_score.tool_call_attempted),
                    len(tool_case_scores),
                ),
                "expected_tool_hit_rate": _rounded_ratio(
                    sum(
                        1
                        for case_score in tool_case_scores
                        if case_score.tool_call_used is not None
                        and case_score.tool_call_used in case_score.expected_tool_names
                    ),
                    len(tool_case_scores),
                ),
                "tool_case_answer_correctness": _rounded_ratio(
                    sum(case_score.correctness_points for case_score in tool_case_scores),
                    len(tool_case_scores),
                ),
            }
        variant_aggregates[variant.variant_id] = aggregate_payload

    result: dict[str, Any] = {
        "schema_version": ANSWER_BENCHMARK_SCHEMA_VERSION,
        "benchmark_kind": ANSWER_BENCHMARK_KIND,
        "benchmark_mode": mode,
        "dataset_version": dataset.schema_version,
        "run_timestamp": run_timestamp,
        "git_commit": git_commit,
        "provider_name": provider_name or benchmark_settings.cloud_provider_name,
        "model_name": model_name or benchmark_settings.cloud_chat_model,
        "prompt_version": resolve_answer_benchmark_prompt_version(),
        "worktree_dirty": worktree_dirty,
        "selected_case_count": len(selected_cases),
        "selected_case_ids": selected_case_ids,
        "case_variant_records": case_variant_records,
        "variant_aggregates": variant_aggregates,
        "run_status": "passed",
    }
    if smoke_subset:
        result["smoke_subset_version"] = ANSWER_BENCHMARK_SMOKE_SUBSET_VERSION

    result["artifact_metadata"] = {
        key: result[key]
        for key in (
            "schema_version",
            "benchmark_kind",
            "benchmark_mode",
            "dataset_version",
            "provider_name",
            "model_name",
            "run_timestamp",
            "git_commit",
            "prompt_version",
            "worktree_dirty",
            "selected_case_count",
            "selected_case_ids",
        )
    }
    if smoke_subset:
        result["artifact_metadata"]["smoke_subset_version"] = ANSWER_BENCHMARK_SMOKE_SUBSET_VERSION

    artifact_path = output_path or build_default_output_path(ROOT_DIR / "eval" / "results")
    write_answer_benchmark_result(result, artifact_path)
    return result


def _select_cases(dataset: AskBenchmarkDataset, mode: str) -> list[AskBenchmarkCase]:
    if mode == "full":
        return list(dataset.cases)

    smoke_case_ids = load_answer_benchmark_smoke_case_ids()
    cases_by_id = {case.case_id: case for case in dataset.cases}
    selected_cases = [cases_by_id[case_id] for case_id in smoke_case_ids if case_id in cases_by_id]
    if len(selected_cases) != len(smoke_case_ids):
        missing_case_ids = [case_id for case_id in smoke_case_ids if case_id not in cases_by_id]
        raise RuntimeError(
            "answer benchmark smoke subset contains case ids missing from the dataset: "
            f"{missing_case_ids}"
        )
    return selected_cases


def _get_git_commit() -> str:
    try:
        completed_process = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "unknown"
    commit = completed_process.stdout.strip()
    return commit or "unknown"


def _is_worktree_dirty() -> bool:
    try:
        completed_process = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return True
    return bool(completed_process.stdout.strip())


def _rounded_ratio(numerator: float, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
