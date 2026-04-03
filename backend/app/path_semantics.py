from __future__ import annotations

from pathlib import Path, PureWindowsPath


class PathContractError(ValueError):
    pass


_LEGACY_VAULT_PREFIX = "/vault/"


def normalize_path_separators(raw_path: str | Path) -> str:
    return str(raw_path).replace("\\", "/")


def is_vault_relative(raw_path: str) -> bool:
    try:
        _validate_relative_contract_path(raw_path)
    except PathContractError:
        return False
    return True


def normalize_to_vault_relative(
    raw_path: str | Path,
    *,
    vault_root: Path,
    legacy_mode: bool = False,
) -> str:
    normalized_raw_path = normalize_path_separators(raw_path)
    if not normalized_raw_path.strip():
        raise PathContractError("Path value must be non-empty.")

    if normalized_raw_path.startswith(_LEGACY_VAULT_PREFIX):
        if not legacy_mode:
            raise PathContractError("Legacy /vault/ paths are not accepted in normal mode.")
        legacy_relative_path = normalized_raw_path.removeprefix(_LEGACY_VAULT_PREFIX)
        if not legacy_relative_path:
            raise PathContractError("Legacy /vault/ path must include a relative target.")
        return _validate_relative_contract_path(legacy_relative_path)

    if _is_windows_absolute_path(normalized_raw_path):
        return _normalize_windows_absolute_path(
            normalized_raw_path,
            vault_root=vault_root,
        )

    if normalized_raw_path.startswith("/"):
        _reject_escape_segments(normalized_raw_path)
        resolved_vault_root = vault_root.expanduser().resolve()
        resolved_candidate = Path(normalized_raw_path).expanduser().resolve()
        try:
            relative_candidate = resolved_candidate.relative_to(resolved_vault_root)
        except ValueError as exc:
            raise PathContractError(
                "Absolute path must resolve inside the configured vault."
            ) from exc
        return _validate_relative_contract_path(relative_candidate.as_posix())

    return _validate_relative_contract_path(normalized_raw_path)


def resolve_vault_relative(raw_path: str, *, vault_root: Path) -> Path:
    normalized_relative_path = normalize_to_vault_relative(
        raw_path,
        vault_root=vault_root,
    )
    resolved_vault_root = vault_root.expanduser().resolve()
    resolved_candidate = (resolved_vault_root / normalized_relative_path).resolve()
    try:
        resolved_candidate.relative_to(resolved_vault_root)
    except ValueError as exc:
        raise PathContractError(
            "Resolved path must stay within the configured vault."
        ) from exc
    return resolved_candidate


def _normalize_windows_absolute_path(
    raw_path: str,
    *,
    vault_root: Path,
) -> str:
    _reject_escape_segments(raw_path)
    windows_vault_root = PureWindowsPath(normalize_path_separators(vault_root))
    if not windows_vault_root.is_absolute():
        raise PathContractError("Absolute path must resolve inside the configured vault.")

    windows_candidate = PureWindowsPath(raw_path)
    try:
        relative_candidate = windows_candidate.relative_to(windows_vault_root)
    except ValueError as exc:
        raise PathContractError(
            "Absolute path must resolve inside the configured vault."
        ) from exc
    return _validate_relative_contract_path("/".join(relative_candidate.parts))


def _validate_relative_contract_path(raw_path: str) -> str:
    normalized_path = normalize_path_separators(raw_path)
    if not normalized_path.strip():
        raise PathContractError("Path value must be non-empty.")
    if normalized_path.startswith("/"):
        raise PathContractError("Path must be vault-relative and not absolute.")
    _reject_escape_segments(normalized_path)
    if any(part == "" for part in normalized_path.split("/")):
        raise PathContractError("Path must not contain empty path segments.")
    if _is_windows_absolute_path(normalized_path):
        raise PathContractError("Path must be vault-relative and not absolute.")

    return normalized_path


def _reject_escape_segments(raw_path: str) -> None:
    parts = [part for part in normalize_path_separators(raw_path).split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise PathContractError("Path must not contain '.' or '..' segments.")


def _is_windows_absolute_path(raw_path: str) -> bool:
    return PureWindowsPath(raw_path).is_absolute()
