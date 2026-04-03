from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.path_semantics import (
    PathContractError,
    is_vault_relative,
    normalize_path_separators,
    normalize_to_vault_relative,
    resolve_vault_relative,
)


class VaultPathSemanticsTests(unittest.TestCase):
    def test_normalize_path_separators_replaces_backslashes(self) -> None:
        self.assertEqual(
            normalize_path_separators("Daily\\2026-03-14.md"),
            "Daily/2026-03-14.md",
        )

    def test_relative_path_stays_unchanged_and_is_vault_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()

            normalized = normalize_to_vault_relative(
                "Daily/2026-03-14.md",
                vault_root=vault_root,
            )

            self.assertEqual(normalized, "Daily/2026-03-14.md")
            self.assertTrue(is_vault_relative(normalized))
            self.assertEqual(
                resolve_vault_relative(normalized, vault_root=vault_root),
                (vault_root.resolve() / "Daily" / "2026-03-14.md").resolve(),
            )

    def test_absolute_in_vault_path_normalizes_to_vault_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()
            note_path = vault_root / "Daily" / "2026-03-14.md"
            note_path.parent.mkdir()
            note_path.write_text("# Daily\n", encoding="utf-8")

            normalized = normalize_to_vault_relative(
                str(note_path.resolve()),
                vault_root=vault_root,
            )

            self.assertEqual(normalized, "Daily/2026-03-14.md")
            self.assertTrue(is_vault_relative(normalized))
            self.assertEqual(
                resolve_vault_relative(normalized, vault_root=vault_root),
                note_path.resolve(),
            )

    def test_absolute_in_vault_path_with_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()

            with self.assertRaises(PathContractError):
                normalize_to_vault_relative(
                    str(vault_root / "Daily" / ".." / "note.md"),
                    vault_root=vault_root,
                )

    def test_absolute_path_outside_vault_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            outside_note = temp_root / "outside" / "note.md"
            outside_note.parent.mkdir()
            outside_note.write_text("# Outside\n", encoding="utf-8")

            with self.assertRaises(PathContractError):
                normalize_to_vault_relative(
                    str(outside_note.resolve()),
                    vault_root=vault_root,
                )

    def test_windows_absolute_in_vault_path_normalizes_to_vault_relative(self) -> None:
        vault_root = Path("C:/Vault")

        normalized = normalize_to_vault_relative(
            "C:\\Vault\\Daily\\2026-03-14.md",
            vault_root=vault_root,
        )

        self.assertEqual(normalized, "Daily/2026-03-14.md")

    def test_normal_mode_rejects_legacy_vault_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()

            with self.assertRaises(PathContractError):
                normalize_to_vault_relative(
                    "/vault/Daily/2026-03-14.md",
                    vault_root=vault_root,
                )

    def test_migration_mode_accepts_legacy_vault_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()

            self.assertEqual(
                normalize_to_vault_relative(
                    "/vault/Daily/2026-03-14.md",
                    vault_root=vault_root,
                    legacy_mode=True,
                ),
                "Daily/2026-03-14.md",
            )

    def test_traversal_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_root = Path(temp_dir) / "vault"
            vault_root.mkdir()

            for candidate in ("../outside.md", "Daily/../../outside.md", "/vault/../outside.md"):
                with self.subTest(candidate=candidate):
                    with self.assertRaises(PathContractError):
                        normalize_to_vault_relative(
                            candidate,
                            vault_root=vault_root,
                            legacy_mode=True,
                        )

    def test_resolve_vault_relative_rejects_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_root = temp_root / "vault"
            vault_root.mkdir()
            outside_dir = temp_root / "outside"
            outside_dir.mkdir()
            outside_note = outside_dir / "note.md"
            outside_note.write_text("# Outside\n", encoding="utf-8")
            escape_link = vault_root / "escape"

            try:
                escape_link.symlink_to(outside_dir, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("Symlinks are not available in this environment.")

            with self.assertRaises(PathContractError):
                resolve_vault_relative(
                    "escape/note.md",
                    vault_root=vault_root,
                )


if __name__ == "__main__":
    unittest.main()
