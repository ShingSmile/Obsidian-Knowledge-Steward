from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.config import ROOT_DIR


ASK_BENCHMARK_DIR = ROOT_DIR / "eval" / "benchmark"
_ASK_BENCHMARK_CASES_PATH = ASK_BENCHMARK_DIR / "ask_benchmark_cases.json"
_ASK_BENCHMARK_REVIEW_BACKLOG_PATH = ASK_BENCHMARK_DIR / "ask_benchmark_review_backlog.json"

AskBenchmarkBucket = Literal[
    "single_hop",
    "multi_hop",
    "metadata_filter",
    "abstain_or_no_hit",
    "tool_allowed",
]
AskBenchmarkSourceOrigin = Literal["sample_vault", "fixture"]
AskBenchmarkApprovedReviewStatus = Literal["approved"]
AskBenchmarkBacklogReviewStatus = Literal["revise", "reject"]
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class AskBenchmarkLocator(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    note_path: NonEmptyStr
    heading_path: NonEmptyStr
    line_range: dict[str, int] | None = None
    excerpt_anchor: NonEmptyStr

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkLocator":
        return cls.model_validate(payload)


class AskBenchmarkCase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    case_id: NonEmptyStr
    bucket: AskBenchmarkBucket
    user_query: NonEmptyStr
    source_origin: AskBenchmarkSourceOrigin
    expected_relevant_paths: list[NonEmptyStr]
    expected_relevant_locators: list[AskBenchmarkLocator]
    expected_facts: list[NonEmptyStr]
    forbidden_claims: list[NonEmptyStr]
    allow_tool: bool
    expected_tool_names: list[NonEmptyStr]
    allow_retrieval_only: bool
    should_generate_answer: bool
    review_status: AskBenchmarkApprovedReviewStatus
    review_notes: str

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkCase":
        return cls.model_validate(payload)


class AskBenchmarkBacklogItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    case_id: NonEmptyStr
    fingerprint: NonEmptyStr
    bucket: AskBenchmarkBucket
    user_query: NonEmptyStr
    source_origin: AskBenchmarkSourceOrigin
    expected_relevant_paths: list[NonEmptyStr]
    expected_relevant_locators: list[AskBenchmarkLocator]
    expected_facts: list[NonEmptyStr]
    forbidden_claims: list[NonEmptyStr]
    allow_tool: bool
    expected_tool_names: list[NonEmptyStr]
    allow_retrieval_only: bool
    should_generate_answer: bool
    review_status: AskBenchmarkBacklogReviewStatus
    review_notes: str

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkBacklogItem":
        return cls.model_validate(payload)


class AskBenchmarkDataset(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    cases: list[AskBenchmarkCase]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkDataset":
        return cls.model_validate(payload)


class AskBenchmarkReviewBacklog(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    items: list[AskBenchmarkBacklogItem]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkReviewBacklog":
        return cls.model_validate(payload)


def load_ask_benchmark_dataset(path: Path | None = None) -> AskBenchmarkDataset:
    dataset_path = path or _ASK_BENCHMARK_CASES_PATH
    return AskBenchmarkDataset.model_validate_json(dataset_path.read_text(encoding="utf-8"))


def write_ask_benchmark_dataset(dataset: AskBenchmarkDataset, path: Path | None = None) -> None:
    dataset_path = path or _ASK_BENCHMARK_CASES_PATH
    _write_json_file(dataset_path, dataset.to_dict())


def load_ask_benchmark_backlog(path: Path | None = None) -> AskBenchmarkReviewBacklog:
    backlog_path = path or _ASK_BENCHMARK_REVIEW_BACKLOG_PATH
    return AskBenchmarkReviewBacklog.model_validate_json(backlog_path.read_text(encoding="utf-8"))


def write_ask_benchmark_backlog(backlog: AskBenchmarkReviewBacklog, path: Path | None = None) -> None:
    backlog_path = path or _ASK_BENCHMARK_REVIEW_BACKLOG_PATH
    _write_json_file(backlog_path, backlog.to_dict())
