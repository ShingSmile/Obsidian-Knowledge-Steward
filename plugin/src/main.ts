import { Notice, Plugin, WorkspaceLeaf } from "obsidian";

import { KnowledgeStewardApiClient } from "./api/client";
import { KnowledgeStewardBackendRuntime } from "./backend/runtime";
import type {
  PatchOp,
  Proposal,
  WorkflowInvokeResponse
} from "./contracts";
import {
  DEFAULT_SETTINGS,
  KnowledgeStewardSettingTab,
  type KnowledgeStewardSettings
} from "./settings";
import {
  KNOWLEDGE_STEWARD_VIEW_TYPE,
  KnowledgeStewardView,
  type ApprovalPanelContext
} from "./views/KnowledgeStewardView";

export default class KnowledgeStewardPlugin extends Plugin {
  settings: KnowledgeStewardSettings = DEFAULT_SETTINGS;
  private readonly backendRuntime = new KnowledgeStewardBackendRuntime(
    () => this.client,
    () => this.settings
  );

  async onload(): Promise<void> {
    await this.loadSettings();

    this.registerView(
      KNOWLEDGE_STEWARD_VIEW_TYPE,
      (leaf) => new KnowledgeStewardView(
        leaf,
        () => this.client,
        () => this.backendRuntime
      )
    );

    this.addCommand({
      id: "open-knowledge-steward-panel",
      name: "Open panel",
      callback: async () => {
        await this.activateView();
      }
    });

    this.addCommand({
      id: "ping-knowledge-steward-backend",
      name: "Ping backend",
      callback: async () => {
        await this.pingBackend();
      }
    });

    this.addCommand({
      id: "start-knowledge-steward-backend",
      name: "Start backend",
      callback: async () => {
        await this.startBackend();
      }
    });

    this.addCommand({
      id: "load-knowledge-steward-digest-approval",
      name: "Load daily digest approval",
      callback: async () => {
        await this.loadDailyDigestApproval();
      }
    });

    this.addCommand({
      id: "refresh-knowledge-steward-pending-approvals",
      name: "Refresh pending approvals",
      callback: async () => {
        await this.refreshPendingApprovals();
      }
    });

    this.addCommand({
      id: "open-knowledge-steward-approval-demo",
      name: "Open approval demo",
      callback: async () => {
        await this.openApprovalDemo();
      }
    });

    this.addSettingTab(new KnowledgeStewardSettingTab(this.app, this));
    void this.backendRuntime.maybeAutoStartBackend();
  }

  async onunload(): Promise<void> {
    this.backendRuntime.dispose();
    await this.app.workspace.detachLeavesOfType(KNOWLEDGE_STEWARD_VIEW_TYPE);
  }

  async loadSettings(): Promise<void> {
    this.settings = {
      ...DEFAULT_SETTINGS,
      ...(await this.loadData())
    };
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }

  private get client(): KnowledgeStewardApiClient {
    return new KnowledgeStewardApiClient(
      this.settings.backendUrl,
      this.settings.requestTimeoutMs
    );
  }

  private async activateView(): Promise<KnowledgeStewardView | null> {
    const { workspace } = this.app;
    let leaf: WorkspaceLeaf | null = null;

    const leaves = workspace.getLeavesOfType(KNOWLEDGE_STEWARD_VIEW_TYPE);
    if (leaves.length > 0) {
      leaf = leaves[0];
    } else {
      leaf = workspace.getRightLeaf(false);
      await leaf?.setViewState({
        type: KNOWLEDGE_STEWARD_VIEW_TYPE,
        active: true
      });
    }

    if (leaf) {
      workspace.revealLeaf(leaf);
      const view = leaf.view;
      if (view instanceof KnowledgeStewardView) {
        return view;
      }
    }
    return null;
  }

  private async pingBackend(): Promise<void> {
    const view = await this.activateView();
    const snapshot = await this.backendRuntime.refreshStatus();
    view?.setBackendStatus(snapshot);

    if (snapshot.health) {
      new Notice(
        `Knowledge Steward backend OK. Sample notes: ${snapshot.health.sample_vault.note_count}`
      );
      return;
    }

    new Notice(`Knowledge Steward backend unavailable: ${snapshot.status_message}`);
  }

