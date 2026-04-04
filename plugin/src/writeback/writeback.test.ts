import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";

import { applyProposalWriteback, rollbackProposalWriteback } from "./applyProposalWriteback.ts";
import {
  applyInsertUnderHeading,
  computeSha256Hash,
  extractHeadingInsertPayload,
  frontmatterContainsPatch,
  mergeFrontmatterValue,
  normalizePatchOp,
  normalizePatchOpName,
  sectionContainsInsertedContent
} from "./helpers.ts";
import { normalizeWritebackTargetPath } from "./pathSemantics.ts";
import * as writebackHelpers from "./helpers.ts";
import type { App } from "obsidian";

const helperFns = writebackHelpers as unknown as Record<string, (...args: any[]) => any>;

function createFakeApp(
  basePath: string,
  files: Record<string, string>
): App {
  const fileStore = new Map(Object.entries(files));

  const makeFile = (vaultPath: string) => ({
    path: vaultPath,
    basename: path.posix.basename(vaultPath).replace(/\.(md|markdown)$/i, ""),
    extension: path.posix.extname(vaultPath).replace(/^\./, ""),
    stat: {}
  });

  return {
    vault: {
      adapter: {
        getBasePath: () => basePath
      },
      getAbstractFileByPath: (vaultPath: string) => {
        if (!fileStore.has(vaultPath)) {
          return null;
        }
        return makeFile(vaultPath);
      },
      cachedRead: async (file: { path: string }) => fileStore.get(file.path) ?? "",
      modify: async (file: { path: string }, data: string) => {
        fileStore.set(file.path, data);
      }
    },
    fileManager: {
      processFrontMatter: async () => {}
    },
    metadataCache: {
      getFileCache: () => null
    }
  } as unknown as App;
}

test("normalizePatchOpName accepts canonical and legacy frontmatter op names", () => {
  assert.equal(normalizePatchOpName("merge_frontmatter"), "merge_frontmatter");
  assert.equal(normalizePatchOpName("frontmatter_merge"), "merge_frontmatter");
  assert.equal(normalizePatchOpName("insert_under_heading"), "insert_under_heading");
  assert.equal(normalizePatchOpName("replace_section"), "replace_section");
  assert.equal(normalizePatchOpName("add_wikilink"), "add_wikilink");
  assert.equal(normalizePatchOpName("delete_block"), null);
});

test("applyInsertUnderHeading appends content inside the matched section", () => {
  const markdown = [
    "# Daily",
    "intro",
    "",
    "## Digest",
    "- existing line",
    "",
    "## Next",
    "todo"
  ].join("\n");

  const result = applyInsertUnderHeading(markdown, {
    heading: "## Digest",
    content: "- inserted line"
  });

  assert.match(
    result,
    /## Digest\n- existing line\n\n- inserted line\n\n## Next/
  );
  assert.equal(
    sectionContainsInsertedContent(result, {
      heading: "## Digest",
      content: "- inserted line"
    }),
    true
  );
});

test("applyInsertUnderHeading rejects unknown headings", () => {
  assert.throws(
    () => applyInsertUnderHeading("# Root\n", {
      heading: "## Missing",
      content: "- x"
    }),
    /Heading not found/
  );
});

test("mergeFrontmatterValue preserves unknown fields and merges arrays", () => {
  const currentFrontmatter = {
    tags: ["langgraph"],
    aliases: ["Digest"],
    nested: {
      reviewer: "human"
    }
  };

  const merged = mergeFrontmatterValue(currentFrontmatter, {
    tags: ["digest", "langgraph"],
    nested: {
      approved: true
    }
  }) as Record<string, unknown>;

  assert.deepEqual(merged.tags, ["langgraph", "digest"]);
  assert.deepEqual(merged.aliases, ["Digest"]);
  assert.deepEqual(merged.nested, {
    reviewer: "human",
    approved: true
  });
  assert.equal(
    frontmatterContainsPatch(merged, {
      tags: ["digest"],
      nested: {
        approved: true
      }
    }),
    true
  );
});

