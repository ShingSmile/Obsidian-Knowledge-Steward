import path from "path";

const LEGACY_VAULT_PREFIX = "/vault/";

export interface VaultPathApp {
  vault: {
    adapter?: unknown;
  };
}

export class PathContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PathContractError";
  }
}

export function normalizeWritebackTargetPath(
  app: VaultPathApp,
  rawPath: string
): string {
  const normalizedRawPath = normalizePathSeparators(rawPath).trim();
  if (normalizedRawPath.length === 0) {
    throw new PathContractError("Path value must be non-empty.");
  }

  if (isWindowsAbsolutePath(normalizedRawPath)) {
    return normalizeWindowsAbsolutePath(app, normalizedRawPath);
  }

  if (normalizedRawPath.startsWith("/")) {
    return normalizePosixAbsolutePath(app, normalizedRawPath);
  }

  return normalizeVaultRelativePath(normalizedRawPath);
}

export function normalizeVaultRelativePath(rawPath: string): string {
  const normalizedRawPath = normalizePathSeparators(rawPath).trim();
  if (normalizedRawPath.length === 0) {
    throw new PathContractError("Path value must be non-empty.");
  }
  if (normalizedRawPath.startsWith("/")) {
    throw new PathContractError("Path must be vault-relative and not absolute.");
  }
  if (isWindowsAbsolutePath(normalizedRawPath)) {
    throw new PathContractError("Path must be vault-relative and not absolute.");
  }
  rejectEscapeSegments(normalizedRawPath);

  const normalizedPath = path.posix.normalize(normalizedRawPath);
  if (
    normalizedPath.length === 0
    || normalizedPath === "."
    || normalizedPath.startsWith("/")
    || normalizedPath === ".."
  ) {
    throw new PathContractError("Path must be vault-relative and not absolute.");
  }
  if (normalizedPath.split("/").some((segment) => segment.length === 0)) {
    throw new PathContractError("Path must not contain empty path segments.");
  }
  return normalizedPath;
}

function normalizePosixAbsolutePath(app: VaultPathApp, rawPath: string): string {
  const adapter = app.vault.adapter as {
    getBasePath?: () => string;
  } | null | undefined;
  if (typeof adapter?.getBasePath !== "function") {
    throw new PathContractError(
      "Absolute target paths require a filesystem-backed Obsidian vault adapter."
    );
  }

  const vaultRoot = normalizeFilesystemPath(path.resolve(adapter.getBasePath()));
  const absolutePath = normalizeFilesystemPath(path.resolve(rawPath));
  if (
    absolutePath !== vaultRoot
    && !absolutePath.startsWith(`${vaultRoot}/`)
  ) {
    if (isLegacyVaultPseudoPath(rawPath)) {
      throw new PathContractError("Legacy /vault/ paths are not accepted in normal mode.");
    }
    throw new PathContractError("Absolute path must resolve inside the configured vault.");
  }

  return normalizeVaultRelativePath(path.relative(vaultRoot, absolutePath));
}

function normalizeWindowsAbsolutePath(app: VaultPathApp, rawPath: string): string {
  const adapter = app.vault.adapter as {
    getBasePath?: () => string;
  } | null | undefined;
  if (typeof adapter?.getBasePath !== "function") {
    throw new PathContractError(
      "Absolute target paths require a filesystem-backed Obsidian vault adapter."
    );
  }

  const vaultRoot = normalizeFilesystemPath(path.win32.resolve(adapter.getBasePath()));
  const absolutePath = normalizeFilesystemPath(path.win32.resolve(rawPath));
  const comparisonVaultRoot = vaultRoot.toLowerCase();
  const comparisonAbsolutePath = absolutePath.toLowerCase();
  if (
    comparisonAbsolutePath !== comparisonVaultRoot
    && !comparisonAbsolutePath.startsWith(`${comparisonVaultRoot}/`)
  ) {
    if (isLegacyVaultPseudoPath(rawPath)) {
      throw new PathContractError("Legacy /vault/ paths are not accepted in normal mode.");
    }
    throw new PathContractError("Absolute path must resolve inside the configured vault.");
  }

  return normalizeVaultRelativePath(path.win32.relative(vaultRoot, absolutePath));
}

function normalizePathSeparators(rawPath: string): string {
  return String(rawPath).replace(/\\/g, "/");
}

function normalizeFilesystemPath(rawPath: string): string {
  return rawPath.replace(/\\/g, "/");
}

function rejectEscapeSegments(rawPath: string): void {
  const parts = rawPath.split("/").filter((part) => part.length > 0);
  if (parts.some((part) => part === "." || part === "..")) {
    throw new PathContractError("Path must not contain '.' or '..' segments.");
  }
  if (rawPath.includes("//")) {
    throw new PathContractError("Path must not contain empty path segments.");
  }
}

function isWindowsAbsolutePath(rawPath: string): boolean {
  return /^[A-Za-z]:\//.test(rawPath) || rawPath.startsWith("//");
}

function isLegacyVaultPseudoPath(rawPath: string): boolean {
  return rawPath === "/vault" || rawPath.startsWith(LEGACY_VAULT_PREFIX);
}
