import { createHash } from "crypto";

import type { PatchOp } from "../contracts";

export type SupportedPatchOpName = "merge_frontmatter" | "insert_under_heading";

export interface NormalizedPatchOp extends PatchOp {
  normalizedOp: SupportedPatchOpName;
}

export interface HeadingInsertPayload {
  heading: string;
  content: string;
}

export function computeSha256Hash(input: string | Uint8Array): string {
  return `sha256:${createHash("sha256").update(input).digest("hex")}`;
}

export function normalizePatchOpName(op: string): SupportedPatchOpName | null {
  if (op === "merge_frontmatter" || op === "frontmatter_merge") {
    return "merge_frontmatter";
  }
  if (op === "insert_under_heading") {
    return "insert_under_heading";
  }
  return null;
}

export function normalizePatchOp(patchOp: PatchOp): NormalizedPatchOp {
  const normalizedOp = normalizePatchOpName(patchOp.op);
  if (!normalizedOp) {
    throw new Error(`Unsupported patch op: ${patchOp.op}`);
  }
  return {
    ...patchOp,
    normalizedOp
  };
}

export function extractHeadingInsertPayload(patchOp: PatchOp): HeadingInsertPayload {
  const heading = firstNonEmptyString(
    patchOp.payload.heading,
    patchOp.payload.heading_path
  );
  const content = typeof patchOp.payload.content === "string"
    ? patchOp.payload.content
    : null;

  if (!heading) {
    throw new Error("insert_under_heading payload must include heading or heading_path.");
  }
  if (content === null || content.trim().length === 0) {
    throw new Error("insert_under_heading payload must include non-empty content.");
  }
  return {
    heading,
    content
  };
}

export function applyInsertUnderHeading(
  markdown: string,
  payload: {
    heading: string;
    content: string;
  }
): string {
  const newline = markdown.includes("\r\n") ? "\r\n" : "\n";
  const lines = markdown.split(/\r?\n/);
  const bounds = findHeadingSectionBounds(lines, payload.heading);
  if (!bounds) {
    throw new Error(`Heading not found for insert_under_heading: ${payload.heading}`);
  }

  const insertionLines = normalizeTextBlock(payload.content).split("\n");
  if (
    bounds.sectionEnd > bounds.headingIndex + 1
    && lines[bounds.sectionEnd - 1]?.trim().length !== 0
  ) {
    insertionLines.unshift("");
  }
  if (
    bounds.sectionEnd < lines.length
    && insertionLines[insertionLines.length - 1]?.trim().length !== 0
    && lines[bounds.sectionEnd]?.trim().length !== 0
  ) {
    insertionLines.push("");
  }

  const resultLines = [
    ...lines.slice(0, bounds.sectionEnd),
    ...insertionLines,
    ...lines.slice(bounds.sectionEnd)
  ];
  return resultLines.join(newline);
}

export function sectionContainsInsertedContent(
  markdown: string,
  payload: {
    heading: string;
    content: string;
  }
): boolean {
  const lines = markdown.split(/\r?\n/);
  const bounds = findHeadingSectionBounds(lines, payload.heading);
  if (!bounds) {
    return false;
  }
  const sectionText = normalizeTextBlock(
    lines.slice(bounds.headingIndex + 1, bounds.sectionEnd).join("\n")
  );
  return sectionText.includes(normalizeTextBlock(payload.content));
}

export function mergeFrontmatterValue(existing: unknown, incoming: unknown): unknown {
  if (Array.isArray(incoming)) {
    const mergedArray = Array.isArray(existing)
      ? [...existing]
      : existing === undefined || existing === null
        ? []
        : [existing];
    const seen = new Set(mergedArray.map((item) => stableSerialize(item)));
    for (const item of incoming) {
      const itemKey = stableSerialize(item);
      if (!seen.has(itemKey)) {
        mergedArray.push(item);
        seen.add(itemKey);
      }
    }
    return mergedArray;
  }

  if (isPlainObject(incoming)) {
    const mergedObject: Record<string, unknown> = isPlainObject(existing)
      ? { ...existing }
      : {};
    for (const [key, value] of Object.entries(incoming)) {
      mergedObject[key] = mergeFrontmatterValue(mergedObject[key], value);
    }
    return mergedObject;
  }

  return incoming;
}

export function frontmatterContainsPatch(
  frontmatter: Record<string, unknown>,
  patchPayload: Record<string, unknown>
): boolean {
  for (const [key, value] of Object.entries(patchPayload)) {
    if (!valueContainsPatch(frontmatter[key], value)) {
      return false;
    }
  }
  return true;
}

export function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return isPlainObject(value);
}

function valueContainsPatch(current: unknown, patchValue: unknown): boolean {
  if (Array.isArray(patchValue)) {
    if (!Array.isArray(current)) {
      return false;
    }
    return patchValue.every((expectedItem) =>
      current.some((currentItem) => stableSerialize(currentItem) === stableSerialize(expectedItem))
    );
  }

  if (isPlainObject(patchValue)) {
    if (!isPlainObject(current)) {
      return false;
    }
    return Object.entries(patchValue).every(([key, value]) =>
      valueContainsPatch(current[key], value)
    );
  }

  return stableSerialize(current) === stableSerialize(patchValue);
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

function normalizeTextBlock(value: string): string {
  return value.replace(/\r\n/g, "\n").trimEnd();
}

function firstNonEmptyString(...values: unknown[]): string | null {
  for (const value of values) {
    if (typeof value === "string" && value.trim().length > 0) {
      return value;
    }
  }
  return null;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stableSerialize(value: unknown): string {
  if (value === undefined) {
    return "undefined";
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(",")}]`;
  }
  if (isPlainObject(value)) {
    const entries = Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`);
    return `{${entries.join(",")}}`;
  }
  return JSON.stringify(value);
}
