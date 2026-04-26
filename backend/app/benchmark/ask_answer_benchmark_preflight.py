from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.benchmark.ask_answer_benchmark import ANSWER_BENCHMARK_CANONICAL_MODEL
from app.benchmark.ask_answer_benchmark_judge import JudgeProviderConfig
from app.benchmark.ask_answer_benchmark_variants import load_answer_benchmark_smoke_case_ids
from app.benchmark.ask_dataset import load_ask_benchmark_dataset
from app.config import ROOT_DIR, Settings


@dataclass(frozen=True)
class AskAnswerBenchmarkPreflightResult:
    status: str
    provider_name: str | None
    model_name: str | None
    message: str


def run_answer_benchmark_preflight(
    *,
    settings: Settings,
    mode: str,
    dataset_path: Path | None = None,
    smoke_subset_path: Path | None = None,
    judge_enabled: bool = False,
    judge_provider_config: JudgeProviderConfig | None = None,
) -> AskAnswerBenchmarkPreflightResult:
    if not settings.cloud_base_url or not settings.cloud_chat_model:
        return AskAnswerBenchmarkPreflightResult(
            status="provider_not_configured",
            provider_name=None,
            model_name=None,
            message=(
                "Cloud answer benchmark provider is not configured. "
                "Set KS_CLOUD_BASE_URL and KS_CLOUD_CHAT_MODEL."
            ),
        )

    if settings.cloud_chat_model != ANSWER_BENCHMARK_CANONICAL_MODEL:
        return AskAnswerBenchmarkPreflightResult(
            status="canonical_model_mismatch",
            provider_name=settings.cloud_provider_name,
            model_name=settings.cloud_chat_model,
            message=(
                "Cloud answer benchmark model must be "
                f"{ANSWER_BENCHMARK_CANONICAL_MODEL}; got {settings.cloud_chat_model!r}."
            ),
        )

    if judge_enabled:
        if judge_provider_config is None or not judge_provider_config.base_url:
            return AskAnswerBenchmarkPreflightResult(
                status="judge_provider_not_configured",
                provider_name=None if judge_provider_config is None else judge_provider_config.provider_name,
                model_name=None if judge_provider_config is None else judge_provider_config.model_name,
                message=(
                    "Answer benchmark judge provider is not configured. "
                    "Set KS_JUDGE_BASE_URL or pass --judge-base-url."
                ),
            )
        if not judge_provider_config.model_name:
            return AskAnswerBenchmarkPreflightResult(
                status="judge_model_not_configured",
                provider_name=judge_provider_config.provider_name,
                model_name=None,
                message=(
                    "Answer benchmark judge model is not configured. "
                    "Set KS_JUDGE_MODEL or pass --judge-model."
                ),
            )

    try:
        load_ask_benchmark_dataset(dataset_path)
    except FileNotFoundError:
        return AskAnswerBenchmarkPreflightResult(
            status="dataset_not_found",
            provider_name=settings.cloud_provider_name,
            model_name=settings.cloud_chat_model,
            message=(
                "Answer benchmark dataset is not readable. "
                f"Missing dataset path: {dataset_path or 'default eval/benchmark dataset'}."
            ),
        )
    except (OSError, ValueError) as exc:
        return AskAnswerBenchmarkPreflightResult(
            status="dataset_unreadable",
            provider_name=settings.cloud_provider_name,
            model_name=settings.cloud_chat_model,
            message=f"Answer benchmark dataset is not readable: {exc}",
        )

    if mode == "smoke":
        smoke_subset_path = smoke_subset_path or (ROOT_DIR / "eval" / "benchmark" / "ask_answer_benchmark_smoke_cases.json")
        try:
            load_answer_benchmark_smoke_case_ids(smoke_subset_path)
        except FileNotFoundError:
            return AskAnswerBenchmarkPreflightResult(
                status="smoke_subset_not_found",
                provider_name=settings.cloud_provider_name,
                model_name=settings.cloud_chat_model,
                message=(
                    "Answer benchmark smoke subset is not readable. "
                    f"Missing smoke subset path: {smoke_subset_path}."
                ),
            )
        except (OSError, ValueError) as exc:
            return AskAnswerBenchmarkPreflightResult(
                status="smoke_subset_unreadable",
                provider_name=settings.cloud_provider_name,
                model_name=settings.cloud_chat_model,
                message=f"Answer benchmark smoke subset is not readable: {exc}",
            )

    return AskAnswerBenchmarkPreflightResult(
        status="ok",
        provider_name=settings.cloud_provider_name,
        model_name=settings.cloud_chat_model,
        message=(
            "Answer benchmark preflight passed for "
            f"{settings.cloud_provider_name}/{settings.cloud_chat_model}."
        ),
    )
