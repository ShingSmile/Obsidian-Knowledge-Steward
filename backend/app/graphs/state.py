from __future__ import annotations

from typing import TypedDict

from app.contracts.workflow import (
    ApprovalDecision,
    AskWorkflowResult,
    DigestWorkflowResult,
    IngestAnalysisResult,
    IngestWorkflowResult,
    PostWritebackSyncResult,
    Proposal,
    RetrievalMetadataFilter,
    WorkflowAction,
    WritebackResult,
)


class StewardState(TypedDict, total=False):
    thread_id: str
    run_id: str
    action_type: WorkflowAction
    note_path: str | None
    note_paths: list[str]
    user_query: str | None
    provider_preference: str | None
    retrieval_filter: RetrievalMetadataFilter
    request_metadata: dict
    raw_markdown: str | None
    note_meta: dict
    retrieved_chunks: list[dict]
    ask_query: str
    ask_candidates: list[dict]
    ask_bundle: dict
    ask_tool_decision: dict | None
    ask_tool_results: list[dict]
    ask_prompt_tool_results: list[dict]
    ask_prompt_candidates: list[dict]
    ask_citations: list[dict]
    ask_tool_call_rounds: int
    ask_max_tool_rounds: int
    ask_should_finalize: bool
    ask_retrieval_fallback_used: bool
    ask_retrieval_fallback_reason: str | None
    ask_tool_call_attempted: bool
    ask_tool_call_used: str | None
    ask_result: AskWorkflowResult | None
    ingest_result: IngestWorkflowResult | None
    analysis_result: IngestAnalysisResult | None
    digest_result: DigestWorkflowResult | None
    analysis_issues: list[dict]
    proposal: Proposal | None
    approval_required: bool
    approval_decision: ApprovalDecision | None
    patch_plan: list[dict]
    before_hash: str | None
    writeback_result: WritebackResult | None
    rollback_result: WritebackResult | None
    post_writeback_sync: PostWritebackSyncResult | None
    audit_event_id: str | None
    rollback_audit_event_id: str | None
    trace_events: list[dict]
    errors: list[dict]
    transient_prompt_context: dict
