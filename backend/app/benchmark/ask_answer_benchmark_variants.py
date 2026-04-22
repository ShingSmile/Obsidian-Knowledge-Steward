from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import ROOT_DIR
from app.context.render import (
    ASK_GROUNDED_ANSWER_PROMPT_VERSION,
    ASK_TOOL_SELECTION_PROMPT_VERSION,
)


ASK_ANSWER_BENCHMARK_DIR = ROOT_DIR / "eval" / "benchmark"
_ASK_ANSWER_BENCHMARK_SMOKE_CASES_PATH = (
    ASK_ANSWER_BENCHMARK_DIR / "ask_answer_benchmark_smoke_cases.json"
)
_ASK_ANSWER_BENCHMARK_SMOKE_CASE_COUNT = 10


@dataclass(frozen=True, slots=True)
class AskAnswerBenchmarkVariant:
    variant_id: str
    context_assembly_enabled: bool
    runtime_faithfulness_gate_enabled: bool


ANSWER_BENCHMARK_VARIANTS = (
    AskAnswerBenchmarkVariant(
        variant_id="hybrid",
        context_assembly_enabled=False,
        runtime_faithfulness_gate_enabled=False,
    ),
    AskAnswerBenchmarkVariant(
        variant_id="hybrid_assembly",
        context_assembly_enabled=True,
        runtime_faithfulness_gate_enabled=False,
    ),
    AskAnswerBenchmarkVariant(
        variant_id="hybrid_assembly_gate",
        context_assembly_enabled=True,
        runtime_faithfulness_gate_enabled=True,
    ),
)


def load_answer_benchmark_smoke_case_ids(path: Path | None = None) -> tuple[str, ...]:
    smoke_cases_path = path or _ASK_ANSWER_BENCHMARK_SMOKE_CASES_PATH
    payload = json.loads(smoke_cases_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("answer benchmark smoke subset must be a JSON object.")
    if payload.get("version") != 1:
        raise ValueError("answer benchmark smoke subset version must be 1.")

    case_ids = payload.get("case_ids")
    if not isinstance(case_ids, list):
        raise ValueError("answer benchmark smoke subset must include case_ids as a list.")

    normalized_case_ids: list[str] = []
    seen_case_ids: set[str] = set()
    for index, case_id in enumerate(case_ids):
        if not isinstance(case_id, str):
            raise ValueError(f"case_ids[{index}] must be a string.")
        normalized_case_id = case_id.strip()
        if not normalized_case_id:
            raise ValueError(f"case_ids[{index}] must not be empty.")
        if normalized_case_id in seen_case_ids:
            raise ValueError(f"case_ids[{index}] duplicates {normalized_case_id!r}.")
        seen_case_ids.add(normalized_case_id)
        normalized_case_ids.append(normalized_case_id)

    if len(normalized_case_ids) != _ASK_ANSWER_BENCHMARK_SMOKE_CASE_COUNT:
        raise ValueError(
            "answer benchmark smoke subset must contain exactly "
            f"{_ASK_ANSWER_BENCHMARK_SMOKE_CASE_COUNT} case ids."
        )

    return tuple(normalized_case_ids)


def build_answer_benchmark_metadata(
    *,
    case_id: str,
    variant: AskAnswerBenchmarkVariant,
    smoke_subset: bool,
) -> dict[str, Any]:
    return {
        "benchmark_kind": "ask_answer",
        "case_id": case_id,
        "variant_id": variant.variant_id,
        "context_assembly_enabled": variant.context_assembly_enabled,
        "runtime_faithfulness_gate_enabled": variant.runtime_faithfulness_gate_enabled,
        "smoke_subset": smoke_subset,
        "prompt_version": resolve_answer_benchmark_prompt_version(),
    }


def resolve_answer_benchmark_prompt_version() -> str:
    return "|".join(
        [
            f"tool:{ASK_TOOL_SELECTION_PROMPT_VERSION}",
            f"answer:{ASK_GROUNDED_ANSWER_PROMPT_VERSION}",
        ]
    )
