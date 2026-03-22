import { createHash } from "crypto";
import path from "path";

import {
  normalizePath,
  TFile,
  type App
} from "obsidian";

import type { Proposal, WritebackResult } from "../contracts";
import {
  applyInsertUnderHeading,
  computeSha256Hash,
  extractHeadingInsertPayload,
  frontmatterContainsPatch,
  isPlainRecord,
  mergeFrontmatterValue,
  normalizePatchOp,
  sectionContainsInsertedContent,
  type NormalizedPatchOp
} from "./helpers";

export interface LocalRollbackContext {
  before_markdown: string;
  before_hash: string | null;
  after_hash: string | null;
}

export interface LocalWritebackExecution {
  writeback_result: WritebackResult;
  rollback_context: LocalRollbackContext | null;
}

export async function applyProposalWriteback(
  app: App,
  proposal: Proposal
): Promise<LocalWritebackExecution> {
  if (proposal.patch_ops.length === 0) {
    return buildFailedWritebackExecution(proposal, {
      error: "The proposal does not contain any patch ops."
    });
  }

  try {
    const targetFile = resolveTargetFile(app, proposal.target_note_path);
    const normalizedPatchOps = proposal.patch_ops.map((patchOp) => normalizePatchOp(patchOp));

    for (const patchOp of normalizedPatchOps) {
      const patchTarget = resolveVaultPath(app, patchOp.target_path);
      if (patchTarget !== targetFile.path) {
        return buildFailedWritebackExecution(proposal, {
          error: "Current writeback executor only supports patch ops targeting a single note."
        });
      }
    }

    const currentHash = await computeFileHash(app, targetFile);
    const currentMarkdown = await app.vault.cachedRead(targetFile);

    const preflightError = validatePatchPlan(currentMarkdown, normalizedPatchOps);
    if (preflightError) {
      return buildFailedWritebackExecution(proposal, {
        beforeHash: currentHash,
        error: preflightError
      });
    }

    const expectedBeforeHash = proposal.safety_checks.before_hash;
    if (expectedBeforeHash && currentHash !== expectedBeforeHash) {
      if (await isProposalAlreadyApplied(app, targetFile, normalizedPatchOps)) {
        return buildSuccessfulWritebackExecution(
          {
            applied: true,
            target_note_path: proposal.target_note_path,
            before_hash: expectedBeforeHash,
            after_hash: currentHash,
            applied_patch_ops: proposal.patch_ops,
            error: null
          },
          null
        );
      }

      return buildFailedWritebackExecution(proposal, {
        beforeHash: currentHash,
        error: (
          `before_hash mismatch for ${proposal.target_note_path}. `
          + `expected ${expectedBeforeHash}, got ${currentHash}.`
        )
      });
    }

    // rollback 只能对“当前插件进程亲手执行的那次写回”负责。
    // 因此必须在任何真实落盘前先抓住原始 markdown；一旦 frontmatter API 改写完成，
    // 老内容就无法再从 proposal patch 里可靠反推出来。
    const rollbackContext: LocalRollbackContext = {
      before_markdown: currentMarkdown,
      before_hash: expectedBeforeHash ?? currentHash,
      after_hash: null
    };
    await executePatchPlan(app, targetFile, normalizedPatchOps);
    const afterHash = await computeFileHash(app, targetFile);
    rollbackContext.after_hash = afterHash;
    return buildSuccessfulWritebackExecution(
      {
        applied: true,
        target_note_path: proposal.target_note_path,
        before_hash: expectedBeforeHash ?? currentHash,
        after_hash: afterHash,
        applied_patch_ops: proposal.patch_ops,
        error: null
      },
      rollbackContext
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return buildFailedWritebackExecution(proposal, {
      error: message
    });
  }
}

export async function rollbackProposalWriteback(
  app: App,
  proposal: Proposal,
  rollbackContext: LocalRollbackContext
): Promise<WritebackResult> {
  try {
    const targetFile = resolveTargetFile(app, proposal.target_note_path);
    const currentHash = await computeFileHash(app, targetFile);
    const expectedAfterHash = rollbackContext.after_hash;
    if (expectedAfterHash && currentHash !== expectedAfterHash) {
      return buildFailedWritebackResult(proposal, {
        beforeHash: currentHash,
        error: (
          `Rollback refused for ${proposal.target_note_path}. `
          + `expected current hash ${expectedAfterHash}, got ${currentHash}.`
        )
      });
    }

    const snapshotHash = computeSha256Hash(rollbackContext.before_markdown);
    if (
      rollbackContext.before_hash !== null
      && snapshotHash !== rollbackContext.before_hash
    ) {
      return buildFailedWritebackResult(proposal, {
        beforeHash: currentHash,
        error: (
          `Rollback snapshot for ${proposal.target_note_path} is inconsistent with `
          + `the original before_hash.`
        )
      });
    }

    // 只有当文件仍停留在“那次写回后的精确状态”时才允许整文恢复，
    // 否则宁可拒绝撤销，也不覆盖用户后来手动改的内容。
    await app.vault.modify(targetFile, rollbackContext.before_markdown);
    const afterHash = await computeFileHash(app, targetFile);
    return {
      applied: true,
      target_note_path: proposal.target_note_path,
      before_hash: currentHash,
      after_hash: afterHash,
      applied_patch_ops: [],
      error: null
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return buildFailedWritebackResult(proposal, {
      error: message
    });
  }
}

async function executePatchPlan(
  app: App,
  file: TFile,
  patchOps: NormalizedPatchOp[]
): Promise<void> {
  let workingMarkdown = await app.vault.cachedRead(file);
  let markdownDirty = false;

  for (const patchOp of patchOps) {
    if (patchOp.normalizedOp === "merge_frontmatter") {
      if (!isPlainRecord(patchOp.payload)) {
        throw new Error("merge_frontmatter payload must be a plain object.");
      }

      if (markdownDirty) {
        await app.vault.modify(file, workingMarkdown);
        markdownDirty = false;
        workingMarkdown = await app.vault.cachedRead(file);
      }

      await app.fileManager.processFrontMatter(file, (frontmatter) => {
        const mutableFrontmatter = frontmatter as Record<string, unknown>;
        for (const [key, value] of Object.entries(patchOp.payload)) {
          mutableFrontmatter[key] = mergeFrontmatterValue(
            mutableFrontmatter[key],
            value
          );
        }
      });
      workingMarkdown = await app.vault.cachedRead(file);
      continue;
    }

    const insertPayload = extractHeadingInsertPayload(patchOp);
    workingMarkdown = applyInsertUnderHeading(workingMarkdown, insertPayload);
    markdownDirty = true;
  }

  if (markdownDirty) {
    await app.vault.modify(file, workingMarkdown);
  }
}

async function isProposalAlreadyApplied(
  app: App,
  file: TFile,
  patchOps: NormalizedPatchOp[]
): Promise<boolean> {
  const currentMarkdown = await app.vault.cachedRead(file);
  const currentFrontmatter = app.metadataCache.getFileCache(file)?.frontmatter;

  for (const patchOp of patchOps) {
    if (patchOp.normalizedOp === "merge_frontmatter") {
      if (!isPlainRecord(patchOp.payload) || !isPlainRecord(currentFrontmatter)) {
        return false;
      }
      if (!frontmatterContainsPatch(currentFrontmatter, patchOp.payload)) {
        return false;
      }
      continue;
    }

    const insertPayload = extractHeadingInsertPayload(patchOp);
    if (!sectionContainsInsertedContent(currentMarkdown, insertPayload)) {
      return false;
    }
  }

  return true;
}

function validatePatchPlan(
  currentMarkdown: string,
  patchOps: NormalizedPatchOp[]
): string | null {
  let workingMarkdown = currentMarkdown;

  for (const patchOp of patchOps) {
    if (patchOp.normalizedOp === "merge_frontmatter") {
      if (!isPlainRecord(patchOp.payload)) {
        return "merge_frontmatter payload must be a plain object.";
      }
      continue;
    }

    try {
      const insertPayload = extractHeadingInsertPayload(patchOp);
      workingMarkdown = applyInsertUnderHeading(workingMarkdown, insertPayload);
    } catch (error) {
      return error instanceof Error ? error.message : String(error);
    }
  }

  return null;
}

function resolveTargetFile(app: App, targetPath: string): TFile {
  const vaultPath = resolveVaultPath(app, targetPath);
  const abstractFile = app.vault.getAbstractFileByPath(vaultPath);
  if (!(abstractFile instanceof TFile)) {
    throw new Error(`Target note was not found in the current vault: ${targetPath}`);
  }
  return abstractFile;
}

function resolveVaultPath(app: App, targetPath: string): string {
  if (!path.isAbsolute(targetPath)) {
    return normalizePath(targetPath);
  }

  const adapter = app.vault.adapter as { getBasePath?: () => string };
  if (typeof adapter.getBasePath !== "function") {
    throw new Error(
      "Absolute target paths require a filesystem-backed Obsidian vault adapter."
    );
  }

  const normalizedBasePath = normalizeFilesystemPath(
    path.resolve(adapter.getBasePath())
  );
  const normalizedTargetPath = normalizeFilesystemPath(path.resolve(targetPath));
  if (
    normalizedTargetPath !== normalizedBasePath
    && !normalizedTargetPath.startsWith(`${normalizedBasePath}/`)
  ) {
    throw new Error(
      `Absolute target path is outside the current vault root: ${targetPath}`
    );
  }

  const relativePath = path.relative(normalizedBasePath, normalizedTargetPath);
  return normalizePath(normalizeFilesystemPath(relativePath));
}

async function computeFileHash(app: App, file: TFile): Promise<string> {
  const adapter = app.vault.adapter as {
    readBinary?: (normalizedPath: string) => Promise<ArrayBuffer>;
  };
  if (typeof adapter.readBinary === "function") {
    const buffer = await adapter.readBinary(file.path);
    return createHash("sha256")
      .update(Buffer.from(buffer))
      .digest("hex")
      .replace(/^/, "sha256:");
  }

  const fallbackContent = await app.vault.cachedRead(file);
  return createHash("sha256")
    .update(fallbackContent, "utf8")
    .digest("hex")
    .replace(/^/, "sha256:");
}

function buildFailedWritebackResult(
  proposal: Proposal,
  input: {
    beforeHash?: string | null;
    error: string;
  }
): WritebackResult {
  return {
    applied: false,
    target_note_path: proposal.target_note_path,
    before_hash: input.beforeHash ?? null,
    after_hash: null,
    applied_patch_ops: [],
    error: input.error
  };
}

function buildFailedWritebackExecution(
  proposal: Proposal,
  input: {
    beforeHash?: string | null;
    error: string;
  }
): LocalWritebackExecution {
  return buildSuccessfulWritebackExecution(
    buildFailedWritebackResult(proposal, input),
    null
  );
}

function buildSuccessfulWritebackExecution(
  writebackResult: WritebackResult,
  rollbackContext: LocalRollbackContext | null
): LocalWritebackExecution {
  return {
    writeback_result: writebackResult,
    rollback_context: rollbackContext
  };
}

function normalizeFilesystemPath(value: string): string {
  return value.replace(/\\/g, "/");
}