test("extractHeadingInsertPayload and computeSha256Hash keep protocol-compatible shapes", () => {
  assert.deepEqual(
    extractHeadingInsertPayload({
      op: "insert_under_heading",
      target_path: "Daily.md",
      payload: {
        heading_path: "## Digest",
        content: "- hello"
      }
    }),
    {
      heading: "## Digest",
      content: "- hello"
    }
  );
  assert.match(computeSha256Hash("hello"), /^sha256:[a-f0-9]{64}$/);
});

test("extractReplaceSectionPayload and applyReplaceSection rewrite only the matched heading body", () => {
  const markdown = [
    "# Root",
    "",
    "## Review",
    "- old line",
    "",
    "## Next",
    "- keep me"
  ].join("\n");

  assert.deepEqual(
    helperFns.extractReplaceSectionPayload({
      op: "replace_section",
      target_path: "Root.md",
      payload: {
        heading: "## Review",
        content: "- new line"
      }
    }),
    {
      heading: "## Review",
      content: "- new line"
    }
  );

  assert.match(
    helperFns.applyReplaceSection(markdown, {
      heading: "## Review",
      content: "- new line"
    }),
    /## Review\n- new line\n\n## Next\n- keep me/
  );
});

test("extractAddWikilinkPayload and applyAddWikilink append a normalized wikilink and reject duplicates", () => {
  const markdown = ["# Root", "", "## Links", "- [[Alpha]]"].join("\n");

  assert.deepEqual(
    helperFns.extractAddWikilinkPayload({
      op: "add_wikilink",
      target_path: "Root.md",
      payload: {
        heading: "## Links",
        linked_note_path: "Alpha.md"
      }
    }),
    {
      heading: "## Links",
      linked_note_path: "Alpha.md"
    }
  );

  assert.match(
    helperFns.applyAddWikilink(["# Root", "", "## Links"].join("\n"), {
      heading: "## Links",
      linked_note_path: "Alpha.md"
    }),
    /## Links\n\[\[Alpha\]\]/
  );

  assert.throws(
    () => helperFns.applyAddWikilink(markdown, {
      heading: "## Links",
      linked_note_path: "Alpha.md"
    }),
    /already exists/
  );
});

test("preparePatchOpsForExecution resolves add_wikilink targets before preflight and execution", () => {
  const normalizedPatchOps = [
    normalizePatchOp({
      op: "merge_frontmatter",
      target_path: "Root.md",
      payload: {
        tags: ["review"]
      }
    }),
    normalizePatchOp({
      op: "add_wikilink",
      target_path: "Root.md",
      payload: {
        heading: "## Links",
        linked_note_path: "Alpha.md"
      }
    })
  ];

  const prepared = helperFns.preparePatchOpsForExecution(
    normalizedPatchOps,
    (linkedNotePath: string) => {
      assert.equal(linkedNotePath, "Alpha.md");
      return "Notes/Alpha.md";
    }
  );

  assert.equal(prepared[0].normalizedOp, "merge_frontmatter");
  assert.equal(
    prepared[1].payload.linked_note_path,
    "Notes/Alpha.md"
  );

  assert.throws(
    () => helperFns.preparePatchOpsForExecution(
      [normalizedPatchOps[1]],
      () => {
        throw new Error("Linked note was not found");
      }
    ),
    /Linked note was not found/
  );
});

test("normalizeWritebackTargetPath keeps canonical vault-relative paths unchanged", () => {
  assert.equal(
    normalizeWritebackTargetPath(
      {
        vault: {
          adapter: {
            getBasePath: () => "/tmp/workspace/vault"
          }
        }
      },
      "Daily/2026-03-14.md"
    ),
    "Daily/2026-03-14.md"
  );
});

