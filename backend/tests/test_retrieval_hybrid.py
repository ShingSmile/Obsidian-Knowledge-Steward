from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.config import get_settings
from app.contracts.workflow import RetrievalMetadataFilter
from app.indexing.ingest import ingest_vault
from app.retrieval.embeddings import EmbeddingBatchResult
from app.retrieval.hybrid import search_hybrid_chunks_in_db


class HybridRetrievalTests(unittest.TestCase):
    def test_search_hybrid_chunks_fuses_fts_and_vector_hits_without_duplicates(self) -> None:
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

            (vault_path / "Roadmap.md").write_text(
                "# Roadmap\n\nRoadmap delivery plan.\n",
                encoding="utf-8",
            )
            (vault_path / "Strategy.md").write_text(
                "# Strategy\n\nSemantic strategy note.\n",
                encoding="utf-8",
            )

            with patch(
                "app.indexing.ingest.embed_texts",
                side_effect=lambda texts, **_: EmbeddingBatchResult(
                    embeddings=[
                        [1.0, 0.0]
                        if "roadmap" in text.casefold()
                        else [0.9, 0.1]
                        if "strategy" in text.casefold()
                        else [0.0, 1.0]
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
                response = search_hybrid_chunks_in_db(
                    db_path,
                    "Roadmap",
                    settings=settings,
                    limit=3,
                )

            self.assertFalse(response.fallback_used)
            self.assertGreaterEqual(len(response.candidates), 2)
            self.assertEqual(Path(response.candidates[0].path).name, "Roadmap.md")
            self.assertEqual(response.candidates[0].retrieval_source, "hybrid_rrf")
            self.assertEqual(Path(response.candidates[1].path).name, "Strategy.md")
            self.assertEqual(response.candidates[1].retrieval_source, "sqlite_vector")
            self.assertEqual(
                len({candidate.chunk_id for candidate in response.candidates}),
                len(response.candidates),
            )

    def test_search_hybrid_chunks_falls_back_to_fts_when_vector_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            settings = replace(
                get_settings(),
                cloud_base_url="",
                cloud_embedding_model="",
                local_embedding_model="",
            )

            (vault_path / "Roadmap.md").write_text(
                "# Roadmap\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )
            ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)

            response = search_hybrid_chunks_in_db(
                db_path,
                "Roadmap",
                settings=settings,
                limit=3,
            )

            self.assertFalse(response.fallback_used)
            self.assertEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].retrieval_source, "sqlite_fts")
            self.assertEqual(Path(response.candidates[0].path).name, "Roadmap.md")

    def test_search_hybrid_chunks_uses_shared_metadata_filter_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            settings = replace(
                get_settings(),
                cloud_base_url="",
                cloud_embedding_model="",
                local_embedding_model="",
            )

            (vault_path / "Roadmap.md").write_text(
                "# Roadmap\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )
            ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)

            response = search_hybrid_chunks_in_db(
                db_path,
                "Roadmap",
                settings=settings,
                limit=3,
                metadata_filter=RetrievalMetadataFilter(note_types=["summary_note"]),
            )

            self.assertTrue(response.fallback_used)
            self.assertEqual(response.fallback_reason, "metadata_filters_too_strict")
            self.assertEqual(response.requested_filters.note_types, ["summary_note"])
            self.assertTrue(response.effective_filters.is_empty())
            self.assertEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].retrieval_source, "sqlite_fts")


if __name__ == "__main__":
    unittest.main()