  private async openApprovalDemo(): Promise<void> {
    const view = await this.activateView();
    if (!view) {
      new Notice("Knowledge Steward panel could not be opened.");
      return;
    }

    // 虽然当前已经有真实 pending inbox，但 demo 入口仍保留，
    // 作为后端不可用时的离线审批面板验证后备，不让 UI 调试路径被启动问题卡死。
    view.setApprovalContext(buildApprovalDemoContext());
    new Notice("Knowledge Steward approval demo loaded.");
  }

  private async refreshPendingApprovals(): Promise<void> {
    const view = await this.activateView();
    if (!view) {
      new Notice("Knowledge Steward panel could not be opened.");
      return;
    }

    await view.refreshPendingApprovals();
  }

  private async loadDailyDigestApproval(): Promise<void> {
    const view = await this.activateView();
    if (!view) {
      new Notice("Knowledge Steward panel could not be opened.");
      return;
    }

    try {
      const result = await this.client.invokeWorkflow({
        action_type: "daily_digest",
        require_approval: true,
        metadata: {
          trigger: "plugin_approval_panel",
          approval_mode: "proposal"
        }
      });
      this.applyWorkflowApprovalResult(view, result);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      view.setApprovalStatusMessage(
        `Failed to load a real approval proposal from DAILY_DIGEST: ${message}`
      );
      new Notice(`Knowledge Steward approval load failed: ${message}`);
    }
  }

  private async startBackend(): Promise<void> {
    const view = await this.activateView();
    const snapshot = await this.backendRuntime.startBackend();
    view?.setBackendStatus(snapshot);

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

  private applyWorkflowApprovalResult(
    view: KnowledgeStewardView,
    result: WorkflowInvokeResponse
  ): void {
    if (result.status === "waiting_for_approval" && result.proposal) {
      view.setApprovalContext({
        threadId: result.thread_id,
        proposal: result.proposal,
        sourceLabel: "workflow:daily_digest",
        loadedAt: new Date().toISOString(),
        serverBacked: true
      });
      void view.refreshPendingApprovals();
      new Notice("Knowledge Steward loaded a real DAILY_DIGEST approval proposal.");
      return;
    }

    view.setApprovalStatusMessage(
      `${result.message} Thread: ${result.thread_id}.`
    );
    new Notice("Knowledge Steward did not receive a pending approval proposal.");
  }
}

function buildApprovalDemoContext(): ApprovalPanelContext {
  const patchOps: PatchOp[] = [
    {
      op: "merge_frontmatter",
      target_path: "日常/2026-03-14.md",
      payload: {
        tags: ["review", "stewarded"],
        aliases: ["3月14日复盘"]
      }
    },
    {
      op: "insert_under_heading",
      target_path: "日常/2026-03-14.md",
      payload: {
        heading: "## Open Questions",
        content:
          "- 为什么今天的 ingest 结果与预期不一致？\n- 下次复盘前需要补哪条证据链？"
      }
    }
  ];

  const proposal: Proposal = {
    proposal_id: "prop_demo_approval_panel",
    action_type: "daily_digest",
    target_note_path: "日常/2026-03-14.md",
    summary: "为今日日志补齐标签，并在 Open Questions 下追加两条待追踪问题。",
    risk_level: "medium",
    evidence: [
      {
        source_path: "日常/2026-03-14.md",
        heading_path: "## 今日复盘",
        chunk_id: "chunk_demo_digest_1",
        reason: "原笔记已经出现复盘段落，但缺少结构化待跟进问题。"
      },
      {
        source_path: "学习记录/LangGraph checkpoint.md",
        heading_path: "## 风险",
        chunk_id: "chunk_demo_digest_2",
        reason: "近期学习记录中反复提到 checkpoint 恢复风险，需要被拉入日复盘。"
      }
    ],
    patch_ops: patchOps,
    safety_checks: {
      before_hash: "sha256:demo-before-hash",
      max_changed_lines: 14,
      contains_delete: false
    }
  };

  return {
    threadId: "thread_demo_approval_panel",
    proposal,
    sourceLabel: "local_demo_command",
    loadedAt: new Date().toISOString(),
    serverBacked: false
  };
}
