import { spawn, type ChildProcess, type SpawnOptions } from "child_process";

import {
  formatApiErrorMessage,
  type KnowledgeStewardApiClient
} from "../api/client.ts";
import type { HealthResponse } from "../contracts.ts";
import type { KnowledgeStewardSettings } from "../settings.ts";

const MAX_RECENT_OUTPUT_LINES = 20;

export type BackendRuntimeStatus =
  | "checking"
  | "starting"
  | "ready"
  | "unavailable"
  | "failed";

export interface BackendRuntimeSnapshot {
  status: BackendRuntimeStatus;
  status_message: string;
  health: HealthResponse | null;
  startup_command_configured: boolean;
  auto_start_enabled: boolean;
  tracked_pid: number | null;
  last_checked_at: string | null;
  last_started_at: string | null;
  last_ready_at: string | null;
  last_error: string | null;
  last_exit_code: number | null;
  recent_output: string[];
}

type SnapshotListener = (snapshot: BackendRuntimeSnapshot) => void;

interface BackendRuntimeDeps {
  spawnCommand?: (command: string, options: SpawnOptions) => ChildProcess;
  sleep?: (ms: number) => Promise<void>;
}

export class KnowledgeStewardBackendRuntime {
  private readonly getClient: () => KnowledgeStewardApiClient;
  private readonly getSettings: () => KnowledgeStewardSettings;
  private snapshot: BackendRuntimeSnapshot;
  private readonly listeners = new Set<SnapshotListener>();
  private readonly spawnCommand: (command: string, options: SpawnOptions) => ChildProcess;
  private readonly sleep: (ms: number) => Promise<void>;
  private activeChild: ChildProcess | null = null;
  private healthCheckPromise: Promise<BackendRuntimeSnapshot> | null = null;
  private startPromise: Promise<BackendRuntimeSnapshot> | null = null;
  private disposed = false;

  constructor(
    getClient: () => KnowledgeStewardApiClient,
    getSettings: () => KnowledgeStewardSettings,
    deps: BackendRuntimeDeps = {}
  ) {
    this.getClient = getClient;
    this.getSettings = getSettings;
    this.spawnCommand = deps.spawnCommand ?? spawn;
    this.sleep = deps.sleep ?? defaultSleep;
    this.snapshot = this.buildInitialSnapshot();
  }

  subscribe(listener: SnapshotListener): () => void {
    this.listeners.add(listener);
    listener(this.getSnapshot());
    return () => {
      this.listeners.delete(listener);
    };
  }

  getSnapshot(): BackendRuntimeSnapshot {
    return cloneSnapshot(this.snapshot);
  }

  async refreshStatus(): Promise<BackendRuntimeSnapshot> {
    if (this.healthCheckPromise) {
      return this.healthCheckPromise;
    }

    const preserveStartingState = this.snapshot.status === "starting";
    if (!preserveStartingState) {
      this.updateSnapshot({
        status: "checking",
        status_message: "Checking backend health...",
        last_error: null,
        startup_command_configured: hasStartupCommand(this.getSettings()),
        auto_start_enabled: this.getSettings().autoStartBackendOnLoad
      });
    }

    this.healthCheckPromise = this.probeBackendHealth({ preserveStartingState })
      .finally(() => {
        this.healthCheckPromise = null;
      });
    return this.healthCheckPromise;
  }

  async maybeAutoStartBackend(): Promise<BackendRuntimeSnapshot> {
    if (this.getSettings().autoStartBackendOnLoad) {
      return this.startBackend();
    }
    return this.refreshStatus();
  }

  async startBackend(): Promise<BackendRuntimeSnapshot> {
    if (this.startPromise) {
      return this.startPromise;
    }

    const healthSnapshot = await this.refreshStatus();
    if (healthSnapshot.status === "ready") {
      return healthSnapshot;
    }

    const settings = this.getSettings();
    if (!hasStartupCommand(settings)) {
      const message = (
        "Backend is unavailable. Configure a backend start command in settings or start it manually."
      );
      this.updateSnapshot({
        status: "unavailable",
        status_message: message,
        last_error: message,
        startup_command_configured: false,
        auto_start_enabled: settings.autoStartBackendOnLoad
      });
      return this.getSnapshot();
    }

    this.startPromise = this.launchAndWaitUntilHealthy()
      .finally(() => {
        this.startPromise = null;
      });
    return this.startPromise;
  }

  dispose(): void {
    this.disposed = true;
    this.listeners.clear();
  }

  private buildInitialSnapshot(): BackendRuntimeSnapshot {
    const settings = this.getSettings();
    return {
      status: "checking",
      status_message: "Backend status has not been checked yet.",
      health: null,
      startup_command_configured: hasStartupCommand(settings),
      auto_start_enabled: settings.autoStartBackendOnLoad,
      tracked_pid: null,
      last_checked_at: null,
      last_started_at: null,
      last_ready_at: null,
      last_error: null,
      last_exit_code: null,
      recent_output: []
    };
  }

