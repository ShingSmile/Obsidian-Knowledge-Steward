from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.config import ROOT_DIR


ASK_BENCHMARK_DIR = ROOT_DIR / "eval" / "benchmark"
_ASK_BENCHMARK_CASES_PATH = ASK_BENCHMARK_DIR / "ask_benchmark_cases.json"
_ASK_BENCHMARK_REVIEW_BACKLOG_PATH = ASK_BENCHMARK_DIR / "ask_benchmark_review_backlog.json"

_ALLOWED_BUCKETS = {
    "single_hop",
    "multi_hop",
    "metadata_filter",
    "abstain_or_no_hit",
    "tool_allowed",
}
_ALLOWED_SOURCE_ORIGINS = {"sample_vault", "fixture"}
_APPROVED_REVIEW_STATUS = "approved"
_BACKLOG_REVIEW_STATUSES = {"revise", "reject"}


def _require_non_empty_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_string_list(value: Any, field_name: str) -> list[str]:
    items = _require_list(value, field_name)
    return [_require_non_empty_text(item, field_name) for item in items]


def _require_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _read_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("top-level payload must be a JSON object")
    return payload


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass(frozen=True, slots=True)
class AskBenchmarkLocator:
    note_path: str
    heading_path: str
    excerpt_anchor: str

    def __post_init__(self) -> None:
        _require_non_empty_text(self.note_path, "note_path")
        _require_non_empty_text(self.heading_path, "heading_path")
        _require_non_empty_text(self.excerpt_anchor, "excerpt_anchor")

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_path": self.note_path,
            "heading_path": self.heading_path,
            "excerpt_anchor": self.excerpt_anchor,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkLocator":
        return cls(
            note_path=payload["note_path"],
            heading_path=payload["heading_path"],
            excerpt_anchor=payload["excerpt_anchor"],
        )


@dataclass(frozen=True, slots=True)
class AskBenchmarkCase:
    case_id: str
    bucket: str
    user_query: str
    source_origin: str
    expected_relevant_paths: list[str] = field(default_factory=list)
    expected_relevant_locators: list[AskBenchmarkLocator] = field(default_factory=list)
    expected_facts: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    allow_tool: bool = False
    expected_tool_names: list[str] = field(default_factory=list)
    allow_retrieval_only: bool = False
    should_generate_answer: bool = True
    review_status: str = _APPROVED_REVIEW_STATUS
    review_notes: str = ""

    def __post_init__(self) -> None:
        _require_non_empty_text(self.case_id, "case_id")
        if self.bucket not in _ALLOWED_BUCKETS:
            raise ValueError("bucket must be one of the allowed ask benchmark buckets")
        _require_non_empty_text(self.user_query, "user_query")
        if self.source_origin not in _ALLOWED_SOURCE_ORIGINS:
            raise ValueError("source_origin must be sample_vault or fixture")
        self._validate_lists()
        _require_bool(self.allow_tool, "allow_tool")
        _require_bool(self.allow_retrieval_only, "allow_retrieval_only")
        _require_bool(self.should_generate_answer, "should_generate_answer")
        if self.review_status != _APPROVED_REVIEW_STATUS:
            raise ValueError("review_status must be approved for the formal dataset")

    def _validate_lists(self) -> None:
        _require_string_list(self.expected_relevant_paths, "expected_relevant_paths")
        locators = _require_list(self.expected_relevant_locators, "expected_relevant_locators")
        for locator in locators:
            if not isinstance(locator, AskBenchmarkLocator):
                raise ValueError("expected_relevant_locators must contain AskBenchmarkLocator values")
        _require_string_list(self.expected_facts, "expected_facts")
        _require_string_list(self.forbidden_claims, "forbidden_claims")
        _require_string_list(self.expected_tool_names, "expected_tool_names")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected_relevant_locators"] = [locator.to_dict() for locator in self.expected_relevant_locators]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkCase":
        if "review_status" not in payload:
            raise ValueError("review_status is required for formal dataset cases")
        return cls(
            case_id=payload["case_id"],
            bucket=payload["bucket"],
            user_query=payload["user_query"],
            source_origin=payload["source_origin"],
            expected_relevant_paths=list(payload.get("expected_relevant_paths", [])),
            expected_relevant_locators=[
                AskBenchmarkLocator.from_dict(locator) for locator in payload.get("expected_relevant_locators", [])
            ],
            expected_facts=list(payload.get("expected_facts", [])),
            forbidden_claims=list(payload.get("forbidden_claims", [])),
            allow_tool=payload["allow_tool"],
            expected_tool_names=list(payload.get("expected_tool_names", [])),
            allow_retrieval_only=payload["allow_retrieval_only"],
            should_generate_answer=payload["should_generate_answer"],
            review_status=payload["review_status"],
            review_notes=payload.get("review_notes", ""),
        )


