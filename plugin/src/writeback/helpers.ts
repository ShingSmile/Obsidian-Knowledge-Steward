import { createHash } from "crypto";
import path from "path";

import type { PatchOp } from "../contracts";

export type SupportedPatchOpName =
  | "merge_frontmatter"
  | "insert_under_heading"
  | "replace_section"
  | "add_wikilink";

export interface NormalizedPatchOp extends PatchOp {
  normalizedOp: SupportedPatchOpName;
}

export interface HeadingInsertPayload {
  heading: string;
  content: string;
}

export interface ReplaceSectionPayload {
  heading: string;
  content: string;
}

export interface AddWikilinkPayload {
  heading: string;
  linked_note_path: string;
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
  if (op === "replace_section") {
    return "replace_section";
  }
  if (op === "add_wikilink") {
    return "add_wikilink";
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

export function extractReplaceSectionPayload(patchOp: PatchOp): ReplaceSectionPayload {
  const heading = firstNonEmptyString(
    patchOp.payload.heading,
    patchOp.payload.heading_path
  );
  const content = typeof patchOp.payload.content === "string"
    ? patchOp.payload.content
    : null;

  if (!heading) {
    throw new Error("replace_section payload must include heading or heading_path.");
  }
  if (content === null || content.trim().length === 0) {
    throw new Error("replace_section payload must include non-empty content.");
  }
  return {
    heading,
    content
  };
}

export function applyReplaceSection(
  markdown: string,
  payload: ReplaceSectionPayload
): string {
  const newline = markdown.includes("\r\n") ? "\r\n" : "\n";
  const lines = markdown.split(/\r?\n/);
  const bounds = findUniqueHeadingSectionBounds(lines, payload.heading, "replace_section");
  if (!bounds) {
    throw new Error(`Heading not found for replace_section: ${payload.heading}`);
  }

  const replacementLines = normalizeTextBlock(payload.content).split("\n");
  if (
    bounds.sectionEnd < lines.length
    && replacementLines[replacementLines.length - 1]?.trim().length !== 0
    && lines[bounds.sectionEnd]?.trim().length !== 0
  ) {
    replacementLines.push("");
  }

  const resultLines = [
    ...lines.slice(0, bounds.headingIndex + 1),
    ...replacementLines,
    ...lines.slice(bounds.sectionEnd)
  ];
  return resultLines.join(newline);
}

export function extractAddWikilinkPayload(patchOp: PatchOp): AddWikilinkPayload {
  const heading = firstNonEmptyString(
    patchOp.payload.heading,
    patchOp.payload.heading_path
  );
  const linkedNotePath = firstNonEmptyString(
    patchOp.payload.linked_note_path
  );

  if (!heading) {
    throw new Error("add_wikilink payload must include heading or heading_path.");
  }
  if (!linkedNotePath) {
    throw new Error("add_wikilink payload must include linked_note_path.");
  }
  return {
    heading,
    linked_note_path: linkedNotePath
  };
}

export function applyAddWikilink(
  markdown: string,
  payload: AddWikilinkPayload
): string {
  const lines = markdown.split(/\r?\n/);
  const bounds = findUniqueHeadingSectionBounds(lines, payload.heading, "add_wikilink");
  if (!bounds) {
    throw new Error(`Heading not found for add_wikilink: ${payload.heading}`);
  }

  const normalizedTargetPath = normalizeWikilinkTargetPath(payload.linked_note_path);
  const sectionText = normalizeTextBlock(
    lines.slice(bounds.headingIndex + 1, bounds.sectionEnd).join("\n")
  );
  if (sectionContainsWikilinkTarget(sectionText, normalizedTargetPath)) {
    throw new Error(
      `Wikilink already exists in section for add_wikilink: [[${normalizedTargetPath}]]`
    );
  }

  return applyInsertUnderHeading(markdown, {
    heading: payload.heading,
    content: `[[${normalizedTargetPath}]]`
  });
}

export function preparePatchOpsForExecution(
  patchOps: NormalizedPatchOp[],
  resolveLinkedNotePath: (linkedNotePath: string) => string
): NormalizedPatchOp[] {
  return patchOps.map((patchOp) => {
    if (patchOp.normalizedOp !== "add_wikilink") {
      return patchOp;
    }

    const wikilinkPayload = extractAddWikilinkPayload(patchOp);
    return {
      ...patchOp,
      payload: {
        ...patchOp.payload,
        heading: wikilinkPayload.heading,
        linked_note_path: resolveLinkedNotePath(wikilinkPayload.linked_note_path)
      }
    };
  });
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

function findUniqueHeadingSectionBounds(
  lines: string[],
  heading: string,
  opName: string
): { headingIndex: number; sectionEnd: number } | null {
  const normalizedHeading = heading.trim();
  let matchCount = 0;
  for (const line of lines) {
    if (line.trim() === normalizedHeading) {
      matchCount += 1;
      if (matchCount > 1) {
        throw new Error(`Heading matched multiple sections for ${opName}: ${heading}`);
      }
    }
  }
  if (matchCount === 0) {
    return null;
  }
  return findHeadingSectionBounds(lines, heading);
}

function sectionContainsWikilinkTarget(sectionText: string, normalizedTargetPath: string): boolean {
  const wikilinkPattern = /\[\[([^\]]+)\]\]/g;
  for (const match of sectionText.matchAll(wikilinkPattern)) {
    if (normalizeWikilinkTargetPath(match[1]) === normalizedTargetPath) {
      return true;
    }
  }
  return false;
}

export function normalizeWikilinkTargetPath(value: string): string {
  const withoutAlias = value.split("|", 1)[0].split("#", 1)[0].trim();
  if (withoutAlias.length === 0) {
    throw new Error("linked_note_path must be a non-empty note path.");
  }
  return path.posix.normalize(withoutAlias.replace(/\\/g, "/")).replace(/\.(md|markdown)$/i, "");
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
