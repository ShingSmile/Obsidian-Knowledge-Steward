export type WorkflowAction = "ask_qa" | "ingest_steward" | "daily_digest";
export type RunStatus =
  | "accepted"
  | "waiting_for_approval"
  | "completed"
  | "failed"
  | "not_implemented";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ModelProviderDescriptor {
  name: string;
  priority: number;
  enabled: boolean;
  purpose: string;
  base_url?: string | null;
  chat_model?: string | null;
  embedding_model?: string | null;
}

export interface SampleVaultStats {
  path: string;
  note_count: number;
  frontmatter_note_count: number;
  wikilink_count: number;
  task_checkbox_count: number;
  template_family_counts: Record<string, number>;
}

export interface HealthResponse {
  service_name: string;
  version: string;
  status: string;
  model_strategy: string;
  supported_actions: WorkflowAction[];
  providers: ModelProviderDescriptor[];
  sample_vault: SampleVaultStats;
  generated_at: string;
}

export interface RetrievalMetadataFilter {
  path_prefixes: string[];
  note_types: string[];
  template_families: string[];
  min_source_mtime_ns?: number | null;
  max_source_mtime_ns?: number | null;
  daily_note_date_from?: string | null;
  daily_note_date_to?: string | null;
}

export interface RetrievedChunkCandidate {
  retrieval_source: string;
  chunk_id: string;
  note_id: string;
  path: string;
  title: string;
  heading_path?: string | null;
  note_type: string;
  template_family: string;
  daily_note_date?: string | null;
  source_mtime_ns: number;
  start_line: number;
  end_line: number;
  score: number;
  snippet: string;
  text: string;
}

export type AskResultMode = "generated_answer" | "retrieval_only" | "no_hits";

export interface AskCitation {
  chunk_id: string;
  path: string;
  title: string;
  heading_path?: string | null;
  start_line: number;
  end_line: number;
  score: number;
  snippet: string;
  retrieval_source: string;
}

export interface AskWorkflowResult {
  mode: AskResultMode;
  query: string;
  answer: string;
  citations: AskCitation[];
  retrieved_candidates: RetrievedChunkCandidate[];
  retrieval_fallback_used: boolean;
  retrieval_fallback_reason?: string | null;
  model_fallback_used: boolean;
  model_fallback_reason?: string | null;
  provider_name?: string | null;
  model_name?: string | null;
}

export interface PatchOp {
  op: string;
  target_path: string;
  payload: Record<string, unknown>;
}

export interface SafetyChecks {
  before_hash?: string | null;
  max_changed_lines: number;
  contains_delete: boolean;
}

export interface ProposalEvidence {
  source_path: string;
  heading_path?: string | null;
  chunk_id?: string | null;
  reason: string;
}

export interface Proposal {
  proposal_id: string;
  action_type: WorkflowAction;
  target_note_path: string;
  summary: string;
  risk_level: RiskLevel;
  evidence: ProposalEvidence[];
  patch_ops: PatchOp[];
  safety_checks: SafetyChecks;
}

export interface ApprovalDecision {
  approved: boolean;
  reviewer: string;
  comment?: string | null;
  approved_patch_ops: PatchOp[];
  decided_at: string;
}

export interface WritebackResult {
  applied: boolean;
  target_note_path?: string | null;
  before_hash?: string | null;
  after_hash?: string | null;
  applied_patch_ops: PatchOp[];
  error?: string | null;
}

export interface IngestWorkflowResult {
  vault_path: string;
  db_path: string;
  scanned_notes: number;
  created_notes: number;
  updated_notes: number;
  current_chunk_count: number;
  replaced_chunk_count: number;
}

export interface IngestAnalysisFinding {
  finding_type: string;
  summary: string;
  source: string;
  source_paths: string[];
  related_chunk_ids: string[];
}

export interface IngestAnalysisResult {
  scope: string;
  target_note_path: string;
  target_note_title: string;
  retrieval_queries: string[];
  related_candidates: RetrievedChunkCandidate[];
  findings: IngestAnalysisFinding[];
  fallback_used: boolean;
  fallback_reason?: string | null;
}

export interface PostWritebackSyncResult {
  succeeded: boolean;
  target_note_path: string;
  message: string;
  ingest_result?: IngestWorkflowResult | null;
  error?: string | null;
}

export interface DigestSourceNote {
  note_id: string;
  path: string;
  title: string;
  note_type: string;
  template_family: string;
  daily_note_date?: string | null;
  source_mtime_ns: number;
  task_count: number;
}

export interface DigestWorkflowResult {
  digest_markdown: string;
  source_notes: DigestSourceNote[];
  source_note_count: number;
  fallback_used: boolean;
  fallback_reason?: string | null;
}

export interface WorkflowInvokeRequest {
  thread_id?: string;
  action_type: WorkflowAction;
  user_query?: string | null;
  note_path?: string | null;
  note_paths?: string[];
  require_approval?: boolean;
  resume_from_checkpoint?: boolean;
  provider_preference?: string | null;
  retrieval_filter?: RetrievalMetadataFilter;
  metadata?: Record<string, unknown>;
}

export interface WorkflowInvokeResponse {
  run_id: string;
  thread_id: string;
  action_type: WorkflowAction;
  status: RunStatus;
  message: string;
  approval_required: boolean;
  proposal?: Proposal | null;
  ask_result?: AskWorkflowResult | null;
  ingest_result?: IngestWorkflowResult | null;
  analysis_result?: IngestAnalysisResult | null;
  digest_result?: DigestWorkflowResult | null;
}

export interface WorkflowResumeRequest {
  thread_id: string;
  proposal_id: string;
  approval_decision: ApprovalDecision;
  writeback_result?: WritebackResult | null;
  metadata?: Record<string, unknown>;
}

export interface WorkflowResumeResponse {
  run_id: string;
  thread_id: string;
  proposal_id: string;
  action_type: WorkflowAction;
  status: RunStatus;
  message: string;
  approval_required: boolean;
  proposal: Proposal;
  approval_decision: ApprovalDecision;
  audit_event_id?: string | null;
  resumed_from_checkpoint: boolean;
  writeback_result?: WritebackResult | null;
  post_writeback_sync?: PostWritebackSyncResult | null;
}

export interface WorkflowRollbackRequest {
  thread_id: string;
  proposal_id: string;
  rollback_result: WritebackResult;
  metadata?: Record<string, unknown>;
}

export interface WorkflowRollbackResponse {
  run_id: string;
  thread_id: string;
  proposal_id: string;
  action_type: WorkflowAction;
  status: RunStatus;
  message: string;
  proposal: Proposal;
  audit_event_id?: string | null;
  rollback_result: WritebackResult;
}

export interface PendingApprovalItem {
  thread_id: string;
  proposal_id: string;
  action_type: WorkflowAction;
  graph_name: string;
  summary: string;
  target_note_path: string;
  risk_level: RiskLevel;
  proposal: Proposal;
  proposal_created_at?: string | null;
  proposal_updated_at?: string | null;
  checkpoint_updated_at: string;
}

export interface WorkflowPendingApprovalsResponse {
  items: PendingApprovalItem[];
  generated_at: string;
}
