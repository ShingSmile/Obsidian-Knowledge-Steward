from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from app.config import get_settings
from app.contracts.workflow import RetrievalMetadataFilter
from app.indexing.ingest import ingest_vault
from app.retrieval.sqlite_fts import search_chunks_in_db


class SqliteFTSRetrievalTests(unittest.TestCase):
    def test_search_chunks_supports_natural_language_date_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            (vault_path / "日常" / "2023-06").mkdir(parents=True)
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "日常" / "2023-06" / "2023-06-05_星期一.md").write_text(
                "# 一、 工作任务\n\n"
                "- [ ] 对v6.2.5迭代进行总结复盘\n"
                "- [x] 周报完成 ✅ 2023-06-05\n"
                "- [ ] 自测相关工作继续推进\n",
                encoding="utf-8",
            )
            (vault_path / "日常" / "2023-06" / "2023-06-06_星期二.md").write_text(
                "# 一、 工作任务\n\n"
                "- [ ] 普通跟进事项\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)
            response = search_chunks_in_db(
                db_path,
                "2023-06-05 的工作任务里有哪些还没完成的事项？",
                limit=5,
            )

            self.assertGreaterEqual(len(response.candidates), 1)
            self.assertEqual(
                response.candidates[0].path,
                "日常/2023-06/2023-06-05_星期一.md",
            )

    def test_search_chunks_supports_natural_language_version_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            (vault_path / "日常" / "2023-06").mkdir(parents=True)
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "日常" / "2023-06" / "v6.2.5迭代总结.md").write_text(
                "# v6.2.5 迭代总结\n\n"
                "## 2、优化点\n\n"
                "- 对业务特征积累熟练度，提高阅读代码的效率\n",
                encoding="utf-8",
            )
            (vault_path / "日常" / "2023-06" / "v6.3.0迭代总结.md").write_text(
                "# v6.3.0 迭代总结\n\n"
                "## 2、优化点\n\n"
                "- 一般性的优化点\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)
            response = search_chunks_in_db(
                db_path,
                "v6.2.5 迭代总结里列了哪些优化点？",
                limit=5,
            )

            self.assertGreaterEqual(len(response.candidates), 1)
            self.assertEqual(
                response.candidates[0].path,
                "日常/2023-06/v6.2.5迭代总结.md",
            )

    def test_search_chunks_returns_standard_candidates_with_metadata_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            (vault_path / "Daily").mkdir(parents=True)
            (vault_path / "Notes").mkdir(parents=True)
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Daily" / "2026-03-14.md").write_text(
                "# 2026-03-14\n\n# 一、工作任务\n\n- [ ] Roadmap tasks\n\n# 四、今日总结\n\nRoadmap wrap-up.\n",
                encoding="utf-8",
            )
            (vault_path / "Notes" / "Roadmap.md").write_text(
                "# Roadmap\n\nThe roadmap details live here.\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)
            response = search_chunks_in_db(
                db_path,
                "roadmap",
                limit=5,
                metadata_filter=RetrievalMetadataFilter(
                    note_types=["DAILY_NOTE"],
                    template_families=["daily_cn_template"],
                ),
            )

            self.assertFalse(response.fallback_used)
            self.assertGreaterEqual(len(response.candidates), 1)
            self.assertEqual(response.requested_filters.note_types, ["daily_note"])
            self.assertEqual(response.effective_filters.template_families, ["daily_cn_template"])
            self.assertTrue(all(candidate.chunk_id for candidate in response.candidates))
            self.assertTrue(all(candidate.path.endswith(".md") for candidate in response.candidates))
            self.assertTrue(all(candidate.score >= 0 for candidate in response.candidates))
            self.assertTrue(all(candidate.snippet for candidate in response.candidates))
            self.assertTrue(all(candidate.text for candidate in response.candidates))
            self.assertTrue(all(candidate.retrieval_source == "sqlite_fts" for candidate in response.candidates))
            self.assertTrue(any("[Roadmap]" in candidate.snippet for candidate in response.candidates))
            self.assertTrue(all(candidate.note_type == "daily_note" for candidate in response.candidates))
            self.assertTrue(
                all(candidate.template_family == "daily_cn_template" for candidate in response.candidates)
            )
            self.assertEqual(
                {candidate.path for candidate in response.candidates},
                {"Daily/2026-03-14.md"},
            )

    def test_search_chunks_supports_path_prefix_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            (vault_path / "Alpha").mkdir(parents=True)
            (vault_path / "Beta").mkdir(parents=True)
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Alpha" / "Alpha.md").write_text(
                "# Alpha\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )
            (vault_path / "Beta" / "Beta.md").write_text(
                "# Beta\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)
            response = search_chunks_in_db(
                db_path,
                "Plan",
                limit=5,
                metadata_filter=RetrievalMetadataFilter(
                    path_prefixes=["Alpha/"],
                ),
            )

            self.assertFalse(response.fallback_used)
            self.assertEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].path, "Alpha/Alpha.md")

    def test_search_chunks_normalizes_absolute_path_prefix_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            (vault_path / "Alpha").mkdir(parents=True)
            (vault_path / "Beta").mkdir(parents=True)
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Alpha" / "Alpha.md").write_text(
                "# Alpha\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )
            (vault_path / "Beta" / "Beta.md").write_text(
                "# Beta\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(get_settings(), sample_vault_dir=vault_path)
            response = search_chunks_in_db(
                db_path,
                "Plan",
                limit=5,
                metadata_filter=RetrievalMetadataFilter(
                    path_prefixes=[str((vault_path / "Alpha").resolve())],
                ),
                settings=settings,
            )

            self.assertFalse(response.fallback_used)
            self.assertEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].path, "Alpha/Alpha.md")

    def test_search_chunks_falls_back_when_metadata_filter_is_too_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Roadmap.md").write_text(
                "# Roadmap\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)
            response = search_chunks_in_db(
                db_path,
                "Roadmap",
                limit=3,
                metadata_filter=RetrievalMetadataFilter(note_types=["summary_note"]),
            )

            self.assertTrue(response.fallback_used)
            self.assertEqual(response.fallback_reason, "metadata_filters_too_strict")
            self.assertEqual(response.requested_filters.note_types, ["summary_note"])
            self.assertTrue(response.effective_filters.is_empty())
            self.assertEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].path, "Roadmap.md")

    def test_search_chunks_normalizes_punctuation_and_rejects_blank_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"

            (vault_path / "Roadmap.md").write_text(
                "# Roadmap\n\nPlan the next retrieval iteration.\n",
                encoding="utf-8",
            )

            ingest_vault(vault_path=vault_path, db_path=db_path)
            response = search_chunks_in_db(db_path, "Roadmap!!!", limit=3)

            self.assertEqual(len(response.candidates), 1)
            self.assertEqual(response.candidates[0].path, "Roadmap.md")

            with self.assertRaises(ValueError):
                search_chunks_in_db(db_path, "   ", limit=3)


if __name__ == "__main__":
    unittest.main()
