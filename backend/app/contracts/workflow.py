from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowAction(str, Enum):
    ASK_QA = "ask_qa"
    INGEST_STEWARD = "ingest_steward"
    DAILY_DIGEST = "daily_digest"


class ContextEvidenceItem(BaseModel):
    source_path: str
    chunk_id: str | None = None
    source_note_title: str | None = None
    heading_path: str | None = None
    position_hint: str | None = None
    text: str
    score: float | None = None
    source_kind: Literal["retrieval", "tool", "proposal", "digest"]


class ContextSourceNote(BaseModel):
    source_path: str
    title: str
    chunk_count: int = 0
    max_score: float | None = None


class ContextAssemblyMetadata(BaseModel):
    initial_candidate_count: int = 0
    relevance_filtered_count: int = 0
    diversity_filtered_count: int = 0
    budget_filtered_count: int = 0
    suspicious_filtered_count: int = 0
    final_evidence_count: int = 0
    relevance_threshold: float = 0.0
    per_source_limit: int = 0
    full_text_char_budget: int = 0
    summary_char_budget: int = 0


class ContextBundle(BaseModel):
    user_intent: str
    workflow_action: WorkflowAction
    evidence_items: list[ContextEvidenceItem] = Field(default_factory=list)
    source_notes: list[ContextSourceNote] = Field(default_factory=list)
    assembly_metadata: ContextAssemblyMetadata = Field(
        default_factory=ContextAssemblyMetadata
    )
    tool_results: list["ToolExecutionResult"] = Field(default_factory=list)
    allowed_tool_names: list[str] = Field(default_factory=list)
    token_budget: int
    safety_flags: list[str] = Field(default_factory=list)
    assembly_notes: list[str] = Field(default_factory=list)


class ToolSpec(BaseModel):
    name: str
    purpose: str
    allowed_workflows: list[WorkflowAction]
    input_schema: dict[str, object]
    output_schema: dict[str, object]
    risk_level: str
    read_only: bool = True


class ToolCallDecision(BaseModel):
    requested: bool
    tool_name: str | None = None
    arguments: dict[str, object] = Field(default_factory=dict)
    rationale: str | None = None


class ToolExecutionResult(BaseModel):
    tool_name: str
    ok: bool
    data: dict[str, object] = Field(default_factory=dict)
    diagnostics: dict[str, object] = Field(default_factory=dict)
    error: str | None = None
    allow_context_reentry: bool = True


ContextBundle.model_rebuild()


class GuardrailAction(str, Enum):
    ALLOW = "allow"
    DOWNGRADE_TO_RETRIEVAL_ONLY = "downgrade_to_retrieval_only"
    REFUSE_STRONG_CLAIM = "refuse_strong_claim"
    TOOL_RESULT_INSUFFICIENT = "tool_result_insufficient"
    POSSIBLE_INJECTION_DETECTED = "possible_injection_detected"


class GuardrailOutcome(BaseModel):
    action: GuardrailAction
    reasons: list[str] = Field(default_factory=list)
    applied: bool = False


class RunStatus(str, Enum):
    ACCEPTED = "accepted"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    NOT_IMPLEMENTED = "not_implemented"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatchOp(BaseModel):
    op: str
    target_path: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SafetyChecks(BaseModel):
    before_hash: str | None = None
    max_changed_lines: int = 0
    contains_delete: bool = False


class ProposalEvidence(BaseModel):
    source_path: str
    heading_path: str | None = None
    chunk_id: str | None = None
    reason: str


class Proposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"prop_{uuid4().hex}")
    action_type: WorkflowAction
    target_note_path: str
    summary: str
    risk_level: RiskLevel = RiskLevel.HIGH
    evidence: list[ProposalEvidence] = Field(default_factory=list)
    patch_ops: list[PatchOp] = Field(default_factory=list)
    safety_checks: SafetyChecks = Field(default_factory=SafetyChecks)


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer: str = "human"
    comment: str | None = None
    approved_patch_ops: list[PatchOp] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WritebackResult(BaseModel):
    applied: bool = False
    target_note_path: str | None = None
    before_hash: str | None = None
    after_hash: str | None = None
    applied_patch_ops: list[PatchOp] = Field(default_factory=list)
    error: str | None = None