test("normalizeWritebackTargetPath converts absolute in-vault paths to canonical vault-relative paths", () => {
  const vaultRoot = "/tmp/workspace/vault";
  assert.equal(
    normalizeWritebackTargetPath(
      {
        vault: {
          adapter: {
            getBasePath: () => vaultRoot
          }
        }
      },
      path.join(vaultRoot, "Daily", "2026-03-14.md")
    ),
    "Daily/2026-03-14.md"
  );
});

test("normalizeWritebackTargetPath rejects legacy /vault pseudo-paths outside a real /vault root", () => {
  assert.throws(
    () => normalizeWritebackTargetPath(
      {
        vault: {
          adapter: {
            getBasePath: () => "/tmp/workspace/vault"
          }
        }
      },
      "/vault/Daily/2026-03-14.md"
    ),
    /Legacy \/vault\/ paths are not accepted in normal mode|Absolute path must resolve inside the configured vault/
  );
});

test("applyProposalWriteback and rollbackProposalWriteback preserve canonical target paths on execution", async () => {
  const vaultRoot = "/vault";
  const targetPath = path.join(vaultRoot, "Daily", "2026-03-14.md");
  const initialMarkdown = [
    "# Daily",
    "",
    "## Notes"
  ].join("\n");
  const app = createFakeApp(vaultRoot, {
    "Daily/2026-03-14.md": initialMarkdown
  });

  const applyResult = await applyProposalWriteback(app, {
    proposal_id: "proposal-absolute-target",
    action_type: "daily_digest",
    target_note_path: targetPath,
    summary: "Normalize path",
    risk_level: "low",
    evidence: [],
    patch_ops: [
      {
        op: "insert_under_heading",
        target_path: targetPath,
        payload: {
          heading: "## Notes",
          content: "- inserted"
        }
      }
    ],
    safety_checks: {
      before_hash: computeSha256Hash(initialMarkdown),
      max_changed_lines: 10,
      contains_delete: false
    }
  });

  assert.equal(applyResult.writeback_result.applied, true);
  assert.equal(applyResult.writeback_result.target_note_path, "Daily/2026-03-14.md");
  assert.ok(applyResult.rollback_context);

  const rollbackResult = await rollbackProposalWriteback(
    app,
    {
      proposal_id: "proposal-absolute-target",
      action_type: "daily_digest",
      target_note_path: targetPath,
      summary: "Normalize path",
      risk_level: "low",
      evidence: [],
      patch_ops: [],
      safety_checks: {
        before_hash: computeSha256Hash(initialMarkdown),
        max_changed_lines: 10,
        contains_delete: false
      }
    },
    applyResult.rollback_context
  );

  assert.equal(rollbackResult.applied, true);
  assert.equal(rollbackResult.target_note_path, "Daily/2026-03-14.md");
});

test("applyProposalWriteback rejects a /vault pseudo-path on the execution path without leaking it", async () => {
  const app = createFakeApp("/tmp/workspace/vault", {
    "Daily/2026-03-14.md": [
      "# Daily",
      "",
      "## Notes"
    ].join("\n")
  });

  const result = await applyProposalWriteback(app, {
    proposal_id: "proposal-legacy-target",
    action_type: "daily_digest",
    target_note_path: "/vault/Daily/2026-03-14.md",
    summary: "Reject legacy path",
    risk_level: "low",
    evidence: [],
    patch_ops: [
      {
        op: "insert_under_heading",
        target_path: "/vault/Daily/2026-03-14.md",
        payload: {
          heading: "## Notes",
          content: "- inserted"
        }
      }
    ],
    safety_checks: {
      before_hash: computeSha256Hash([
        "# Daily",
        "",
        "## Notes"
      ].join("\n")),
      max_changed_lines: 10,
      contains_delete: false
    }
  });

  assert.equal(result.writeback_result.applied, false);
  assert.equal(result.writeback_result.target_note_path, null);
  assert.match(result.writeback_result.error ?? "", /inside the configured vault|Legacy \/vault\//);
});
