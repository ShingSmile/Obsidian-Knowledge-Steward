from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from app.benchmark.ask_retrieval_preflight import run_local_retrieval_preflight
from app.config import Settings, get_settings
from app.indexing.ingest import ingest_vault
from app.retrieval.embeddings import EmbeddingBatchResult


class AskRetrievalPreflightTests(unittest.TestCase):
    def test_run_local_retrieval_preflight_reports_provider_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            db_path = temp_root / "knowledge_steward.sqlite3"
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                cloud_base_url="",
                cloud_embedding_model="",
                local_base_url="",
                local_embedding_model="",
            )

            result = run_local_retrieval_preflight(settings=settings)

        self.assertEqual(result.status, "provider_not_configured")
        self.assertIsNone(result.provider_name)
        self.assertIsNone(result.model_name)
        self.assertIn("KS_LOCAL_BASE_URL", result.message)
        self.assertIn("KS_LOCAL_EMBEDDING_MODEL", result.message)

    def test_run_local_retrieval_preflight_reports_provider_probe_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_settings, db_path = _build_fixture_database(Path(temp_dir))

            with patch(
                "app.benchmark.ask_retrieval_preflight.embed_texts",
                return_value=EmbeddingBatchResult(
                    embeddings=[],
                    provider_key="local",
                    provider_name=runtime_settings.local_provider_name,
                    model_name=runtime_settings.local_embedding_model,
                    disabled=True,
                    disabled_reason="all_embedding_providers_failed",
                ),
            ):
                result = run_local_retrieval_preflight(
                    settings=runtime_settings,
                    db_path=db_path,
                )

        self.assertEqual(result.status, "provider_unreachable_or_model_unavailable")
        self.assertEqual(result.provider_key, "local")
        self.assertEqual(result.provider_name, runtime_settings.local_provider_name)
        self.assertEqual(result.model_name, runtime_settings.local_embedding_model)
        self.assertIn(
            f"{runtime_settings.local_provider_name}/{runtime_settings.local_embedding_model}",
            result.message,
        )

    def test_run_local_retrieval_preflight_reports_partial_vector_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_settings, db_path = _build_fixture_database(Path(temp_dir))
            _insert_local_embeddings(db_path=db_path, limit=1)

            with patch(
                "app.benchmark.ask_retrieval_preflight.embed_texts",
                return_value=EmbeddingBatchResult(
                    embeddings=[[1.0, 0.0]],
                    provider_key="local",
                    provider_name=runtime_settings.local_provider_name,
                    model_name=runtime_settings.local_embedding_model,
                ),
            ):
                result = run_local_retrieval_preflight(
                    settings=runtime_settings,
                )

        self.assertEqual(result.status, "vector_index_not_ready")
        self.assertEqual(result.provider_key, "local")
        self.assertEqual(result.provider_name, runtime_settings.local_provider_name)
        self.assertEqual(result.model_name, runtime_settings.local_embedding_model)
        self.assertIn(
            f"{runtime_settings.local_provider_name}/{runtime_settings.local_embedding_model}",
            result.message,
        )
        self.assertIn("Run ingest", result.message)

    def test_run_local_retrieval_preflight_reports_ok_with_full_vector_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_settings, db_path = _build_fixture_database(Path(temp_dir))
            _insert_local_embeddings(db_path=db_path)

            with patch(
                "app.benchmark.ask_retrieval_preflight.embed_texts",
                return_value=EmbeddingBatchResult(
                    embeddings=[[1.0, 0.0]],
                    provider_key="local",
                    provider_name=runtime_settings.local_provider_name,
                    model_name=runtime_settings.local_embedding_model,
                ),
            ):
                result = run_local_retrieval_preflight(
                    settings=runtime_settings,
                    db_path=db_path,
                )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.provider_key, "local")
        self.assertEqual(result.provider_name, runtime_settings.local_provider_name)
        self.assertEqual(result.model_name, runtime_settings.local_embedding_model)
        self.assertIn(
            f"{runtime_settings.local_provider_name}/{runtime_settings.local_embedding_model}",
            result.message,
        )


def _build_fixture_database(temp_root: Path) -> tuple[Settings, Path]:
    vault_path = temp_root / "vault"
    vault_path.mkdir()
    db_path = temp_root / "knowledge_steward.sqlite3"
    (vault_path / "Alpha.md").write_text(
        "# Alpha\n\nbody\n\n## Detail\n\nmore detail\n",
        encoding="utf-8",
    )
    runtime_settings = replace(
        get_settings(),
        sample_vault_dir=vault_path,
        index_db_path=db_path,
        cloud_base_url="",
        cloud_embedding_model="",
        local_base_url="http://127.0.0.1:11434",
        local_embedding_model="nomic-embed-text",
    )
    ingest_settings = replace(
        runtime_settings,
        local_base_url="",
        local_embedding_model="",
    )
    ingest_vault(
        vault_path=vault_path,
        db_path=db_path,
        settings=ingest_settings,
    )
    return runtime_settings, db_path


def _insert_local_embeddings(*, db_path: Path, limit: int | None = None) -> None:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT chunk_id, note_id, content_hash
            FROM chunk
            ORDER BY ordinal ASC;
            """
        ).fetchall()
        selected_rows = rows if limit is None else rows[:limit]
        for row in selected_rows:
            connection.execute(
                """
                INSERT INTO chunk_embedding (
                    chunk_id,
                    note_id,
                    provider_key,
                    provider_name,
                    model_name,
                    embedding_dim,
                    vector_norm,
                    embedding_json,
                    content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    row["chunk_id"],
                    row["note_id"],
                    "local",
                    "ollama",
                    "nomic-embed-text",
                    2,
                    1.0,
                    "[1.0, 0.0]",
                    row["content_hash"],
                ),
            )
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    unittest.main()