class AuditEvent(BaseModel):
    audit_event_id: str = Field(default_factory=lambda: f"audit_{uuid4().hex}")
    thread_id: str
    proposal_id: str | None = None
    action_type: WorkflowAction
    target_note_path: str | None = None
    approval_required: bool = False
    approval_decision: ApprovalDecision | None = None
    writeback_result: WritebackResult | None = None
    model_info: dict[str, Any] = Field(default_factory=dict)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    latency_ms: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModelProviderDescriptor(BaseModel):
    name: str
    priority: int
    enabled: bool
    purpose: str
    base_url: str | None = None
    chat_model: str | None = None
    embedding_model: str | None = None


class SampleVaultStats(BaseModel):
    path: str
    note_count: int
    frontmatter_note_count: int
    wikilink_count: int
    task_checkbox_count: int
    template_family_counts: dict[str, int] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    service_name: str
    version: str
    status: str
    model_strategy: str
    supported_actions: list[WorkflowAction]
    providers: list[ModelProviderDescriptor]
    sample_vault: SampleVaultStats
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RetrievalMetadataFilter(BaseModel):
    path_prefixes: list[str] = Field(default_factory=list)
    note_types: list[str] = Field(default_factory=list)
    template_families: list[str] = Field(default_factory=list)
    min_source_mtime_ns: int | None = None
    max_source_mtime_ns: int | None = None
    daily_note_date_from: str | None = None
    daily_note_date_to: str | None = None

    def is_empty(self) -> bool:
        return not (
            self.path_prefixes
            or self.note_types
            or self.template_families
            or self.min_source_mtime_ns is not None
            or self.max_source_mtime_ns is not None
            or self.daily_note_date_from is not None
            or self.daily_note_date_to is not None
        )


class RetrievedChunkCandidate(BaseModel):
    retrieval_source: str = "sqlite_fts"
    chunk_id: str
    note_id: str
    path: str
    title: str
    heading_path: str | None = None
    note_type: str
    template_family: str
    daily_note_date: str | None = None
    source_mtime_ns: int
    start_line: int
    end_line: int
    score: float
    snippet: str
    text: str


class AskResultMode(str, Enum):
    GENERATED_ANSWER = "generated_answer"
    RETRIEVAL_ONLY = "retrieval_only"
    NO_HITS = "no_hits"


class AskCitation(BaseModel):
    chunk_id: str
    path: str
    title: str
    heading_path: str | None = None
    start_line: int
    end_line: int
    score: float
    snippet: str
    retrieval_source: str = "sqlite_fts"


class RetrievalSearchResponse(BaseModel):
    candidates: list[RetrievedChunkCandidate] = Field(default_factory=list)
    requested_filters: RetrievalMetadataFilter = Field(default_factory=RetrievalMetadataFilter)
    effective_filters: RetrievalMetadataFilter = Field(default_factory=RetrievalMetadataFilter)
    fallback_used: bool = False
    fallback_reason: str | None = None
    disabled: bool = False
    disabled_reason: str | None = None
    provider_name: str | None = None
    model_name: str | None = None


class AskWorkflowResult(BaseModel):
    mode: AskResultMode
    query: str
    answer: str
    citations: list[AskCitation] = Field(default_factory=list)
    retrieved_candidates: list[RetrievedChunkCandidate] = Field(default_factory=list)
    retrieval_fallback_used: bool = False
    retrieval_fallback_reason: str | None = None
    model_fallback_used: bool = False
    model_fallback_reason: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    tool_call_attempted: bool = False
    tool_call_rounds: int = 0
    tool_call_used: str | None = None
    guardrail_action: GuardrailAction | None = None


