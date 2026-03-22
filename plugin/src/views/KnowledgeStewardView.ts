import { ItemView, Notice, WorkspaceLeaf } from "obsidian";

import {
  KnowledgeStewardApiClient,
  KnowledgeStewardApiError,
  formatApiErrorMessage
} from "../api/client";
import type {
  BackendRuntimeSnapshot,
  KnowledgeStewardBackendRuntime
} from "../backend/runtime";
import type {
  ApprovalDecision,
  PatchOp,
  PendingApprovalItem,
  PostWritebackSyncResult,
  Proposal,
  WorkflowRollbackResponse,
  WritebackResult,
  WorkflowResumeResponse
} from "../contracts";
import {
  applyProposalWriteback,
  type LocalRollbackContext,
  type LocalWritebackExecution,
  rollbackProposalWriteback
} from "../writeback/applyProposalWriteback";

export const KNOWLEDGE_STEWARD_VIEW_TYPE = "knowledge-steward-view";

export interface ApprovalPanelContext {
  threadId: string;
  proposal: Proposal;
  sourceLabel?: string;
  loadedAt?: string;
  serverBacked?: boolean;
}

export class KnowledgeStewardView extends ItemView {
  private backendStatus: BackendRuntimeSnapshot | null = null;
  private unsubscribeBackendRuntime: (() => void) | null = null;
  private pendingApprovalItems: PendingApprovalItem[] = [];
  private pendingApprovalMessage: string | null = null;
  private pendingApprovalError: string | null = null;
  private isLoadingPendingApprovals = false;
  private approvalContext: ApprovalPanelContext | null = null;
  private approvalStatusMessage: string | null = null;
  private reviewer = "human";
  private comment = "";
  private submissionError: string | null = null;
  private lastResumeResponse: WorkflowResumeResponse | null = null;
  private lastRollbackResponse: WorkflowRollbackResponse | null = null;
  private pendingWritebackExecution: LocalWritebackExecution | null = null;
  private rollbackContext: LocalRollbackContext | null = null;
  private pendingRollbackResult: WritebackResult | null = null;
  private isSubmitting = false;

  constructor(
    leaf: WorkspaceLeaf,
    private readonly getClient: () => KnowledgeStewardApiClient,
    private readonly getBackendRuntime: () => KnowledgeStewardBackendRuntime
  ) {
    super(leaf);
    this.backendStatus = this.getBackendRuntime().getSnapshot();
  }

  getViewType(): string {
    return KNOWLEDGE_STEWARD_VIEW_TYPE;
  }

  getDisplayText(): string {
    return "Knowledge Steward";
  }

  async onOpen(): Promise<void> {
    this.unsubscribeBackendRuntime = this.getBackendRuntime().subscribe((snapshot) => {
      this.backendStatus = snapshot;
      this.render();
    });
    this.render();
    await Promise.allSettled([
      this.getBackendRuntime().refreshStatus(),
      this.refreshPendingApprovals()
    ]);
  }

  async onClose(): Promise<void> {
    this.unsubscribeBackendRuntime?.();
    this.unsubscribeBackendRuntime = null;
  }

  setBackendStatus(snapshot: BackendRuntimeSnapshot): void {
    this.backendStatus = snapshot;
    this.render();
  }

  setApprovalContext(context: ApprovalPanelContext): void {
    this.approvalContext = context;
    this.approvalStatusMessage = null;
    this.comment = "";
    this.submissionError = null;
    this.lastResumeResponse = null;
    this.lastRollbackResponse = null;
    this.pendingWritebackExecution = null;
    this.rollbackContext = null;
    this.pendingRollbackResult = null;
    this.render();
  }

  setApprovalStatusMessage(message: string): void {
    this.approvalContext = null;
    this.approvalStatusMessage = message;
    this.comment = "";
    this.submissionError = null;
    this.lastResumeResponse = null;
    this.lastRollbackResponse = null;
    this.pendingWritebackExecution = null;
    this.rollbackContext = null;
    this.pendingRollbackResult = null;
    this.isSubmitting = false;
    this.render();
  }

  clearApprovalContext(): void {
    this.approvalContext = null;
    this.approvalStatusMessage = null;
    this.comment = "";
    this.submissionError = null;
    this.lastResumeResponse = null;
    this.lastRollbackResponse = null;
    this.pendingWritebackExecution = null;
    this.rollbackContext = null;
    this.pendingRollbackResult = null;
    this.isSubmitting = false;
    this.render();
  }

