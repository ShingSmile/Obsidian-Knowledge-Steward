from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import Response

from app.config import get_settings
from app.contracts.workflow import RunStatus, WorkflowAction, WorkflowInvokeRequest
from app.indexing.ingest import ingest_vault
from app.main import WORKFLOW_INVOKE_HANDLERS, invoke_workflow


class WorkflowInvokeContractTests(unittest.TestCase):
    def test_workflow_invoke_handler_registry_covers_all_supported_actions(self) -> None:
        self.assertEqual(set(WORKFLOW_INVOKE_HANDLERS.keys()), set(WorkflowAction))

    def test_invoke_workflow_uses_shared_response_contract_for_all_supported_actions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
                ask_runtime_trace_path=trace_path,
                cloud_base_url="",
                cloud_chat_model="",
                local_chat_model="",
            )

            # 先预热索引，让 ask / digest 都走真实统一入口，而不是被空索引短路成无意义分支。
            ingest_vault(vault_path=vault_path, db_path=db_path, settings=settings)

            cases = [
                (
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Alpha",
                    ),
                    "ask_result",
                ),
                (
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.INGEST_STEWARD,
                        note_path="Alpha.md",
                    ),
                    "ingest_result",
                ),
                (
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.DAILY_DIGEST,
                    ),
                    "digest_result",
                ),
            ]

            with patch("app.main.settings", settings):
                for request, expected_result_field in cases:
                    with self.subTest(action_type=request.action_type.value):
                        response = Response()
                        result = invoke_workflow(request, response)

                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(result.action_type, request.action_type)
                        self.assertEqual(result.status, RunStatus.COMPLETED)
                        self.assertTrue(result.thread_id.startswith("thread_"))
                        self.assertTrue(result.run_id.startswith("run_"))
                        self.assertIsInstance(result.message, str)
                        self.assertFalse(result.approval_required)
                        self.assertIsNotNone(getattr(result, expected_result_field))

                        for other_field in ("ask_result", "ingest_result", "digest_result"):
                            if other_field == expected_result_field:
                                continue
                            self.assertIsNone(getattr(result, other_field))

    @staticmethod
    def _build_vault_fixture(temp_root: Path) -> Path:
        vault_path = temp_root / "vault"
        vault_path.mkdir()
        (vault_path / "Alpha.md").write_text(
            "# Alpha\n\nAlpha note for ask and ingest.\n",
            encoding="utf-8",
        )
        (vault_path / "2026-03-14.md").write_text(
            "# 一、工作任务\n- [ ] 完成 workflow contract\n\n# 四、今日总结\n今天统一了 invoke 入口。\n",
            encoding="utf-8",
        )
        (vault_path / "迭代总结.md").write_text(
            "# 迭代总结\n\n本周主要收敛了 ask / ingest / digest 入口。\n",
            encoding="utf-8",
        )
        return vault_path


if __name__ == "__main__":
    unittest.main()