class IngestWorkflowResult(BaseModel):
    vault_path: str
    db_path: str
    scanned_notes: int
    created_notes: int
    updated_notes: int
    current_chunk_count: int
    replaced_chunk_count: int


class IngestAnalysisFinding(BaseModel):
    finding_type: str
    summary: str
    source: str
    source_paths: list[str] = Field(default_factory=list)
    related_chunk_ids: list[str] = Field(default_factory=list)


class IngestAnalysisResult(BaseModel):
    scope: str
    target_note_path: str
    target_note_title: str
    retrieval_queries: list[str] = Field(default_factory=list)
    related_candidates: list[RetrievedChunkCandidate] = Field(default_factory=list)
    findings: list[IngestAnalysisFinding] = Field(default_factory=list)
    fallback_used: bool = False
    fallback_reason: str | None = None


class PostWritebackSyncResult(BaseModel):
    succeeded: bool
    target_note_path: str
    message: str
    ingest_result: IngestWorkflowResult | None = None
    error: str | None = None


class DigestSourceNote(BaseModel):
    note_id: str
    path: str
    title: str
    note_type: str
    template_family: str
    daily_note_date: str | None = None
    source_mtime_ns: int
    task_count: int = 0


class DigestWorkflowResult(BaseModel):
    digest_markdown: str
    source_notes: list[DigestSourceNote] = Field(default_factory=list)
    source_note_count: int = 0
    fallback_used: bool = False
    fallback_reason: str | None = None
    context_bundle_summary: dict[str, object] = Field(default_factory=dict)


class WorkflowInvokeRequest(BaseModel):
    thread_id: str | None = None
    action_type: WorkflowAction
    user_query: str | None = None
    note_path: str | None = None
    note_paths: list[str] = Field(default_factory=list)
    require_approval: bool = True
    resume_from_checkpoint: bool = False
    provider_preference: str | None = None
    retrieval_filter: RetrievalMetadataFilter = Field(default_factory=RetrievalMetadataFilter)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowInvokeResponse(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex}")
    thread_id: str
    action_type: WorkflowAction
    status: RunStatus
    message: str
    approval_required: bool = False
    proposal: Proposal | None = None
    ask_result: AskWorkflowResult | None = None
    ingest_result: IngestWorkflowResult | None = None
    analysis_result: IngestAnalysisResult | None = None
    digest_result: DigestWorkflowResult | None = None


class WorkflowResumeRequest(BaseModel):
    thread_id: str
    proposal_id: str
    approval_decision: ApprovalDecision
    writeback_result: WritebackResult | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowResumeResponse(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex}")
    thread_id: str
    proposal_id: str
    action_type: WorkflowAction
    status: RunStatus
    message: str
    approval_required: bool = False
    proposal: Proposal
    approval_decision: ApprovalDecision
    audit_event_id: str | None = None
    resumed_from_checkpoint: bool = True
    writeback_result: WritebackResult | None = None
    post_writeback_sync: PostWritebackSyncResult | None = None


class WorkflowRollbackRequest(BaseModel):
    thread_id: str
    proposal_id: str
    rollback_result: WritebackResult
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowRollbackResponse(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex}")
    thread_id: str
    proposal_id: str
    action_type: WorkflowAction
    status: RunStatus
    message: str
    proposal: Proposal
    audit_event_id: str | None = None
    rollback_result: WritebackResult


class PendingApprovalItem(BaseModel):
    thread_id: str
    proposal_id: str
    action_type: WorkflowAction
    graph_name: str
    summary: str
    target_note_path: str
    risk_level: RiskLevel
    proposal: Proposal
    proposal_created_at: str | None = None
    proposal_updated_at: str | None = None
    checkpoint_updated_at: str


class WorkflowPendingApprovalsResponse(BaseModel):
    items: list[PendingApprovalItem] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