  private render(): void {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass("knowledge-steward-view");

    contentEl.createEl("h2", { text: "Knowledge Steward" });
    contentEl.createEl("div", {
      cls: "knowledge-steward-meta",
      text: "Workflow-first plugin shell. Health, approval review and resume interaction are wired here first."
    });

    this.renderBackendRuntimeSection(contentEl);
    this.renderHealthSection(contentEl);

    this.renderPendingApprovalInboxSection(contentEl);
    this.renderApprovalSection(contentEl);
  }

  async refreshPendingApprovals(): Promise<void> {
    if (this.isLoadingPendingApprovals) {
      return;
    }

    this.isLoadingPendingApprovals = true;
    this.pendingApprovalError = null;
    this.render();

    try {
      const response = await this.getClient().listPendingApprovals();
      this.pendingApprovalItems = response.items;
      this.pendingApprovalMessage = (
        response.items.length === 0
          ? "No pending approval proposals found."
          : null
      );
      this.reconcileApprovalContextWithInbox(response.items);
    } catch (error) {
      this.pendingApprovalError = `Failed to load pending approvals: ${formatErrorMessage(error)}`;
      if (this.pendingApprovalItems.length === 0) {
        this.pendingApprovalMessage = "Pending approval inbox is currently unavailable.";
      }
    } finally {
      this.isLoadingPendingApprovals = false;
      this.render();
    }
  }

