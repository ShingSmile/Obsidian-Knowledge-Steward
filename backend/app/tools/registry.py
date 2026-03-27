from __future__ import annotations

from app.config import Settings
from app.contracts.workflow import (
    GuardrailAction,
    GuardrailOutcome,
    ToolCallDecision,
    ToolExecutionResult,
    ToolSpec,
    WorkflowAction,
)
from app.tools.ask_tools import (
    execute_find_backlinks,
    execute_get_note_outline,
    execute_list_pending_approvals,
    execute_load_note_excerpt,
    execute_search_notes,
)


TOOL_REGISTRY: dict[str, ToolSpec] = {
    "search_notes": ToolSpec(
        name="search_notes",
        purpose="Search indexed notes for relevant excerpts.",
        allowed_workflows=[WorkflowAction.ASK_QA],
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {"type": "object"},
                }
            },
            "required": ["results"],
        },
        risk_level="low",
        read_only=True,
    ),
    "load_note_excerpt": ToolSpec(
        name="load_note_excerpt",
        purpose="Load a bounded excerpt from a note in the sample vault.",
        allowed_workflows=[WorkflowAction.ASK_QA],
        input_schema={
            "type": "object",
            "properties": {
                "note_path": {"type": "string"},
                "max_chars": {"type": "integer", "minimum": 1, "maximum": 4000},
            },
            "required": ["note_path"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "note_path": {"type": "string"},
                "excerpt": {"type": "string"},
                "line_count": {"type": "integer"},
            },
            "required": ["note_path", "excerpt", "line_count"],
        },
        risk_level="low",
        read_only=True,
    ),
    "get_note_outline": ToolSpec(
        name="get_note_outline",
        purpose="Read the current heading tree from a note on disk.",
        allowed_workflows=[WorkflowAction.ASK_QA],
        input_schema={
            "type": "object",
            "properties": {
                "note_path": {"type": "string"},
            },
            "required": ["note_path"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "note_path": {"type": "string"},
                "title": {"type": "string"},
                "has_frontmatter": {"type": "boolean"},
                "frontmatter_summary": {
                    "type": "object",
                    "properties": {
                        "raw_text": {"type": "string"},
                        "line_count": {"type": "integer"},
                        "char_count": {"type": "integer"},
                    },
                },
                "headings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "level": {"type": "integer"},
                            "text": {"type": "string"},
                            "line_no": {"type": "integer"},
                            "heading_path": {"type": "string"},
                        },
                        "required": ["level", "text", "line_no", "heading_path"],
                    },
                },
            },
            "required": ["note_path", "title", "has_frontmatter", "frontmatter_summary", "headings"],
        },
        risk_level="low",
        read_only=True,
    ),
    "find_backlinks": ToolSpec(
        name="find_backlinks",
        purpose="Find verified backlinks to a note from the SQLite index.",
        allowed_workflows=[WorkflowAction.ASK_QA],
        input_schema={
            "type": "object",
            "properties": {
                "note_path": {"type": "string"},
            },
            "required": ["note_path"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "target_path": {"type": "string"},
                "backlinks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_path": {"type": "string"},
                            "chunk_id": {"type": "string"},
                            "heading_path": {"type": ["string", "null"]},
                            "start_line": {"type": "integer"},
                            "end_line": {"type": "integer"},
                            "link_text": {"type": "string"},
                        },
                        "required": [
                            "source_path",
                            "chunk_id",
                            "heading_path",
                            "start_line",
                            "end_line",
                            "link_text",
                        ],
                    },
                },
            },
            "required": ["target_path", "backlinks"],
        },
        risk_level="low",
        read_only=True,
    ),
    "list_pending_approvals": ToolSpec(
        name="list_pending_approvals",
        purpose="List currently pending approval items.",
        allowed_workflows=[WorkflowAction.ASK_QA],
        input_schema={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["items"],
        },
        risk_level="low",
        read_only=True,
    ),
}


TOOL_EXECUTORS = {
    "search_notes": execute_search_notes,
    "load_note_excerpt": execute_load_note_excerpt,
    "get_note_outline": execute_get_note_outline,
    "find_backlinks": execute_find_backlinks,
    "list_pending_approvals": execute_list_pending_approvals,
}


def get_allowed_tools_for_workflow(workflow_action: WorkflowAction) -> list[ToolSpec]:
    return [
        spec
        for spec in TOOL_REGISTRY.values()
        if workflow_action in spec.allowed_workflows
    ]


def validate_tool_call(
    decision: ToolCallDecision,
    *,
    workflow_action: WorkflowAction,
) -> GuardrailOutcome:
    if not decision.requested:
        return GuardrailOutcome(action=GuardrailAction.ALLOW, reasons=[], applied=False)

    tool_name = decision.tool_name
    if not tool_name:
        return GuardrailOutcome(
            action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY,
            reasons=["tool_not_allowed"],
            applied=True,
        )

    spec = TOOL_REGISTRY.get(tool_name)
    if spec is None:
        return GuardrailOutcome(
            action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY,
            reasons=["tool_not_allowed"],
            applied=True,
        )
    if workflow_action not in spec.allowed_workflows:
        return GuardrailOutcome(
            action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY,
            reasons=["tool_not_allowed", "workflow_not_allowed"],
            applied=True,
        )
    if not spec.read_only:
        return GuardrailOutcome(
            action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY,
            reasons=["tool_not_read_only"],
            applied=True,
        )
    if not _arguments_match_schema(decision.arguments, spec.input_schema):
        return GuardrailOutcome(
            action=GuardrailAction.DOWNGRADE_TO_RETRIEVAL_ONLY,
            reasons=["invalid_tool_arguments"],
            applied=True,
        )

    return GuardrailOutcome(action=GuardrailAction.ALLOW, reasons=[], applied=False)


def execute_tool_call(
    decision: ToolCallDecision,
    *,
    workflow_action: WorkflowAction,
    settings: Settings,
) -> ToolExecutionResult:
    guardrail = validate_tool_call(decision, workflow_action=workflow_action)
    if guardrail.applied:
        return ToolExecutionResult(
            tool_name=decision.tool_name or "",
            ok=False,
            error="tool_not_allowed",
        )

    tool_name = decision.tool_name
    if not tool_name:
        return ToolExecutionResult(tool_name="", ok=False, error="tool_not_requested")
    executor = TOOL_EXECUTORS[tool_name]
    return executor(decision.arguments, settings=settings)


def _arguments_match_schema(arguments: object, schema: dict[str, object]) -> bool:
    if not _matches_schema_type(arguments, schema.get("type")):
        return False
    if not isinstance(arguments, dict):
        return False

    required = schema.get("required")
    if isinstance(required, list):
        for field_name in required:
            if isinstance(field_name, str) and field_name not in arguments:
                return False

    properties = schema.get("properties")
    property_schemas = properties if isinstance(properties, dict) else {}

    if schema.get("additionalProperties") is False:
        allowed_keys = {key for key in property_schemas.keys() if isinstance(key, str)}
        for key in arguments.keys():
            if key not in allowed_keys:
                return False

    for key, value in arguments.items():
        property_schema = property_schemas.get(key)
        if not isinstance(property_schema, dict):
            continue
        if not _matches_schema_type(value, property_schema.get("type")):
            return False

    return True


def _matches_schema_type(value: object, schema_type: object) -> bool:
    if not isinstance(schema_type, str):
        return True
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "object":
        return isinstance(value, dict)
    return True
