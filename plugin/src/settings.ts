import { App, PluginSettingTab, Setting } from "obsidian";

import type KnowledgeStewardPlugin from "./main";

export interface KnowledgeStewardSettings {
  backendUrl: string;
  requestTimeoutMs: number;
  backendStartCommand: string;
  backendStartWorkingDirectory: string;
  backendStartupTimeoutMs: number;
  backendHealthCheckIntervalMs: number;
  autoStartBackendOnLoad: boolean;
}

export const DEFAULT_SETTINGS: KnowledgeStewardSettings = {
  backendUrl: "http://127.0.0.1:8787",
  requestTimeoutMs: 5000,
  backendStartCommand: "",
  backendStartWorkingDirectory: "",
  backendStartupTimeoutMs: 15000,
  backendHealthCheckIntervalMs: 1500,
  autoStartBackendOnLoad: false
};

export class KnowledgeStewardSettingTab extends PluginSettingTab {
  constructor(app: App, private readonly plugin: KnowledgeStewardPlugin) {
    super(app, plugin);
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl("h2", { text: "Knowledge Steward" });

    new Setting(containerEl)
      .setName("Backend URL")
      .setDesc("Local backend base URL")
      .addText((text) =>
        text
          .setPlaceholder("http://127.0.0.1:8787")
          .setValue(this.plugin.settings.backendUrl)
          .onChange(async (value) => {
            this.plugin.settings.backendUrl = value.trim();
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Request timeout (ms)")
      .setDesc("HTTP timeout for backend calls")
      .addText((text) =>
        text
          .setValue(String(this.plugin.settings.requestTimeoutMs))
          .onChange(async (value) => {
            const parsed = Number.parseInt(value, 10);
            if (!Number.isNaN(parsed) && parsed > 0) {
              this.plugin.settings.requestTimeoutMs = parsed;
              await this.plugin.saveSettings();
            }
          })
      );

    new Setting(containerEl)
      .setName("Backend start command")
      .setDesc("Optional local shell command used by the plugin to launch the backend.")
      .addTextArea((text) =>
        text
          .setPlaceholder("source <conda.sh> && conda activate ... && cd backend && python -m app.main")
          .setValue(this.plugin.settings.backendStartCommand)
          .onChange(async (value) => {
            this.plugin.settings.backendStartCommand = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Backend working directory")
      .setDesc("Optional working directory for the launch command. Leave empty if the command handles cd itself.")
      .addText((text) =>
        text
          .setPlaceholder("/absolute/path/to/project")
          .setValue(this.plugin.settings.backendStartWorkingDirectory)
          .onChange(async (value) => {
            this.plugin.settings.backendStartWorkingDirectory = value.trim();
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Backend startup timeout (ms)")
      .setDesc("How long the plugin waits for /health after launching the backend.")
      .addText((text) =>
        text
          .setValue(String(this.plugin.settings.backendStartupTimeoutMs))
          .onChange(async (value) => {
            const parsed = Number.parseInt(value, 10);
            if (!Number.isNaN(parsed) && parsed > 0) {
              this.plugin.settings.backendStartupTimeoutMs = parsed;
              await this.plugin.saveSettings();
            }
          })
      );

    new Setting(containerEl)
      .setName("Backend health poll interval (ms)")
      .setDesc("Poll interval used while the plugin is waiting for the backend to become ready.")
      .addText((text) =>
        text
          .setValue(String(this.plugin.settings.backendHealthCheckIntervalMs))
          .onChange(async (value) => {
            const parsed = Number.parseInt(value, 10);
            if (!Number.isNaN(parsed) && parsed >= 0) {
              this.plugin.settings.backendHealthCheckIntervalMs = parsed;
              await this.plugin.saveSettings();
            }
          })
      );

    new Setting(containerEl)
      .setName("Auto-start backend on plugin load")
      .setDesc("If enabled, the plugin will try to launch the backend automatically when Obsidian loads.")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.autoStartBackendOnLoad)
          .onChange(async (value) => {
            this.plugin.settings.autoStartBackendOnLoad = value;
            await this.plugin.saveSettings();
          })
      );
  }
}