  private renderBackendRuntimeSection(container: HTMLElement): void {
    const section = container.createDiv({ cls: "knowledge-steward-section" });
    const header = section.createDiv({ cls: "knowledge-steward-section-header" });
    header.createEl("h3", { text: "Backend Runtime" });

    const checkButton = header.createEl("button", {
      text: this.backendStatus?.status === "checking"
        ? "Checking..."
        : "Check backend"
    });
    checkButton.disabled = this.backendStatus?.status === "checking" || this.isSubmitting;
    checkButton.addEventListener("click", () => {
      void this.getBackendRuntime().refreshStatus();
    });

    const startButton = header.createEl("button", {
      cls: "mod-cta",
      text: this.backendStatus?.status === "starting"
        ? "Starting..."
        : "Start backend"
    });
    startButton.disabled = (
      this.isSubmitting
      || this.backendStatus?.status === "starting"
      || this.backendStatus?.status === "ready"
      || !this.backendStatus?.startup_command_configured
    );
    startButton.addEventListener("click", () => {
      void this.handleStartBackend();
    });

    if (!this.backendStatus) {
      section.createDiv({
        cls: "knowledge-steward-callout",
        text: "Backend runtime status has not been loaded yet."
      });
      return;
    }

    const statusCard = section.createDiv({
      cls: [
        "knowledge-steward-card",
        "knowledge-steward-runtime-card",
        `knowledge-steward-runtime-${this.backendStatus.status}`
      ].join(" ")
    });
    statusCard.createEl("div", {
      cls: "knowledge-steward-label",
      text: "Runtime status"
    });
    statusCard.createEl("div", {
      cls: `knowledge-steward-runtime-pill knowledge-steward-runtime-pill-${this.backendStatus.status}`,
      text: this.backendStatus.status.toUpperCase()
    });
    statusCard.createEl("p", {
      text: this.backendStatus.status_message
    });
    statusCard.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: this.backendStatus.startup_command_configured
        ? "Launch command configured."
        : "No launch command configured. Manual backend startup remains available."
    });
    statusCard.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: `Auto-start on load: ${this.backendStatus.auto_start_enabled ? "enabled" : "disabled"}`
    });
    if (this.backendStatus.tracked_pid !== null) {
      statusCard.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Tracked PID: ${this.backendStatus.tracked_pid}`
      });
    }
    if (this.backendStatus.last_checked_at) {
      statusCard.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Last checked: ${formatTimestamp(this.backendStatus.last_checked_at)}`
      });
    }
    if (this.backendStatus.last_started_at) {
      statusCard.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Last launch attempt: ${formatTimestamp(this.backendStatus.last_started_at)}`
      });
    }
    if (this.backendStatus.last_ready_at) {
      statusCard.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Last ready: ${formatTimestamp(this.backendStatus.last_ready_at)}`
      });
    }
    if (this.backendStatus.last_exit_code !== null) {
      statusCard.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Last exit code: ${this.backendStatus.last_exit_code}`
      });
    }

    if (this.backendStatus.last_error) {
      section.createDiv({
        cls: "knowledge-steward-callout knowledge-steward-callout-error",
        text: `Last backend error: ${this.backendStatus.last_error}`
      });
    }

    if (this.backendStatus.recent_output.length > 0) {
      const outputCard = section.createDiv({ cls: "knowledge-steward-card" });
      outputCard.createEl("div", {
        cls: "knowledge-steward-label",
        text: "Recent launch output"
      });
      outputCard.createEl("pre", {
        cls: "knowledge-steward-code",
        text: this.backendStatus.recent_output.join("\n")
      });
    }
  }

  private renderHealthSection(container: HTMLElement): void {
    const health = this.backendStatus?.health;
    const section = container.createDiv({ cls: "knowledge-steward-section" });
    section.createEl("h3", { text: "Backend Health" });

    if (!health) {
      section.createDiv({
        cls: "knowledge-steward-callout",
        text: "Backend is not ready yet. Use Check backend to probe /health, or Start backend if a launch command is configured."
      });
      return;
    }

    section.createEl("p", {
      text: `Backend: ${health.status} (${health.version})`
    });
    section.createEl("p", {
      text: `Model strategy: ${health.model_strategy}`
    });
    section.createEl("p", {
      text: `Sample vault notes: ${health.sample_vault.note_count}`
    });
    section.createEl("p", {
      text: `Tasks: ${health.sample_vault.task_checkbox_count}, Wikilinks: ${health.sample_vault.wikilink_count}`
    });
  }

  private async handleStartBackend(): Promise<void> {
    const snapshot = await this.getBackendRuntime().startBackend();
    if (snapshot.status === "ready") {
      new Notice("Knowledge Steward backend is ready.");
      return;
    }
    if (snapshot.status === "starting") {
      new Notice("Knowledge Steward backend launch started. Waiting for readiness...");
      return;
    }
    new Notice(`Knowledge Steward backend launch did not complete: ${snapshot.status_message}`);
  }

  private renderPendingApprovalInboxSection(container: HTMLElement): void {
    const section = container.createDiv({ cls: "knowledge-steward-section" });
    const header = section.createDiv({ cls: "knowledge-steward-section-header" });
    header.createEl("h3", { text: "Pending Inbox" });

    const refreshButton = header.createEl("button", {
      text: this.isLoadingPendingApprovals ? "Refreshing..." : "Refresh inbox"
    });
    refreshButton.disabled = this.isLoadingPendingApprovals || this.isSubmitting;
    refreshButton.addEventListener("click", () => {
      void this.refreshPendingApprovals();
    });

    if (this.pendingApprovalError) {
      section.createDiv({
        cls: "knowledge-steward-callout knowledge-steward-callout-error",
        text: this.pendingApprovalError
      });
    } else if (this.pendingApprovalMessage) {
      section.createDiv({
        cls: "knowledge-steward-callout",
        text: this.pendingApprovalMessage
      });
    }

    if (this.pendingApprovalItems.length === 0) {
      return;
    }

    for (const item of this.pendingApprovalItems) {
      const isSelected = this.isSameApprovalContext(
        this.approvalContext,
        item.thread_id,
        item.proposal_id
      );
      const card = section.createDiv({
        cls: [
          "knowledge-steward-card",
          "knowledge-steward-inbox-item",
          isSelected ? "knowledge-steward-inbox-item-selected" : ""
        ].filter(Boolean).join(" ")
      });
      card.createEl("div", {
        cls: "knowledge-steward-label",
        text: item.action_type
      });
      card.createEl("p", { text: item.summary });
      card.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Target note: ${item.target_note_path}`
      });
      card.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Updated: ${formatTimestamp(item.checkpoint_updated_at)}`
      });
      card.createEl("div", {
        cls: `knowledge-steward-risk knowledge-steward-risk-${item.risk_level}`,
        text: `Risk: ${item.risk_level.toUpperCase()}`
      });

      const actions = card.createDiv({ cls: "knowledge-steward-actions" });
      const loadButton = actions.createEl("button", {
        cls: isSelected ? "mod-cta" : "",
        text: isSelected ? "Loaded" : "Load"
      });
      loadButton.disabled = this.isSubmitting || isSelected;
      loadButton.addEventListener("click", () => {
        this.setApprovalContext({
          threadId: item.thread_id,
          proposal: item.proposal,
          sourceLabel: "pending_inbox",
          loadedAt: new Date().toISOString(),
          serverBacked: true
        });
      });
    }
  }

  private renderApprovalSection(container: HTMLElement): void {
    const section = container.createDiv({ cls: "knowledge-steward-section" });
    section.createEl("h3", { text: "Approval Review" });

    if (!this.approvalContext) {
      if (this.approvalStatusMessage) {
        section.createDiv({
          cls: "knowledge-steward-callout",
          text: this.approvalStatusMessage
        });
      } else {
        section.createEl("p", {
          text: "No approval proposal loaded. Use the pending inbox, the daily digest approval command, or the local demo command."
        });
      }
      return;
    }

    const { proposal } = this.approvalContext;
    section.createDiv({
      cls: "knowledge-steward-inline-meta",
      text: `Thread: ${this.approvalContext.threadId}`
    });
    section.createDiv({
      cls: "knowledge-steward-inline-meta",
      text: `Proposal: ${proposal.proposal_id}`
    });
    section.createDiv({
      cls: "knowledge-steward-inline-meta",
      text: `Target note: ${proposal.target_note_path}`
    });
    if (this.approvalContext.sourceLabel) {
      section.createDiv({
        cls: "knowledge-steward-inline-meta",
        text: `Loaded from: ${this.approvalContext.sourceLabel}`
      });
    }
    if (this.approvalContext.loadedAt) {
      section.createDiv({
        cls: "knowledge-steward-inline-meta",
        text: `Loaded at: ${formatTimestamp(this.approvalContext.loadedAt)}`
      });
    }

    const summaryBlock = section.createDiv({ cls: "knowledge-steward-card" });
    summaryBlock.createEl("div", {
      cls: "knowledge-steward-label",
      text: "Summary"
    });
    summaryBlock.createEl("p", { text: proposal.summary });
    summaryBlock.createEl("div", {
      cls: `knowledge-steward-risk knowledge-steward-risk-${proposal.risk_level}`,
      text: `Risk: ${proposal.risk_level.toUpperCase()}`
    });

    this.renderSafetyChecks(section, proposal);
    this.renderEvidence(section, proposal);
    this.renderPatchPreview(section, proposal.patch_ops);
    this.renderSubmissionFeedback(section);
    this.renderApprovalForm(section);
    this.renderRollbackSection(section);
  }

  private renderSafetyChecks(container: HTMLElement, proposal: Proposal): void {
    const section = container.createDiv({ cls: "knowledge-steward-card" });
    section.createEl("div", {
      cls: "knowledge-steward-label",
      text: "Safety checks"
    });
    section.createEl("p", {
      text: `before_hash: ${proposal.safety_checks.before_hash ?? "not provided"}`
    });
    section.createEl("p", {
      text: `max_changed_lines: ${proposal.safety_checks.max_changed_lines}`
    });
    section.createEl("p", {
      text: `contains_delete: ${proposal.safety_checks.contains_delete ? "yes" : "no"}`
    });
  }

  private renderEvidence(container: HTMLElement, proposal: Proposal): void {
    const section = container.createDiv({ cls: "knowledge-steward-card" });
    section.createEl("div", {
      cls: "knowledge-steward-label",
      text: `Evidence (${proposal.evidence.length})`
    });

    if (proposal.evidence.length === 0) {
      section.createEl("p", { text: "No evidence attached." });
      return;
    }

    const list = section.createEl("ul", { cls: "knowledge-steward-list" });
    for (const evidence of proposal.evidence) {
      const item = list.createEl("li");
      item.createEl("strong", { text: evidence.source_path });
      item.createEl("div", { text: evidence.reason });
      if (evidence.heading_path) {
        item.createEl("div", {
          cls: "knowledge-steward-inline-meta",
          text: `Heading: ${evidence.heading_path}`
        });
      }
      if (evidence.chunk_id) {
        item.createEl("div", {
          cls: "knowledge-steward-inline-meta",
          text: `Chunk: ${evidence.chunk_id}`
        });
      }
    }
  }

  private renderPatchPreview(container: HTMLElement, patchOps: PatchOp[]): void {
    const section = container.createDiv({ cls: "knowledge-steward-card" });
    section.createEl("div", {
      cls: "knowledge-steward-label",
      text: `Patch preview (${patchOps.length})`
    });

    if (patchOps.length === 0) {
      section.createEl("p", { text: "No patch ops attached." });
      return;
    }

    for (const [index, patchOp] of patchOps.entries()) {
      const patchBlock = section.createDiv({ cls: "knowledge-steward-patch" });
      patchBlock.createEl("div", {
        cls: "knowledge-steward-patch-title",
        text: `PATCH ${index + 1} · ${patchOp.op} · ${patchOp.target_path}`
      });
      patchBlock.createEl("pre", {
        cls: "knowledge-steward-code",
        text: formatPatchPreview(patchOp)
      });
    }
  }

  private renderSubmissionFeedback(container: HTMLElement): void {
    if (this.submissionError) {
      container.createDiv({
        cls: "knowledge-steward-callout knowledge-steward-callout-error",
        text: this.submissionError
      });
    }

    if (!this.lastResumeResponse) {
      if (this.pendingWritebackExecution?.writeback_result.applied) {
        const callout = container.createDiv({
          cls: "knowledge-steward-callout"
        });
        callout.createEl("strong", { text: "Local writeback already applied" });
        callout.createEl("div", {
          text: "Retry Approve to sync backend audit state. Reject is disabled because the target note has already changed locally."
        });
        this.renderWritebackResult(
          callout,
          this.pendingWritebackExecution.writeback_result
        );
      }
      return;
    }

    const callout = container.createDiv({
      cls: "knowledge-steward-callout knowledge-steward-callout-success"
    });
    callout.createEl("strong", { text: "Last response" });
    callout.createEl("div", { text: this.lastResumeResponse.message });
    callout.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: `Status: ${this.lastResumeResponse.status}`
    });
    if (this.lastResumeResponse.audit_event_id) {
      callout.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Audit event: ${this.lastResumeResponse.audit_event_id}`
      });
    }
    if (this.lastResumeResponse.writeback_result) {
      this.renderWritebackResult(callout, this.lastResumeResponse.writeback_result);
    }
    if (this.lastResumeResponse.post_writeback_sync) {
      this.renderPostWritebackSyncResult(
        callout,
        this.lastResumeResponse.post_writeback_sync
      );
    }

    if (!this.lastRollbackResponse) {
      return;
    }

    const rollbackCallout = container.createDiv({
      cls: this.lastRollbackResponse.rollback_result.applied
        ? "knowledge-steward-callout knowledge-steward-callout-success"
        : "knowledge-steward-callout"
    });
    rollbackCallout.createEl("strong", { text: "Last rollback response" });
    rollbackCallout.createEl("div", { text: this.lastRollbackResponse.message });
    rollbackCallout.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: `Status: ${this.lastRollbackResponse.status}`
    });
    if (this.lastRollbackResponse.audit_event_id) {
      rollbackCallout.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Audit event: ${this.lastRollbackResponse.audit_event_id}`
      });
    }
    this.renderWritebackResult(
      rollbackCallout,
      this.lastRollbackResponse.rollback_result
    );
  }

  private renderApprovalForm(container: HTMLElement): void {
    if (!this.approvalContext) {
      return;
    }

    const section = container.createDiv({ cls: "knowledge-steward-card" });
    section.createEl("div", {
      cls: "knowledge-steward-label",
      text: "Decision"
    });

    const reviewerField = section.createDiv({ cls: "knowledge-steward-field" });
    reviewerField.createEl("label", {
      cls: "knowledge-steward-label",
      text: "Reviewer"
    });
    const reviewerInput = reviewerField.createEl("input", {
      cls: "knowledge-steward-input",
      attr: {
        type: "text",
        placeholder: "human"
      }
    });
    reviewerInput.value = this.reviewer;
    reviewerInput.disabled = this.isSubmitting || this.lastResumeResponse !== null;
    reviewerInput.addEventListener("input", () => {
      this.reviewer = reviewerInput.value;
    });

    const commentField = section.createDiv({ cls: "knowledge-steward-field" });
    commentField.createEl("label", {
      cls: "knowledge-steward-label",
      text: "Comment"
    });
    const commentInput = commentField.createEl("textarea", {
      cls: "knowledge-steward-textarea",
      attr: {
        rows: "3",
        placeholder: "Optional reviewer note"
      }
    });
    commentInput.value = this.comment;
    commentInput.disabled = this.isSubmitting || this.lastResumeResponse !== null;
    commentInput.addEventListener("input", () => {
      this.comment = commentInput.value;
    });

    const actions = section.createDiv({ cls: "knowledge-steward-actions" });
    const approveButton = actions.createEl("button", {
      cls: "mod-cta",
      text: this.isSubmitting
        ? "Submitting..."
        : this.pendingWritebackExecution?.writeback_result.applied
          ? "Retry Approve"
          : "Approve"
    });
    approveButton.disabled = this.isSubmitting || this.lastResumeResponse !== null;
    approveButton.addEventListener("click", () => {
      void this.submitDecision(true);
    });

    const rejectButton = actions.createEl("button", {
      text: this.isSubmitting ? "Submitting..." : "Reject"
    });
    rejectButton.disabled = (
      this.isSubmitting
      || this.lastResumeResponse !== null
      || this.pendingWritebackExecution?.writeback_result.applied === true
    );
    rejectButton.addEventListener("click", () => {
      void this.submitDecision(false);
    });

    const clearButton = actions.createEl("button", {
      text: "Clear"
    });
    clearButton.disabled = this.isSubmitting;
    clearButton.addEventListener("click", () => {
      this.clearApprovalContext();
    });

    if (this.lastResumeResponse) {
      section.createEl("p", {
        cls: "knowledge-steward-inline-meta",
        text: "This context is frozen after a successful submission to avoid reusing stale proposal state. Clear it before reviewing another item."
      });
    } else if (this.pendingWritebackExecution?.writeback_result.applied) {
      section.createEl("p", {
        cls: "knowledge-steward-inline-meta",
        text: "Local writeback has already changed the target note. Use Retry Approve to sync backend audit state instead of switching to Reject."
      });
    }
  }

  private renderRollbackSection(container: HTMLElement): void {
    if (
      !this.approvalContext
      || !this.lastResumeResponse?.writeback_result?.applied
    ) {
      return;
    }

    const section = container.createDiv({ cls: "knowledge-steward-card" });
    section.createEl("div", {
      cls: "knowledge-steward-label",
      text: "Rollback"
    });

    if (this.pendingRollbackResult?.applied) {
      const callout = section.createDiv({ cls: "knowledge-steward-callout" });
      callout.createEl("strong", { text: "Local rollback already applied" });
      callout.createEl("div", {
        text: "Retry rollback sync to record audit state. The plugin will not execute the rollback twice."
      });
      this.renderWritebackResult(callout, this.pendingRollbackResult);
    } else if (!this.rollbackContext && !this.lastRollbackResponse) {
      section.createDiv({
        cls: "knowledge-steward-callout",
        text: (
          "Rollback is only available for writebacks executed in the current plugin session. "
          + "Inferred or historical writebacks remain audit-only for now."
        )
      });
      return;
    }

    const rollbackButton = section.createEl("button", {
      text: this.isSubmitting
        ? "Rolling back..."
        : this.pendingRollbackResult?.applied
          ? "Retry rollback sync"
          : this.lastRollbackResponse?.rollback_result.applied
            ? "Rollback recorded"
            : "Rollback"
    });
    rollbackButton.disabled = (
      this.isSubmitting
      || this.lastRollbackResponse?.rollback_result.applied === true
    );
    rollbackButton.addEventListener("click", () => {
      void this.submitRollback();
    });

    if (this.lastRollbackResponse?.rollback_result.applied) {
      section.createEl("p", {
        cls: "knowledge-steward-inline-meta",
        text: "Rollback is frozen after a successful record to avoid replaying the same local snapshot."
      });
    } else if (this.rollbackContext) {
      section.createEl("p", {
        cls: "knowledge-steward-inline-meta",
        text: "Rollback will only run if the current file still matches the exact post-writeback hash."
      });
    }
  }

  private async submitDecision(approved: boolean): Promise<void> {
    if (!this.approvalContext || this.isSubmitting) {
      return;
    }
    if (!approved && this.pendingWritebackExecution?.writeback_result.applied) {
      this.submissionError = (
        "The target note has already been modified locally. "
        + "Retry Approve to sync backend audit state instead of rejecting."
      );
      this.render();
      return;
    }

    this.isSubmitting = true;
    this.submissionError = null;
    this.render();

    let localWritebackResult: WritebackResult | null = null;
    let localWritebackExecution: LocalWritebackExecution | null = null;
    try {
      const decision = buildApprovalDecision({
        approved,
        reviewer: this.reviewer,
        comment: this.comment,
        proposal: this.approvalContext.proposal
      });
      if (approved) {
        // 写回副作用先在插件本地执行，再把真实结果回传给后端。
        // 这样可以守住“后端不直接改 Vault”的边界，同时让 audit/checkpoint 记录到真实写回状态。
        localWritebackExecution = this.pendingWritebackExecution
          ?? await applyProposalWriteback(this.app, this.approvalContext.proposal);
        localWritebackResult = localWritebackExecution.writeback_result;
      }
      const response = await this.getClient().resumeWorkflow({
        thread_id: this.approvalContext.threadId,
        proposal_id: this.approvalContext.proposal.proposal_id,
        approval_decision: decision,
        writeback_result: localWritebackResult
      });
      this.removeResolvedProposalFromInbox(
        this.approvalContext.threadId,
        this.approvalContext.proposal.proposal_id
      );
      this.pendingWritebackExecution = null;
      this.pendingRollbackResult = null;
      this.rollbackContext = localWritebackExecution?.rollback_context ?? null;
      this.lastRollbackResponse = null;
      // 审批一旦成功提交就冻结当前上下文，避免同一份陈旧 proposal 在面板中被二次改判。
      this.lastResumeResponse = response;
      new Notice(`Knowledge Steward approval submitted: ${response.message}`);
    } catch (error) {
      const errorMessage = formatErrorMessage(error);
      if (approved && localWritebackResult?.applied) {
        // 这里保留已成功的本地写回结果，允许用户重试 approve 只做“同步后端审计”这一步，
        // 避免因为网络失败而再次执行同一批 patch。
        this.pendingWritebackExecution = localWritebackExecution;
        this.submissionError = (
          "Local writeback already succeeded, but backend resume failed. "
          + `Retry Approve to sync audit state. Original error: ${errorMessage}`
        );
      } else {
        this.submissionError = isPendingProposalStaleError(error)
          ? "This proposal is no longer pending. Refresh the inbox and load the latest item before retrying."
          : errorMessage;
        if (isPendingProposalStaleError(error)) {
          void this.refreshPendingApprovals();
        }
      }
      new Notice(`Knowledge Steward approval failed: ${this.submissionError}`);
    } finally {
      this.isSubmitting = false;
      this.render();
    }
  }

  private async submitRollback(): Promise<void> {
    if (
      !this.approvalContext
      || this.isSubmitting
      || !this.lastResumeResponse?.writeback_result?.applied
    ) {
      return;
    }

    this.isSubmitting = true;
    this.submissionError = null;
    this.render();

    let localRollbackResult: WritebackResult | null = null;
    try {
      if (this.pendingRollbackResult?.applied) {
        localRollbackResult = this.pendingRollbackResult;
      } else if (this.rollbackContext) {
        localRollbackResult = await rollbackProposalWriteback(
          this.app,
          this.approvalContext.proposal,
          this.rollbackContext
        );
      } else {
        this.submissionError = (
          "Rollback is unavailable because this writeback was not executed in the current plugin session."
        );
        return;
      }

      const response = await this.getClient().rollbackWorkflow({
        thread_id: this.approvalContext.threadId,
        proposal_id: this.approvalContext.proposal.proposal_id,
        rollback_result: localRollbackResult
      });
      this.pendingRollbackResult = null;
      this.lastRollbackResponse = response;
      if (response.rollback_result.applied) {
        this.rollbackContext = null;
      }
      new Notice(`Knowledge Steward rollback submitted: ${response.message}`);
    } catch (error) {
      const errorMessage = formatErrorMessage(error);
      if (localRollbackResult?.applied) {
        // rollback 和 approve 一样，副作用事实一旦发生，就只能重试同步后端，
        // 不能再重复执行一次本地文件修改。
        this.pendingRollbackResult = localRollbackResult;
        this.rollbackContext = null;
        this.submissionError = (
          "Local rollback already succeeded, but backend rollback sync failed. "
          + `Retry rollback sync. Original error: ${errorMessage}`
        );
      } else {
        this.submissionError = errorMessage;
      }
      new Notice(`Knowledge Steward rollback failed: ${this.submissionError}`);
    } finally {
      this.isSubmitting = false;
      this.render();
    }
  }

  private renderWritebackResult(
    container: HTMLElement,
    writebackResult: WritebackResult
  ): void {
    container.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: `Writeback applied: ${writebackResult.applied ? "yes" : "no"}`
    });
    if (writebackResult.before_hash) {
      container.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `before_hash: ${writebackResult.before_hash}`
      });
    }
    if (writebackResult.after_hash) {
      container.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `after_hash: ${writebackResult.after_hash}`
      });
    }
    container.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: `Applied patch ops: ${writebackResult.applied_patch_ops.length}`
    });
    if (writebackResult.error) {
      container.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Error: ${writebackResult.error}`
      });
    }
  }

  private renderPostWritebackSyncResult(
    container: HTMLElement,
    syncResult: PostWritebackSyncResult
  ): void {
    container.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: `Scoped reindex: ${syncResult.succeeded ? "yes" : "no"}`
    });
    container.createEl("div", {
      cls: "knowledge-steward-inline-meta",
      text: syncResult.message
    });
    if (syncResult.ingest_result) {
      container.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: (
          `Reindexed notes: ${syncResult.ingest_result.scanned_notes}, `
          + `updated: ${syncResult.ingest_result.updated_notes}`
        )
      });
    }
    if (syncResult.error) {
      container.createEl("div", {
        cls: "knowledge-steward-inline-meta",
        text: `Reindex error: ${syncResult.error}`
      });
    }
  }

  private reconcileApprovalContextWithInbox(items: PendingApprovalItem[]): void {
    if (!this.approvalContext?.serverBacked) {
      return;
    }
    if (
      this.lastResumeResponse
      || this.pendingWritebackExecution?.writeback_result.applied
    ) {
      return;
    }

    const matchingItem = items.find((item) =>
      this.isSameApprovalContext(
        this.approvalContext,
        item.thread_id,
        item.proposal_id
      )
    );
    if (matchingItem) {
      return;
    }

    // 收件箱刷新后如果当前 server-backed proposal 已经不在 waiting 列表里，
    // 说明它大概率已被其他恢复动作消费或已过期，继续保留在面板里只会误导用户。
    this.clearApprovalContext();
    this.approvalStatusMessage = (
      "The previously loaded proposal is no longer pending. Refresh the inbox or load another item."
    );
  }

  private removeResolvedProposalFromInbox(threadId: string, proposalId: string): void {
    this.pendingApprovalItems = this.pendingApprovalItems.filter((item) => !(
      item.thread_id === threadId
      && item.proposal_id === proposalId
    ));
    if (this.pendingApprovalItems.length === 0 && !this.pendingApprovalError) {
      this.pendingApprovalMessage = "No pending approval proposals found.";
    }
  }

  private isSameApprovalContext(
    context: ApprovalPanelContext | null,
    threadId: string,
    proposalId: string
  ): boolean {
    return Boolean(
      context
      && context.threadId === threadId
      && context.proposal.proposal_id === proposalId
    );
  }
}