  private async probeBackendHealth(options: {
    preserveStartingState: boolean;
  }): Promise<BackendRuntimeSnapshot> {
    const settings = this.getSettings();
    const checkedAt = new Date().toISOString();
    try {
      const health = await this.getClient().getHealth();
      // 只有真正命中 `/health` 才把状态推进到 ready，避免把“子进程已拉起”
      // 误判成“后端可用”，否则面试里一追问 readiness 定义就会露出控制面是假的。
      this.updateSnapshot({
        status: "ready",
        status_message: "Backend is ready.",
        health,
        startup_command_configured: hasStartupCommand(settings),
        auto_start_enabled: settings.autoStartBackendOnLoad,
        tracked_pid: this.activeChild?.pid ?? this.snapshot.tracked_pid,
        last_checked_at: checkedAt,
        last_ready_at: checkedAt,
        last_error: null
      });
      return this.getSnapshot();
    } catch (error) {
      const message = formatApiErrorMessage(error);
      if (options.preserveStartingState) {
        this.updateSnapshot({
          status: "starting",
          status_message: "Backend process launched. Waiting for /health to become ready...",
          health: null,
          startup_command_configured: hasStartupCommand(settings),
          auto_start_enabled: settings.autoStartBackendOnLoad,
          last_checked_at: checkedAt,
          last_error: message
        });
        return this.getSnapshot();
      }

      this.updateSnapshot({
        status: this.snapshot.status === "failed" ? "failed" : "unavailable",
        status_message: buildUnavailableMessage({
          startupCommandConfigured: hasStartupCommand(settings),
          errorMessage: message
        }),
        health: null,
        startup_command_configured: hasStartupCommand(settings),
        auto_start_enabled: settings.autoStartBackendOnLoad,
        tracked_pid: this.activeChild?.pid ?? null,
        last_checked_at: checkedAt,
        last_error: message
      });
      return this.getSnapshot();
    }
  }

  private async launchAndWaitUntilHealthy(): Promise<BackendRuntimeSnapshot> {
    const settings = this.getSettings();
    const startedAt = new Date().toISOString();

    if (this.activeChild && this.activeChild.exitCode === null) {
      this.updateSnapshot({
        status: "starting",
        status_message: "A tracked backend process is already running. Waiting for /health...",
        startup_command_configured: true,
        auto_start_enabled: settings.autoStartBackendOnLoad,
        tracked_pid: this.activeChild.pid ?? null,
        last_started_at: startedAt,
        last_error: null,
        last_exit_code: null
      });
      return this.waitUntilHealthy();
    }

    this.updateSnapshot({
      status: "starting",
      status_message: "Launching local backend and waiting for /health...",
      startup_command_configured: true,
      auto_start_enabled: settings.autoStartBackendOnLoad,
      tracked_pid: null,
      last_started_at: startedAt,
      last_error: null,
      last_exit_code: null
    });

    let child: ChildProcess;
    try {
      child = this.spawnCommand(settings.backendStartCommand.trim(), {
        cwd: normalizeOptionalSetting(settings.backendStartWorkingDirectory),
        shell: resolveShell(),
        windowsHide: true,
        stdio: ["ignore", "pipe", "pipe"]
      });
    } catch (error) {
      const message = `Backend launch failed before spawn: ${formatApiErrorMessage(error)}`;
      this.recordProcessOutput(`[launcher] ${message}`);
      this.updateSnapshot({
        status: "failed",
        status_message: message,
        tracked_pid: null,
        last_error: message
      });
      return this.getSnapshot();
    }

    this.activeChild = child;
    this.attachChildListeners(child);

    this.updateSnapshot({
      tracked_pid: child.pid ?? null
    });

    return this.waitUntilHealthy();
  }

  private attachChildListeners(child: ChildProcess): void {
    attachReadable(child.stdout, "stdout", (line) => {
      this.recordProcessOutput(line);
    });
    attachReadable(child.stderr, "stderr", (line) => {
      this.recordProcessOutput(line);
    });

    child.once("error", (error) => {
      const message = `Backend process error: ${formatApiErrorMessage(error)}`;
      this.recordProcessOutput(`[process] ${message}`);
      if (this.activeChild === child) {
        this.activeChild = null;
      }
      this.updateSnapshot({
        status: "failed",
        status_message: message,
        tracked_pid: null,
        last_error: message
      });
    });

    child.once("exit", (code, signal) => {
      if (this.activeChild === child) {
        this.activeChild = null;
      }
      const exitMessage = signal
        ? `Backend process exited with signal ${signal}.`
        : `Backend process exited with code ${code ?? 0}.`;
      this.recordProcessOutput(`[process] ${exitMessage}`);

      // 如果进程在 ready 之前就退出，必须明确标成 failed；
      // 否则用户只会看到“后端不可用”，却不知道是启动失败还是根本没启动成功。
      if (this.snapshot.status === "starting") {
        this.updateSnapshot({
          status: "failed",
          status_message: `Backend process exited before /health became ready. ${exitMessage}`,
          tracked_pid: null,
          last_error: exitMessage,
          last_exit_code: code ?? null
        });
        return;
      }

      this.updateSnapshot({
        status: this.snapshot.status === "ready" ? "checking" : this.snapshot.status,
        status_message: this.snapshot.status === "ready"
          ? "Tracked backend process exited. Re-checking /health..."
          : this.snapshot.status_message,
        tracked_pid: null,
        last_error: exitMessage,
        last_exit_code: code ?? null
      });

      if (!this.disposed) {
        void this.refreshStatus();
      }
    });
  }

