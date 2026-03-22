import assert from "node:assert/strict";
import test from "node:test";

import {
  applyInsertUnderHeading,
  computeSha256Hash,
  extractHeadingInsertPayload,
  frontmatterContainsPatch,
  mergeFrontmatterValue,
  normalizePatchOpName,
  sectionContainsInsertedContent
} from "./helpers.ts";

test("normalizePatchOpName accepts canonical and legacy frontmatter op names", () => {
  assert.equal(normalizePatchOpName("merge_frontmatter"), "merge_frontmatter");
  assert.equal(normalizePatchOpName("frontmatter_merge"), "merge_frontmatter");
  assert.equal(normalizePatchOpName("insert_under_heading"), "insert_under_heading");
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