@dataclass(frozen=True, slots=True)
class AskBenchmarkBacklogItem:
    case_id: str
    bucket: str
    user_query: str
    source_origin: str
    expected_relevant_paths: list[str] = field(default_factory=list)
    expected_relevant_locators: list[AskBenchmarkLocator] = field(default_factory=list)
    expected_facts: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    allow_tool: bool = False
    expected_tool_names: list[str] = field(default_factory=list)
    allow_retrieval_only: bool = False
    should_generate_answer: bool = True
    review_status: str = "revise"
    review_notes: str = ""

    def __post_init__(self) -> None:
        _require_non_empty_text(self.case_id, "case_id")
        if self.bucket not in _ALLOWED_BUCKETS:
            raise ValueError("bucket must be one of the allowed ask benchmark buckets")
        _require_non_empty_text(self.user_query, "user_query")
        if self.source_origin not in _ALLOWED_SOURCE_ORIGINS:
            raise ValueError("source_origin must be sample_vault or fixture")
        self._validate_lists()
        _require_bool(self.allow_tool, "allow_tool")
        _require_bool(self.allow_retrieval_only, "allow_retrieval_only")
        _require_bool(self.should_generate_answer, "should_generate_answer")
        if self.review_status not in _BACKLOG_REVIEW_STATUSES:
            raise ValueError("review_status must be revise or reject for backlog items")

    def _validate_lists(self) -> None:
        _require_string_list(self.expected_relevant_paths, "expected_relevant_paths")
        locators = _require_list(self.expected_relevant_locators, "expected_relevant_locators")
        for locator in locators:
            if not isinstance(locator, AskBenchmarkLocator):
                raise ValueError("expected_relevant_locators must contain AskBenchmarkLocator values")
        _require_string_list(self.expected_facts, "expected_facts")
        _require_string_list(self.forbidden_claims, "forbidden_claims")
        _require_string_list(self.expected_tool_names, "expected_tool_names")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["expected_relevant_locators"] = [locator.to_dict() for locator in self.expected_relevant_locators]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkBacklogItem":
        return cls(
            case_id=payload["case_id"],
            bucket=payload["bucket"],
            user_query=payload["user_query"],
            source_origin=payload["source_origin"],
            expected_relevant_paths=list(payload.get("expected_relevant_paths", [])),
            expected_relevant_locators=[
                AskBenchmarkLocator.from_dict(locator) for locator in payload.get("expected_relevant_locators", [])
            ],
            expected_facts=list(payload.get("expected_facts", [])),
            forbidden_claims=list(payload.get("forbidden_claims", [])),
            allow_tool=payload["allow_tool"],
            expected_tool_names=list(payload.get("expected_tool_names", [])),
            allow_retrieval_only=payload["allow_retrieval_only"],
            should_generate_answer=payload["should_generate_answer"],
            review_status=payload.get("review_status", "revise"),
            review_notes=payload.get("review_notes", ""),
        )


@dataclass(frozen=True, slots=True)
class AskBenchmarkDataset:
    schema_version: int = 1
    cases: list[AskBenchmarkCase] = field(default_factory=list)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        cases = _require_list(self.cases, "cases")
        for case in cases:
            if not isinstance(case, AskBenchmarkCase):
                raise ValueError("cases must contain AskBenchmarkCase values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cases": [case.to_dict() for case in self.cases],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkDataset":
        if set(payload.keys()) != {"schema_version", "cases"}:
            raise ValueError("ask benchmark dataset must contain only schema_version and cases")
        return cls(
            schema_version=payload["schema_version"],
            cases=[AskBenchmarkCase.from_dict(case) for case in payload["cases"]],
        )


@dataclass(frozen=True, slots=True)
class AskBenchmarkReviewBacklog:
    schema_version: int = 1
    items: list[AskBenchmarkBacklogItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        items = _require_list(self.items, "items")
        for item in items:
            if not isinstance(item, AskBenchmarkBacklogItem):
                raise ValueError("items must contain AskBenchmarkBacklogItem values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AskBenchmarkReviewBacklog":
        if set(payload.keys()) != {"schema_version", "items"}:
            raise ValueError("ask benchmark review backlog must contain only schema_version and items")
        return cls(
            schema_version=payload["schema_version"],
            items=[AskBenchmarkBacklogItem.from_dict(item) for item in payload["items"]],
        )


def load_ask_benchmark_dataset(path: Path | None = None) -> AskBenchmarkDataset:
    dataset_path = path or _ASK_BENCHMARK_CASES_PATH
    return AskBenchmarkDataset.from_dict(_read_json_file(dataset_path))


def write_ask_benchmark_dataset(dataset: AskBenchmarkDataset, path: Path | None = None) -> None:
    dataset_path = path or _ASK_BENCHMARK_CASES_PATH
    _write_json_file(dataset_path, dataset.to_dict())


def load_ask_benchmark_backlog(path: Path | None = None) -> AskBenchmarkReviewBacklog:
    backlog_path = path or _ASK_BENCHMARK_REVIEW_BACKLOG_PATH
    return AskBenchmarkReviewBacklog.from_dict(_read_json_file(backlog_path))


def write_ask_benchmark_backlog(backlog: AskBenchmarkReviewBacklog, path: Path | None = None) -> None:
    backlog_path = path or _ASK_BENCHMARK_REVIEW_BACKLOG_PATH
    _write_json_file(backlog_path, backlog.to_dict())
