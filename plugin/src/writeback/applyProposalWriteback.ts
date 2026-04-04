import { createHash } from "crypto";

import {
  TFile,
  type App
} from "obsidian";

import type { Proposal, WritebackResult } from "../contracts";
import {
  applyAddWikilink,
  applyInsertUnderHeading,
  applyReplaceSection,
  computeSha256Hash,
  extractAddWikilinkPayload,
  extractHeadingInsertPayload,
  extractReplaceSectionPayload,
  frontmatterContainsPatch,
  isPlainRecord,
  mergeFrontmatterValue,
  normalizePatchOp,
  normalizeWikilinkTargetPath,
  preparePatchOpsForExecution,
  sectionContainsInsertedContent,
  type NormalizedPatchOp
} from "./helpers";
import { normalizeWritebackTargetPath } from "./pathSemantics.ts";

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
  let canonicalProposal: Proposal | null = null;
  try {
    const canonicalTargetNotePath = normalizeWritebackTargetPath(app, proposal.target_note_path);
    canonicalProposal = {
      ...proposal,
      target_note_path: canonicalTargetNotePath,
      patch_ops: proposal.patch_ops
    };
    if (proposal.patch_ops.length === 0) {
      canonicalProposal = {
        ...canonicalProposal,
        patch_ops: []
      };
      return buildFailedWritebackExecution(canonicalProposal, {
        error: "The proposal does not contain any patch ops."
      });
    }

    const normalizedPatchOps = proposal.patch_ops.map((patchOp) => normalizePatchOp(patchOp));
    const canonicalPatchOps = normalizedPatchOps.map((patchOp) => ({
      ...patchOp,
      target_path: normalizeWritebackTargetPath(app, patchOp.target_path)
    }));
    canonicalProposal = {
      ...proposal,
      target_note_path: canonicalTargetNotePath,
      patch_ops: canonicalPatchOps
    };
    const targetFile = resolveTargetFile(app, canonicalTargetNotePath);
    const preparedPatchOps = preparePatchOpsForExecution(
      canonicalPatchOps,
      (linkedNotePath) => resolveExistingFile(app, linkedNotePath, "Linked note").path
    );

    for (const patchOp of preparedPatchOps) {
      const patchTarget = normalizeWritebackTargetPath(app, patchOp.target_path);
      if (patchTarget !== canonicalTargetNotePath) {
        return buildFailedWritebackExecution(canonicalProposal ?? proposal, {
          error: "Current writeback executor only supports patch ops targeting a single note."
        });
      }
    }

    const currentHash = await computeFileHash(app, targetFile);
    const currentMarkdown = await app.vault.cachedRead(targetFile);

    const preflightError = validatePatchPlan(currentMarkdown, preparedPatchOps);
    if (preflightError) {
      return buildFailedWritebackExecution(canonicalProposal ?? proposal, {
        beforeHash: currentHash,
        error: preflightError
      });
    }

    const expectedBeforeHash = proposal.safety_checks.before_hash;
    if (expectedBeforeHash && currentHash !== expectedBeforeHash) {
      if (await isProposalAlreadyApplied(app, targetFile, preparedPatchOps)) {
        return buildSuccessfulWritebackExecution(
          {
            applied: true,
            target_note_path: canonicalTargetNotePath,
            before_hash: expectedBeforeHash,
            after_hash: currentHash,
            applied_patch_ops: canonicalPatchOps,
            error: null
          },
          null
        );
      }

      return buildFailedWritebackExecution(canonicalProposal ?? proposal, {
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
    await executePatchPlan(app, targetFile, preparedPatchOps);
    const afterHash = await computeFileHash(app, targetFile);
    rollbackContext.after_hash = afterHash;
    return buildSuccessfulWritebackExecution(
      {
        applied: true,
        target_note_path: canonicalTargetNotePath,
        before_hash: expectedBeforeHash ?? currentHash,
        after_hash: afterHash,
        applied_patch_ops: canonicalPatchOps,
        error: null
      },
      rollbackContext
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return buildFailedWritebackExecution(canonicalProposal ?? proposal, {
      error: message
    });
  }
}

export async function rollbackProposalWriteback(
  app: App,
  proposal: Proposal,
  rollbackContext: LocalRollbackContext
): Promise<WritebackResult> {
  let canonicalTargetNotePath: string | null = null;
  try {
    canonicalTargetNotePath = normalizeWritebackTargetPath(app, proposal.target_note_path);
    const targetFile = resolveTargetFile(app, canonicalTargetNotePath);
    const currentHash = await computeFileHash(app, targetFile);
    const expectedAfterHash = rollbackContext.after_hash;
    if (expectedAfterHash && currentHash !== expectedAfterHash) {
      return buildFailedWritebackResult({
        ...proposal,
        target_note_path: canonicalTargetNotePath
      }, {
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
      return buildFailedWritebackResult({
        ...proposal,
        target_note_path: canonicalTargetNotePath
      }, {
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
      target_note_path: canonicalTargetNotePath,
      before_hash: currentHash,
      after_hash: afterHash,
      applied_patch_ops: [],
      error: null
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const fallbackTargetNotePath = canonicalTargetNotePath ?? proposal.target_note_path;
    return buildFailedWritebackResult({
      ...proposal,
      target_note_path: fallbackTargetNotePath
    }, {
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

    if (patchOp.normalizedOp === "insert_under_heading") {
      const insertPayload = extractHeadingInsertPayload(patchOp);
      workingMarkdown = applyInsertUnderHeading(workingMarkdown, insertPayload);
      markdownDirty = true;
      continue;
    }

    if (patchOp.normalizedOp === "replace_section") {
      const replacePayload = extractReplaceSectionPayload(patchOp);
      workingMarkdown = applyReplaceSection(workingMarkdown, replacePayload);
      markdownDirty = true;
      continue;
    }

    if (patchOp.normalizedOp === "add_wikilink") {
      const wikilinkPayload = extractAddWikilinkPayload(patchOp);
      workingMarkdown = applyAddWikilink(workingMarkdown, {
        heading: wikilinkPayload.heading,
        linked_note_path: wikilinkPayload.linked_note_path
      });
      markdownDirty = true;
      continue;
    }

    throw new Error(`Unsupported patch op: ${patchOp.normalizedOp}`);
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

    if (patchOp.normalizedOp === "insert_under_heading") {
      const insertPayload = extractHeadingInsertPayload(patchOp);
      if (!sectionContainsInsertedContent(currentMarkdown, insertPayload)) {
        return false;
      }
      continue;
    }

    if (patchOp.normalizedOp === "replace_section") {
      const replacePayload = extractReplaceSectionPayload(patchOp);
      if (applyReplaceSection(currentMarkdown, replacePayload) !== currentMarkdown) {
        return false;
      }
      continue;
    }

    if (patchOp.normalizedOp === "add_wikilink") {
      const wikilinkPayload = extractAddWikilinkPayload(patchOp);
      const normalizedTargetPath = normalizeWikilinkTargetPath(
        wikilinkPayload.linked_note_path
      );
      if (!sectionContainsWikilinkTarget(currentMarkdown, wikilinkPayload.heading, normalizedTargetPath)) {
        return false;
      }
      continue;
    }

    return false;
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
      if (patchOp.normalizedOp === "insert_under_heading") {
        const insertPayload = extractHeadingInsertPayload(patchOp);
        workingMarkdown = applyInsertUnderHeading(workingMarkdown, insertPayload);
        continue;
      }

      if (patchOp.normalizedOp === "replace_section") {
        const replacePayload = extractReplaceSectionPayload(patchOp);
        workingMarkdown = applyReplaceSection(workingMarkdown, replacePayload);
        continue;
      }

      if (patchOp.normalizedOp === "add_wikilink") {
        const wikilinkPayload = extractAddWikilinkPayload(patchOp);
        workingMarkdown = applyAddWikilink(workingMarkdown, wikilinkPayload);
        continue;
      }

      return `Unsupported patch op: ${patchOp.normalizedOp}`;
    } catch (error) {
      return error instanceof Error ? error.message : String(error);
    }
  }

  return null;
}

function resolveTargetFile(app: App, targetPath: string): TFile {
  return resolveExistingFile(app, targetPath, "Target note");
}

function resolveExistingFile(app: App, targetPath: string, label: string): TFile {
  const vaultPath = normalizeWritebackTargetPath(app, targetPath);
  const abstractFile = app.vault.getAbstractFileByPath(vaultPath);
  if (!(abstractFile instanceof TFile)) {
    throw new Error(`${label} was not found in the current vault: ${targetPath}`);
  }
  return abstractFile;
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

function sectionContainsWikilinkTarget(
  markdown: string,
  heading: string,
  normalizedTargetPath: string
): boolean {
  const lines = markdown.split(/\r?\n/);
  const bounds = findHeadingSectionBounds(lines, heading);
  if (!bounds) {
    return false;
  }

  const sectionText = lines.slice(bounds.headingIndex + 1, bounds.sectionEnd).join("\n");
  const wikilinkPattern = /\[\[([^\]]+)\]\]/g;
  for (const match of sectionText.matchAll(wikilinkPattern)) {
    if (normalizeWikilinkTargetPath(match[1]) === normalizedTargetPath) {
      return true;
    }
  }
  return false;
}

function findHeadingSectionBounds(
  lines: string[],
  heading: string
): { headingIndex: number; sectionEnd: number } | null {
  const normalizedHeading = heading.trim();
  const headingIndex = lines.findIndex((line) => line.trim() === normalizedHeading);
  if (headingIndex < 0) {
    return null;
  }

  const headingMatch = /^#{1,6}\s+/.exec(normalizedHeading);
  if (!headingMatch) {
    return null;
  }
  const headingLevel = headingMatch[0].trimEnd().length;

  let sectionEnd = lines.length;
  for (let index = headingIndex + 1; index < lines.length; index += 1) {
    const currentMatch = /^(#{1,6})\s+/.exec(lines[index].trim());
    if (currentMatch && currentMatch[1].length <= headingLevel) {
      sectionEnd = index;
      break;
    }
  }

  return {
    headingIndex,
    sectionEnd
  };
}
