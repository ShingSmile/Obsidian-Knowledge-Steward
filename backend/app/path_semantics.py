from __future__ import annotations

from pathlib import Path


class PathContractError(ValueError):
    pass


_LEGACY_VAULT_PREFIX = "/vault/"


def normalize_path_separators(raw_path: str | Path) -> str:
    return str(raw_path).replace("\\", "/")


def is_vault_relative(raw_path: str) -> bool:
    try:
        normalized_path = _validate_relative_contract_path(raw_path)
    except PathContractError:
        return False
    return not normalized_path.startswith("/")


def normalize_to_vault_relative(
    raw_path: str | Path,
    *,
    vault_root: Path,
    legacy_mode: bool = False,
) -> str:
    normalized_raw_path = normalize_path_separators(raw_path)
    if not normalized_raw_path.strip():
        raise PathContractError("Path value must be non-empty.")

    resolved_vault_root = vault_root.expanduser().resolve()

    if normalized_raw_path.startswith(_LEGACY_VAULT_PREFIX):
        if not legacy_mode:
            raise PathContractError("Legacy /vault/ paths are not accepted in normal mode.")
        legacy_relative_path = normalized_raw_path.removeprefix(_LEGACY_VAULT_PREFIX)
        if not legacy_relative_path:
            raise PathContractError("Legacy /vault/ path must include a relative target.")
        return _validate_relative_contract_path(legacy_relative_path)

    if normalized_raw_path.startswith("/"):
        _reject_escape_segments(normalized_raw_path)
        resolved_candidate = Path(normalized_raw_path).expanduser().resolve()
        try:
            relative_candidate = resolved_candidate.relative_to(resolved_vault_root)
        except ValueError as exc:
            raise PathContractError("Absolute path must resolve inside the configured vault.") from exc
        return _validate_relative_contract_path(relative_candidate.as_posix())

    return _validate_relative_contract_path(normalized_raw_path)


def resolve_vault_relative(raw_path: str, *, vault_root: Path) -> Path:
    normalized_relative_path = normalize_to_vault_relative(raw_path, vault_root=vault_root)
    return vault_root.expanduser().resolve() / normalized_relative_path


def _validate_relative_contract_path(raw_path: str) -> str:
    normalized_path = normalize_path_separators(raw_path)
    if not normalized_path.strip():
        raise PathContractError("Path value must be non-empty.")
    if normalized_path.startswith("/"):
        raise PathContractError("Path must be vault-relative and not absolute.")
    _reject_escape_segments(normalized_path)
    if any(part == "" for part in normalized_path.split("/")):
        raise PathContractError("Path must not contain empty path segments.")
    if len(normalized_path) >= 2 and normalized_path[1] == ":" and normalized_path[0].isalpha():
        raise PathContractError("Path must be vault-relative and not a drive path.")

    return normalized_path


def _reject_escape_segments(raw_path: str) -> None:
    parts = [part for part in raw_path.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise PathContractError("Path must not contain '.' or '..' segments.")
