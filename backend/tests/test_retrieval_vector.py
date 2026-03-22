from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.config import get_settings
from app.indexing.ingest import ingest_vault
from app.retrieval.embeddings import EmbeddingBatchResult
from app.retrieval.sqlite_vector import search_chunk_vectors_in_db


class SqliteVectorRetrievalTests(unittest.TestCase):
    def test_search_chunk_vectors_returns_standard_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            settings = replace(
                get_settings(),
                cloud_base_url="https://example.com",
                cloud_embedding_model="text-embedding-test",
                local_embedding_model="",
            )

            alpha_path = vault_path / "Alpha.md"
            beta_path = vault_path / "Beta.md"
            alpha_path.write_text("# Alpha\n\nalpha vector topic\n", encoding="utf-8")
            beta_path.write_text("# Beta\n\nbeta vector topic\n", encoding="utf-8")

            with patch(
                "app.indexing.ingest.embed_texts",
                side_effect=lambda texts, **_: EmbeddingBatchResult(
                    embeddings=[
                        [1.0, 0.0] if "alpha" in text else [0.0, 1.0]
                        for text in texts
                    ],
                    provider_key="cloud",
                    provider_name=settings.cloud_provider_name,
                    model_name=settings.cloud_embedding_model,
                ),
            ):
                ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)

            with patch(
                "app.retrieval.sqlite_vector.embed_texts",
                return_value=EmbeddingBatchResult(
                    embeddings=[[1.0, 0.0]],
                    provider_key="cloud",
                    provider_name=settings.cloud_provider_name,
                    model_name=settings.cloud_embedding_model,
                ),
            ):
                response = search_chunk_vectors_in_db(
                    db_path,
                    "alpha question",
                    settings=settings,
                    limit=2,
                )

            self.assertFalse(response.disabled)
            self.assertFalse(response.fallback_used)
            self.assertEqual(response.provider_name, settings.cloud_provider_name)
            self.assertEqual(response.model_name, settings.cloud_embedding_model)
            self.assertGreaterEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].retrieval_source, "sqlite_vector")
            self.assertEqual(Path(response.candidates[0].path).name, "Alpha.md")
            self.assertGreater(response.candidates[0].score, 0)
            self.assertTrue(response.candidates[0].snippet)

    def test_search_chunk_vectors_disables_when_provider_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Alpha.md").write_text("# Alpha\n\nalpha vector topic\n", encoding="utf-8")
            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(
                get_settings(),
                cloud_base_url="",
                cloud_embedding_model="",
                local_embedding_model="",
            )

            response = search_chunk_vectors_in_db(
                db_path,
                "alpha question",
                settings=settings,
                limit=2,
            )

            self.assertTrue(response.disabled)
            self.assertEqual(response.disabled_reason, "no_available_embedding_provider")
            self.assertEqual(response.candidates, [])

    def test_search_chunk_vectors_disables_when_vector_index_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Alpha.md").write_text("# Alpha\n\nalpha vector topic\n", encoding="utf-8")
            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(
                get_settings(),
                cloud_base_url="https://example.com",
                cloud_embedding_model="text-embedding-test",
                local_embedding_model="",
            )

            with patch(
                "app.retrieval.sqlite_vector.embed_texts",
                return_value=EmbeddingBatchResult(
                    embeddings=[[1.0, 0.0]],
                    provider_key="cloud",
                    provider_name=settings.cloud_provider_name,
                    model_name=settings.cloud_embedding_model,
                ),
            ):
                response = search_chunk_vectors_in_db(
                    db_path,
                    "alpha question",
                    settings=settings,
                    limit=2,
                )

            self.assertTrue(response.disabled)
            self.assertEqual(response.disabled_reason, "vector_index_not_ready")
            self.assertEqual(response.candidates, [])


if __name__ == "__main__":
    unittest.main()