function buildApprovalDecision(input: {
  approved: boolean;
  reviewer: string;
  comment: string;
  proposal: Proposal;
}): ApprovalDecision {
  const reviewer = input.reviewer.trim() || "human";
  const comment = input.comment.trim();
  // 后端当前明确拒绝 partial patch approval，因此前端 approve 只能整 proposal 放行，
  // reject 则必须传空数组，避免把任务边界偷偷扩大成“局部应用 patch”。
  return {
    approved: input.approved,
    reviewer,
    comment: comment.length > 0 ? comment : null,
    approved_patch_ops: input.approved ? input.proposal.patch_ops : [],
    decided_at: new Date().toISOString()
  };
}

function formatPatchPreview(patchOp: PatchOp): string {
  const payload = JSON.stringify(patchOp.payload, null, 2) ?? "{}";
  return [
    `--- ${patchOp.target_path}`,
    `+++ ${patchOp.target_path}`,
    `@@ ${patchOp.op}`,
    payload
  ].join("\n");
}

function formatErrorMessage(error: unknown): string {
  if (error instanceof KnowledgeStewardApiError) {
    return error.detail
      ? `Backend error ${error.status}: ${error.detail}`
      : `Backend error ${error.status}`;
  }
  return formatApiErrorMessage(error);
}

function isPendingProposalStaleError(error: unknown): boolean {
  return (
    error instanceof KnowledgeStewardApiError
    && (error.status === 404 || error.status === 409)
  );
}

function formatTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}
