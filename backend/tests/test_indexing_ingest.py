from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.config import get_settings
from app.indexing.ingest import ingest_vault
from app.retrieval.embeddings import EmbeddingBatchResult


class IndexIngestTests(unittest.TestCase):
    def test_ingest_vault_writes_note_and_chunk_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Alpha.md").write_text(
                "# Alpha\n\nlink [[Roadmap]]\n",
                encoding="utf-8",
            )
            daily_dir = vault_path / "Daily"
            daily_dir.mkdir()
            (daily_dir / "2026-03-14 Daily.md").write_text(
                "# Task Planner\n\n- [ ] ship ingest\n\n# Summary\n\nDone.\n",
                encoding="utf-8",
            )

            stats = ingest_vault(vault_path=vault_path, db_path=db_path)

            connection = sqlite3.connect(db_path)
            try:
                note_count = connection.execute("SELECT COUNT(*) FROM note;").fetchone()[0]
                chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
                fts_count = connection.execute("SELECT COUNT(*) FROM chunk_fts;").fetchone()[0]
                note_types = {
                    row[0]
                    for row in connection.execute("SELECT note_type FROM note;").fetchall()
                }
            finally:
                connection.close()

            self.assertEqual(stats.scanned_notes, 2)
            self.assertEqual(stats.created_notes, 2)
            self.assertEqual(stats.updated_notes, 0)
            self.assertEqual(note_count, 2)
            self.assertGreater(chunk_count, 0)
            self.assertEqual(fts_count, chunk_count)
            self.assertIn("daily_note", note_types)
            self.assertIn("generic_note", note_types)

    def test_ingest_vault_is_idempotent_and_replaces_old_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            note_path = vault_path / "Alpha.md"

            note_path.write_text(
                "# Alpha\n\nbody\n\n## Detail\n\nmore detail\n",
                encoding="utf-8",
            )

            first_stats = ingest_vault(vault_path=vault_path, db_path=db_path)
            second_stats = ingest_vault(vault_path=vault_path, db_path=db_path)

            connection = sqlite3.connect(db_path)
            try:
                note_count = connection.execute("SELECT COUNT(*) FROM note;").fetchone()[0]
                chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
                fts_count = connection.execute("SELECT COUNT(*) FROM chunk_fts;").fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(first_stats.created_notes, 1)
            self.assertEqual(first_stats.current_chunk_count, 2)
            self.assertEqual(second_stats.created_notes, 0)
            self.assertEqual(second_stats.updated_notes, 1)
            self.assertEqual(second_stats.replaced_chunk_count, 2)
            self.assertEqual(note_count, 1)
            self.assertEqual(chunk_count, 2)
            self.assertEqual(fts_count, chunk_count)

            note_path.write_text(
                "# Alpha\n\nbody only\n",
                encoding="utf-8",
            )
            third_stats = ingest_vault(vault_path=vault_path, db_path=db_path)

            connection = sqlite3.connect(db_path)
            try:
                final_note_count = connection.execute("SELECT COUNT(*) FROM note;").fetchone()[0]
                final_chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
                final_fts_count = connection.execute("SELECT COUNT(*) FROM chunk_fts;").fetchone()[0]
                stored_chunk_texts = {
                    row[0] for row in connection.execute("SELECT text FROM chunk;").fetchall()
                }
            finally:
                connection.close()

            self.assertEqual(third_stats.created_notes, 0)
            self.assertEqual(third_stats.updated_notes, 1)
            self.assertEqual(third_stats.replaced_chunk_count, 2)
            self.assertEqual(third_stats.current_chunk_count, 1)
            self.assertEqual(final_note_count, 1)
            self.assertEqual(final_chunk_count, 1)
            self.assertEqual(final_fts_count, final_chunk_count)
            self.assertEqual(stored_chunk_texts, {"# Alpha\n\nbody only"})

    def test_ingest_vault_supports_scoped_single_note_and_refreshes_fts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            alpha_path = vault_path / "Alpha.md"
            beta_path = vault_path / "Beta.md"

            alpha_path.write_text(
                "# Alpha\n\nlegacyalpha token\n",
                encoding="utf-8",
            )
            beta_path.write_text(
                "# Beta\n\nbetapersist token\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)

            alpha_path.write_text(
                "# Alpha\n\nrefreshedalpha token\n",
                encoding="utf-8",
            )
            scoped_stats = ingest_vault(
                vault_path=vault_path,
                db_path=db_path,
                note_path="Alpha.md",
            )

            connection = sqlite3.connect(db_path)
            try:
                note_count = connection.execute("SELECT COUNT(*) FROM note;").fetchone()[0]
                alpha_texts = {
                    row[0]
                    for row in connection.execute(
                        """
                        SELECT chunk.text
                        FROM chunk
                        JOIN note ON note.note_id = chunk.note_id
                        WHERE note.path = ?;
                        """,
                        ("Alpha.md",),
                    ).fetchall()
                }
                beta_texts = {
                    row[0]
                    for row in connection.execute(
                        """
                        SELECT chunk.text
                        FROM chunk
                        JOIN note ON note.note_id = chunk.note_id
                        WHERE note.path = ?;
                        """,
                        ("Beta.md",),
                    ).fetchall()
                }
                refreshed_hits = connection.execute(
                    "SELECT COUNT(*) FROM chunk_fts WHERE chunk_fts MATCH 'refreshedalpha';"
                ).fetchone()[0]
                legacy_hits = connection.execute(
                    "SELECT COUNT(*) FROM chunk_fts WHERE chunk_fts MATCH 'legacyalpha';"
                ).fetchone()[0]
            finally:
                connection.close()

            self.assertEqual(scoped_stats.scanned_notes, 1)
            self.assertEqual(scoped_stats.created_notes, 0)
            self.assertEqual(scoped_stats.updated_notes, 1)
            self.assertEqual(note_count, 2)
            self.assertEqual(alpha_texts, {"# Alpha\n\nrefreshedalpha token"})
            self.assertEqual(beta_texts, {"# Beta\n\nbetapersist token"})
            self.assertGreater(refreshed_hits, 0)
            self.assertEqual(legacy_hits, 0)

    def test_ingest_vault_canonicalizes_absolute_scoped_note_path_before_persisting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            alpha_path = vault_path / "Alpha.md"

            alpha_path.write_text("# Alpha\n\nalpha body\n", encoding="utf-8")

            scoped_stats = ingest_vault(
                vault_path=vault_path,
                db_path=db_path,
                note_path=str(alpha_path.resolve()),
            )

            connection = sqlite3.connect(db_path)
            try:
                stored_paths = {
                    row[0] for row in connection.execute("SELECT path FROM note;").fetchall()
                }
            finally:
                connection.close()

            self.assertEqual(scoped_stats.scanned_notes, 1)
            self.assertEqual(stored_paths, {"Alpha.md"})

    def test_ingest_vault_supports_scoped_note_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            nested_dir = vault_path / "nested"
            nested_dir.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            alpha_path = vault_path / "Alpha.md"
            beta_path = nested_dir / "Beta.md"
            gamma_path = vault_path / "Gamma.md"

            alpha_path.write_text("# Alpha\n\nalpha body\n", encoding="utf-8")
            beta_path.write_text("# Beta\n\nbeta body\n", encoding="utf-8")
            gamma_path.write_text("# Gamma\n\ngamma body\n", encoding="utf-8")

            scoped_stats = ingest_vault(
                vault_path=vault_path,
                db_path=db_path,
                note_paths=["Alpha.md", "nested/Beta.md"],
            )

            connection = sqlite3.connect(db_path)
            try:
                stored_paths = {
                    row[0] for row in connection.execute("SELECT path FROM note;").fetchall()
                }
            finally:
                connection.close()

            self.assertEqual(scoped_stats.scanned_notes, 2)
            self.assertEqual(scoped_stats.created_notes, 2)
            self.assertEqual(scoped_stats.updated_notes, 0)
            self.assertEqual(
                stored_paths,
                {"Alpha.md", "nested/Beta.md"},
            )

    def test_ingest_vault_writes_chunk_embeddings_when_provider_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            note_path = vault_path / "Alpha.md"
            note_path.write_text(
                "# Alpha\n\nalpha vector text\n",
                encoding="utf-8",
            )
            settings = replace(
                get_settings(),
                cloud_base_url="https://example.com",
                cloud_embedding_model="text-embedding-test",
                local_embedding_model="",
            )

            with patch(
                "app.indexing.ingest.embed_texts",
                return_value=EmbeddingBatchResult(
                    embeddings=[[1.0, 0.0]],
                    provider_key="cloud",
                    provider_name=settings.cloud_provider_name,
                    model_name=settings.cloud_embedding_model,
                ),
            ) as mocked_embed:
                ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)

            connection = sqlite3.connect(db_path)
            try:
                embedding_rows = connection.execute(
                    """
                    SELECT provider_key, provider_name, model_name, embedding_dim
                    FROM chunk_embedding;
                    """
                ).fetchall()
            finally:
                connection.close()

            mocked_embed.assert_called_once()
            self.assertEqual(len(embedding_rows), 1)
            self.assertEqual(embedding_rows[0][0], "cloud")
            self.assertEqual(embedding_rows[0][1], settings.cloud_provider_name)
            self.assertEqual(embedding_rows[0][2], settings.cloud_embedding_model)
            self.assertEqual(embedding_rows[0][3], 2)

    def test_ingest_vault_replaces_chunk_embeddings_when_note_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            note_path = vault_path / "Alpha.md"
            settings = replace(
                get_settings(),
                cloud_base_url="https://example.com",
                cloud_embedding_model="text-embedding-test",
                local_embedding_model="",
            )
            note_path.write_text(
                "# Alpha\n\nbody\n\n## Detail\n\nmore detail\n",
                encoding="utf-8",
            )

            with patch(
                "app.indexing.ingest.embed_texts",
                side_effect=[
                    EmbeddingBatchResult(
                        embeddings=[[1.0, 0.0], [0.0, 1.0]],
                        provider_key="cloud",
                        provider_name=settings.cloud_provider_name,
                        model_name=settings.cloud_embedding_model,
                    ),
                    EmbeddingBatchResult(
                        embeddings=[[0.5, 0.5]],
                        provider_key="cloud",
                        provider_name=settings.cloud_provider_name,
                        model_name=settings.cloud_embedding_model,
                    ),
                ],
            ):
                ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)
                note_path.write_text(
                    "# Alpha\n\nbody only\n",
                    encoding="utf-8",
                )
                ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)

            connection = sqlite3.connect(db_path)
            try:
                chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
                embedding_count = connection.execute(
                    "SELECT COUNT(*) FROM chunk_embedding;"
                ).fetchone()[0]
                current_chunk_ids = {
                    row[0] for row in connection.execute("SELECT chunk_id FROM chunk;").fetchall()
                }
                embedded_chunk_ids = {
                    row[0]
                    for row in connection.execute(
                        "SELECT chunk_id FROM chunk_embedding;"
                    ).fetchall()
                }
            finally:
                connection.close()

            self.assertEqual(chunk_count, 1)
            self.assertEqual(embedding_count, 1)
            self.assertEqual(embedded_chunk_ids, current_chunk_ids)


if __name__ == "__main__":
    unittest.main()
