from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import re

from app.config import Settings
from app.contracts.workflow import PatchOp, Proposal


class ProposalValidationError(ValueError):
    """Raised when a stored or generated proposal fails static validation."""


SCRIPT_TAG_RE = re.compile(r"<\s*/?\s*script\b", re.IGNORECASE)
ALLOWED_PATCH_OPS = {
    "frontmatter_merge",
    "insert_under_heading",
    "merge_frontmatter",
    "replace_section",
    "add_wikilink",
}


def validate_proposal_for_persistence(
    proposal: Proposal,
    *,
    settings: Settings,
    content_limit: int = 2000,
) -> None:
    vault_root = _normalize_vault_root(settings.sample_vault_dir)
    _validate_path_within_vault(
        proposal.target_note_path,
        vault_root=vault_root,
        field_name="proposal.target_note_path",
    )

    for ordinal, patch_op in enumerate(proposal.patch_ops):
        _validate_patch_op(
            patch_op,
            vault_root=vault_root,
            content_limit=content_limit,
            ordinal=ordinal,
        )


def _normalize_vault_root(vault_root: Path) -> Path:
    return vault_root.expanduser().resolve()


def _validate_patch_op(
    patch_op: PatchOp,
    *,
    vault_root: Path,
    content_limit: int,
    ordinal: int,
) -> None:
    if not isinstance(patch_op.op, str) or not patch_op.op.strip():
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].op must be a non-empty string."
        )
    if patch_op.op not in ALLOWED_PATCH_OPS:
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].op={patch_op.op!r} is not supported."
        )

    _validate_path_within_vault(
        patch_op.target_path,
        vault_root=vault_root,
        field_name=f"patch_ops[{ordinal}].target_path",
    )

    if not isinstance(patch_op.payload, dict):
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].payload must be a mapping."
        )

    if patch_op.op in {"insert_under_heading", "replace_section"}:
        _validate_heading_content_payload(
            patch_op.payload,
            content_limit=content_limit,
            ordinal=ordinal,
            op_name=patch_op.op,
        )
    elif patch_op.op == "add_wikilink":
        _validate_add_wikilink_payload(
            patch_op.payload,
            vault_root=vault_root,
            ordinal=ordinal,
        )

    _validate_payload_strings(
        patch_op.payload,
        content_limit=content_limit,
        field_name=f"patch_ops[{ordinal}].{patch_op.op} payload",
    )


def _validate_heading_content_payload(
    payload: dict[str, object],
    *,
    content_limit: int,
    ordinal: int,
    op_name: str,
) -> None:
    heading = _first_string_value(payload, ("heading", "heading_path"))
    if heading is None or not heading.strip():
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].{op_name} payload must include heading or heading_path."
        )

    content = _first_string_value(payload, ("content", "text"))
    if content is None or not content.strip():
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].{op_name} payload must include content or text."
        )
    if len(content) > content_limit:
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].{op_name} payload text exceeds the {content_limit} character limit."
        )


def _validate_add_wikilink_payload(
    payload: dict[str, object],
    *,
    vault_root: Path,
    ordinal: int,
) -> None:
    heading = _first_string_value(payload, ("heading", "heading_path"))
    if heading is None or not heading.strip():
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].add_wikilink payload must include heading or heading_path."
        )

    linked_note_path = _first_string_value(payload, ("linked_note_path",))
    if linked_note_path is None or not linked_note_path.strip():
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].add_wikilink payload must include linked_note_path."
        )

    normalized_linked_note_path = _normalize_candidate_path(
        linked_note_path,
        vault_root=vault_root,
        field_name=f"patch_ops[{ordinal}].payload.linked_note_path",
    )
    if not normalized_linked_note_path.is_file():
        raise ProposalValidationError(
            f"patch_ops[{ordinal}].add_wikilink linked_note_path must reference an existing note within the configured vault."
        )


def _validate_payload_strings(
    payload: dict[str, object],
    *,
    content_limit: int,
    field_name: str,
) -> None:
    for text in _iter_strings(payload):
        if len(text) > content_limit:
            raise ProposalValidationError(
                f"{field_name} contains text longer than {content_limit} characters."
            )
        if SCRIPT_TAG_RE.search(text):
            raise ProposalValidationError(
                f"{field_name} contains a disallowed script tag pattern."
            )


def _validate_path_within_vault(
    raw_path: str,
    *,
    vault_root: Path,
    field_name: str,
) -> None:
    _normalize_candidate_path(
        raw_path,
        vault_root=vault_root,
        field_name=field_name,
    )


def _normalize_candidate_path(
    raw_path: str,
    *,
    vault_root: Path,
    field_name: str,
) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ProposalValidationError(f"{field_name} must be a non-empty string.")

    candidate_path = Path(raw_path).expanduser()
    if not candidate_path.is_absolute():
        candidate_path = vault_root / candidate_path
    normalized_candidate_path = candidate_path.resolve()

    try:
        normalized_candidate_path.relative_to(vault_root)
    except ValueError as exc:
        raise ProposalValidationError(
            f"{field_name} must stay within the configured vault."
        ) from exc
    return normalized_candidate_path


def _iter_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for nested_value in value.values():
            yield from _iter_strings(nested_value)
        return
    if isinstance(value, (list, tuple, set)):
        for nested_value in value:
            yield from _iter_strings(nested_value)


def _first_string_value(
    payload: dict[str, object],
    keys: tuple[str, ...],
) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None