  private async waitUntilHealthy(): Promise<BackendRuntimeSnapshot> {
    const settings = this.getSettings();
    const deadline = Date.now() + settings.backendStartupTimeoutMs;

    while (Date.now() <= deadline) {
      if (this.snapshot.status === "failed") {
        return this.getSnapshot();
      }

      try {
        const health = await this.getClient().getHealth();
        const checkedAt = new Date().toISOString();
        this.updateSnapshot({
          status: "ready",
          status_message: "Backend is ready.",
          health,
          tracked_pid: this.activeChild?.pid ?? this.snapshot.tracked_pid,
          last_checked_at: checkedAt,
          last_ready_at: checkedAt,
          last_error: null
        });
        return this.getSnapshot();
      } catch (error) {
        const checkedAt = new Date().toISOString();
        if (this.snapshot.status === "failed") {
          return this.getSnapshot();
        }
        this.updateSnapshot({
          status: "starting",
          status_message: "Backend process launched. Waiting for /health to become ready...",
          health: null,
          tracked_pid: this.activeChild?.pid ?? this.snapshot.tracked_pid,
          last_checked_at: checkedAt,
          last_error: formatApiErrorMessage(error)
        });
      }

      await this.sleep(settings.backendHealthCheckIntervalMs);
    }

    const timeoutMessage = (
      `Backend start timed out after ${settings.backendStartupTimeoutMs}ms `
      + "without a healthy /health response."
    );
    const richTimeoutMessage = appendRecentOutput(timeoutMessage, this.snapshot.recent_output);
    this.updateSnapshot({
      status: "failed",
      status_message: richTimeoutMessage,
      last_error: richTimeoutMessage
    });
    return this.getSnapshot();
  }

  private recordProcessOutput(line: string): void {
    const normalizedLines = line
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);
    if (normalizedLines.length === 0) {
      return;
    }

    const recentOutput = [
      ...this.snapshot.recent_output,
      ...normalizedLines
    ].slice(-MAX_RECENT_OUTPUT_LINES);

    this.updateSnapshot({ recent_output: recentOutput });
  }

  private updateSnapshot(patch: Partial<BackendRuntimeSnapshot>): void {
    const settings = this.getSettings();
    this.snapshot = {
      ...this.snapshot,
      startup_command_configured: hasStartupCommand(settings),
      auto_start_enabled: settings.autoStartBackendOnLoad,
      ...patch
    };

    const nextSnapshot = this.getSnapshot();
    for (const listener of this.listeners) {
      listener(nextSnapshot);
    }
  }
}

function attachReadable(
  stream: NodeJS.ReadableStream | null | undefined,
  channel: "stdout" | "stderr",
  onLine: (line: string) => void
): void {
  if (!stream) {
    return;
  }
  if ("setEncoding" in stream && typeof stream.setEncoding === "function") {
    stream.setEncoding("utf8");
  }
  stream.on("data", (chunk: string | Buffer) => {
    onLine(`[${channel}] ${String(chunk)}`);
  });
}

function buildUnavailableMessage(input: {
  startupCommandConfigured: boolean;
  errorMessage: string;
}): string {
  if (!input.startupCommandConfigured) {
    return (
      "Backend is unavailable. Configure a backend start command in settings or start it manually. "
      + `Last probe: ${input.errorMessage}`
    );
  }
  return (
    "Backend is unavailable. Use Start backend or verify the configured launch command. "
    + `Last probe: ${input.errorMessage}`
  );
}

function appendRecentOutput(message: string, recentOutput: string[]): string {
  const tail = recentOutput.at(-1);
  if (!tail) {
    return message;
  }
  return `${message} Recent output: ${tail}`;
}

function cloneSnapshot(snapshot: BackendRuntimeSnapshot): BackendRuntimeSnapshot {
  return {
    ...snapshot,
    recent_output: [...snapshot.recent_output]
  };
}

function defaultSleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    globalThis.setTimeout(resolve, ms);
  });
}

function hasStartupCommand(settings: KnowledgeStewardSettings): boolean {
  return settings.backendStartCommand.trim().length > 0;
}

function normalizeOptionalSetting(value: string): string | undefined {
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : undefined;
}

function resolveShell(): string | true {
  if (process.platform === "win32") {
    return process.env.ComSpec || true;
  }
  return process.env.SHELL || true;
}
