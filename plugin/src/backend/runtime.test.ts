import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import test from "node:test";

import type { KnowledgeStewardApiClient } from "../api/client";
import type { HealthResponse } from "../contracts";
import type { KnowledgeStewardSettings } from "../settings";
import { KnowledgeStewardBackendRuntime } from "./runtime.ts";

class FakeReadable extends EventEmitter {
  setEncoding(): this {
    return this;
  }
}

class FakeChildProcess extends EventEmitter {
  pid: number;
  exitCode: number | null = null;
  stdout = new FakeReadable();
  stderr = new FakeReadable();

  constructor(pid: number) {
    super();
    this.pid = pid;
  }
}

function createSettings(overrides: Partial<KnowledgeStewardSettings> = {}): KnowledgeStewardSettings {
  return {
    backendUrl: "http://127.0.0.1:8787",
    requestTimeoutMs: 5000,
    backendStartCommand: "python -m app.main",
    backendStartWorkingDirectory: "/tmp/backend",
    backendStartupTimeoutMs: 100,
    backendHealthCheckIntervalMs: 0,
    autoStartBackendOnLoad: false,
    ...overrides
  };
}

function createHealthResponse(): HealthResponse {
  return {
    service_name: "knowledge-steward-backend",
    version: "0.1.0",
    status: "ok",
    model_strategy: "cloud_primary_local_compatible",
    supported_actions: ["ask_qa", "ingest_steward", "daily_digest"],
    providers: [],
    sample_vault: {
      path: "/tmp/vault",
      note_count: 1,
      frontmatter_note_count: 0,
      wikilink_count: 0,
      task_checkbox_count: 0,
      template_family_counts: {}
    },
    generated_at: new Date().toISOString()
  };
}

test("startBackend returns unavailable when startup command is missing", async () => {
  const settings = createSettings({ backendStartCommand: "" });
  let spawnCalled = false;
  const runtime = new KnowledgeStewardBackendRuntime(
    () => ({
      getHealth: async () => {
        throw new Error("connect ECONNREFUSED");
      }
    }) as KnowledgeStewardApiClient,
    () => settings,
    {
      spawnCommand: () => {
        spawnCalled = true;
        return new FakeChildProcess(101) as never;
      },
      sleep: async () => {}
    }
  );

  const snapshot = await runtime.startBackend();

  assert.equal(snapshot.status, "unavailable");
  assert.match(snapshot.status_message, /Configure a backend start command/);
  assert.equal(spawnCalled, false);
});

test("startBackend marks runtime ready after health probe succeeds", async () => {
  const settings = createSettings();
  const healthChecks: Array<() => Promise<HealthResponse>> = [
    async () => {
      throw new Error("not ready yet");
    },
    async () => {
      throw new Error("still booting");
    },
    async () => createHealthResponse()
  ];
  const spawned: string[] = [];
  const runtime = new KnowledgeStewardBackendRuntime(
    () => ({
      getHealth: async () => {
        const next = healthChecks.shift();
        if (!next) {
          throw new Error("health probe queue exhausted");
        }
        return next();
      }
    }) as KnowledgeStewardApiClient,
    () => settings,
    {
      spawnCommand: (command) => {
        spawned.push(command);
        return new FakeChildProcess(222) as never;
      },
      sleep: async () => {}
    }
  );

  const snapshot = await runtime.startBackend();

  assert.equal(spawned.length, 1);
  assert.equal(snapshot.status, "ready");
  assert.equal(snapshot.tracked_pid, 222);
  assert.equal(snapshot.health?.service_name, "knowledge-steward-backend");
});

test("startBackend reports failed when tracked process exits before ready", async () => {
  const settings = createSettings();
  const child = new FakeChildProcess(333);
  let emittedExit = false;
  const runtime = new KnowledgeStewardBackendRuntime(
    () => ({
      getHealth: async () => {
        throw new Error("still booting");
      }
    }) as KnowledgeStewardApiClient,
    () => settings,
    {
      spawnCommand: () => child as never,
      sleep: async () => {
        if (!emittedExit) {
          emittedExit = true;
          child.stderr.emit("data", "Traceback: boom\n");
          child.exitCode = 1;
          child.emit("exit", 1, null);
        }
      }
    }
  );

  const snapshot = await runtime.startBackend();

  assert.equal(snapshot.status, "failed");
  assert.match(snapshot.status_message, /exited before \/health became ready/);
  assert.equal(snapshot.last_exit_code, 1);
  assert.ok(snapshot.recent_output.some((line) => line.includes("Traceback: boom")));
});
