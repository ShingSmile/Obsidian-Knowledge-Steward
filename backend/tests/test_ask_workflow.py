from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Response

from app.config import get_settings
from app.contracts.workflow import (
    AskResultMode,
    RetrievalMetadataFilter,
    RunStatus,
    WorkflowAction,
    WorkflowInvokeRequest,
)
from app.graphs.ask_graph import invoke_ask_graph
from app.indexing.ingest import ingest_vault
from app.main import invoke_workflow
from app.observability.runtime_trace import query_run_trace_events_in_db
from app.retrieval.embeddings import EmbeddingBatchResult
from app.services.ask import run_minimal_ask


class AskWorkflowTests(unittest.TestCase):
    def test_run_minimal_ask_returns_retrieval_only_when_no_chat_provider_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                cloud_base_url="",
                cloud_chat_model="",
                local_chat_model="",
            )

            result = run_minimal_ask(
                WorkflowInvokeRequest(
                    action_type=WorkflowAction.ASK_QA,
                    user_query="Roadmap",
                ),
                settings=settings,
            )

            self.assertEqual(result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertTrue(result.model_fallback_used)
            self.assertEqual(result.model_fallback_reason, "no_available_chat_provider")
            self.assertFalse(result.retrieval_fallback_used)
            self.assertGreaterEqual(len(result.citations), 1)
            self.assertIn("当前未使用模型生成答案", result.answer)

    def test_run_minimal_ask_returns_generated_answer_when_provider_call_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                cloud_base_url="https://example.com",
                cloud_chat_model="gpt-test",
                local_chat_model="",
            )

            with patch("app.services.ask._request_grounded_answer", return_value="Roadmap 已拆成检索与 ask 两段实现。[1]") as mocked_request:
                result = run_minimal_ask(
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    settings=settings,
                )

            self.assertEqual(result.mode, AskResultMode.GENERATED_ANSWER)
            self.assertFalse(result.model_fallback_used)
            self.assertEqual(result.provider_name, settings.cloud_provider_name)
            self.assertEqual(result.model_name, "gpt-test")
            self.assertIn("[1]", result.answer)
            mocked_request.assert_called_once()

    def test_run_minimal_ask_consumes_hybrid_retrieval_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = temp_root / "vault"
            vault_path.mkdir()
            db_path = temp_root / "knowledge_steward.sqlite3"
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                cloud_base_url="https://example.com",
                cloud_embedding_model="text-embedding-test",
                cloud_chat_model="",
                local_chat_model="",
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
                result = run_minimal_ask(
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    settings=settings,
                )

            self.assertEqual(result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertGreaterEqual(len(result.retrieved_candidates), 2)
            self.assertEqual(result.retrieved_candidates[0].retrieval_source, "hybrid_rrf")
            self.assertEqual(Path(result.retrieved_candidates[0].path).name, "Roadmap.md")
            self.assertEqual(Path(result.retrieved_candidates[1].path).name, "Strategy.md")
            self.assertEqual(result.citations[0].retrieval_source, "hybrid_rrf")

    def test_run_minimal_ask_downgrades_when_generated_answer_has_no_citation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                cloud_base_url="https://example.com",
                cloud_chat_model="gpt-test",
                local_chat_model="",
            )

            with patch(
                "app.services.ask._request_grounded_answer",
                return_value="Roadmap 已拆成检索与 ask 两段实现。",
            ):
                result = run_minimal_ask(
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    settings=settings,
                )

            self.assertEqual(result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertTrue(result.model_fallback_used)
            self.assertEqual(
                result.model_fallback_reason,
                "citation_alignment_missing_reference",
            )
            self.assertIn("当前未使用模型生成答案", result.answer)

    def test_run_minimal_ask_downgrades_when_generated_answer_has_out_of_range_citation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                cloud_base_url="https://example.com",
                cloud_chat_model="gpt-test",
                local_chat_model="",
            )

            with patch(
                "app.services.ask._request_grounded_answer",
                return_value="Roadmap 已拆成检索与 ask 两段实现。[9]",
            ):
                result = run_minimal_ask(
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    settings=settings,
                )

            self.assertEqual(result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertTrue(result.model_fallback_used)
            self.assertEqual(
                result.model_fallback_reason,
                "citation_alignment_out_of_range",
            )
            self.assertIn("[1]", result.answer)

    def test_invoke_workflow_returns_completed_ask_result_with_retrieval_fallback_signal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            response = Response()
            request = WorkflowInvokeRequest(
                action_type=WorkflowAction.ASK_QA,
                user_query="Roadmap",
                retrieval_filter=RetrievalMetadataFilter(note_types=["summary_note"]),
            )

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                    cloud_base_url="",
                    cloud_chat_model="",
                    local_chat_model="",
                ),
            ):
                result = invoke_workflow(request, response)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertTrue(result.thread_id.startswith("thread_"))
            self.assertTrue(result.run_id.startswith("run_"))
            self.assertIsNotNone(result.ask_result)
            self.assertEqual(result.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertTrue(result.ask_result.retrieval_fallback_used)
            self.assertEqual(
                result.ask_result.retrieval_fallback_reason,
                "metadata_filters_too_strict",
            )
            self.assertEqual(result.message, "Ask workflow completed with retrieval-only fallback.")
            self.assertTrue(trace_path.exists())

    def test_invoke_workflow_preserves_explicit_thread_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            response = Response()
            request = WorkflowInvokeRequest(
                thread_id="thread_existing_ask",
                action_type=WorkflowAction.ASK_QA,
                user_query="Roadmap",
            )

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                    cloud_base_url="",
                    cloud_chat_model="",
                    local_chat_model="",
                ),
            ):
                result = invoke_workflow(request, response)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.thread_id, "thread_existing_ask")
            self.assertIsNotNone(result.ask_result)
            self.assertEqual(result.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)

    def test_invoke_workflow_downgrades_invalid_generated_answer_to_retrieval_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            response = Response()
            request = WorkflowInvokeRequest(
                action_type=WorkflowAction.ASK_QA,
                user_query="Roadmap",
            )

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                    cloud_base_url="https://example.com",
                    cloud_chat_model="gpt-test",
                    local_chat_model="",
                ),
            ):
                with patch(
                    "app.services.ask._request_grounded_answer",
                    return_value="Roadmap 已拆成检索与 ask 两段实现。[9]",
                ):
                    result = invoke_workflow(request, response)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertIsNotNone(result.ask_result)
            self.assertEqual(result.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertTrue(result.ask_result.model_fallback_used)
            self.assertEqual(
                result.ask_result.model_fallback_reason,
                "citation_alignment_out_of_range",
            )
            self.assertEqual(result.message, "Ask workflow completed with retrieval-only fallback.")

    def test_invoke_workflow_resumes_completed_ask_from_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                ask_runtime_trace_path=trace_path,
                cloud_base_url="",
                cloud_chat_model="",
                local_chat_model="",
            )

            with patch("app.main.settings", settings):
                first_result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_resume_ask",
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    Response(),
                )

                with patch(
                    "app.graphs.ask_graph.run_minimal_ask",
                    side_effect=AssertionError("resume should not rerun ask execution"),
                ):
                    resumed_response = Response()
                    resumed_result = invoke_workflow(
                        WorkflowInvokeRequest(
                            thread_id="thread_resume_ask",
                            action_type=WorkflowAction.ASK_QA,
                            user_query="Roadmap",
                            resume_from_checkpoint=True,
                        ),
                        resumed_response,
                    )

            self.assertEqual(resumed_response.status_code, 200)
            self.assertEqual(resumed_result.message, "Ask workflow resumed from checkpoint.")
            self.assertEqual(resumed_result.thread_id, "thread_resume_ask")
            self.assertNotEqual(resumed_result.run_id, first_result.run_id)
            self.assertIsNotNone(resumed_result.ask_result)
            self.assertEqual(resumed_result.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)

            resumed_trace_events = query_run_trace_events_in_db(
                db_path,
                run_id=resumed_result.run_id,
            )
            self.assertEqual(len(resumed_trace_events), 1)
            self.assertEqual(resumed_trace_events[0].node_name, "checkpoint_resume")
            self.assertEqual(resumed_trace_events[0].event_type, "hit")

    def test_invoke_ask_graph_keeps_thread_id_and_emits_trace_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                ask_runtime_trace_path=trace_path,
                cloud_base_url="",
                cloud_chat_model="",
                local_chat_model="",
            )
            trace_events: list[dict[str, object]] = []

            execution = invoke_ask_graph(
                WorkflowInvokeRequest(
                    thread_id="thread_graph_test",
                    action_type=WorkflowAction.ASK_QA,
                    user_query="Roadmap",
                ),
                settings=settings,
                thread_id="thread_graph_test",
                run_id="run_graph_test",
                trace_hook=trace_events.append,
            )

            self.assertEqual(execution.thread_id, "thread_graph_test")
            self.assertEqual(execution.run_id, "run_graph_test")
            self.assertEqual(execution.graph_name, "ask_graph")
            self.assertEqual(execution.action_type, WorkflowAction.ASK_QA)
            self.assertEqual(execution.state["thread_id"], "thread_graph_test")
            self.assertEqual(execution.state["run_id"], "run_graph_test")
            self.assertEqual(execution.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertEqual(len(execution.trace_events), 3)
            self.assertEqual(
                [event["node_name"] for event in execution.trace_events],
                ["prepare_ask", "execute_ask", "finalize_ask"],
            )
            self.assertEqual(len(trace_events), 3)
            self.assertTrue(all(event["thread_id"] == "thread_graph_test" for event in trace_events))
            persisted_events = [
                json.loads(line)
                for line in trace_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(persisted_events), 3)
            self.assertEqual(
                [event["node_name"] for event in persisted_events],
                ["prepare_ask", "execute_ask", "finalize_ask"],
            )
            self.assertTrue(all(event["run_id"] == "run_graph_test" for event in persisted_events))
            self.assertTrue(
                all(
                    {
                        "thread_id",
                        "run_id",
                        "node_name",
                        "event_type",
                        "timestamp",
                    }.issubset(event.keys())
                    for event in persisted_events
                )
            )

    def test_invoke_workflow_persists_run_trace_rows_and_supports_query(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            response = Response()

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                    cloud_base_url="",
                    cloud_chat_model="",
                    local_chat_model="",
                ),
            ):
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 200)
            run_trace_events = query_run_trace_events_in_db(db_path, run_id=result.run_id)
            self.assertEqual(len(run_trace_events), 3)
            self.assertEqual(
                [event.node_name for event in run_trace_events],
                ["prepare_ask", "execute_ask", "finalize_ask"],
            )
            self.assertTrue(all(event.run_id == result.run_id for event in run_trace_events))
            self.assertTrue(all(event.thread_id == result.thread_id for event in run_trace_events))
            self.assertIn("query_length", run_trace_events[0].details)
            self.assertIn("result_mode", run_trace_events[1].details)

            thread_trace_events = query_run_trace_events_in_db(
                db_path,
                thread_id=result.thread_id,
            )
            self.assertEqual(
                [event.trace_id for event in thread_trace_events],
                [event.trace_id for event in run_trace_events],
            )

    def test_invoke_ask_graph_checkpoint_save_failure_does_not_block_ask(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                ask_runtime_trace_path=trace_path,
                cloud_base_url="",
                cloud_chat_model="",
                local_chat_model="",
            )

            with patch(
                "app.graphs.runtime.save_graph_checkpoint",
                side_effect=OSError("checkpoint db unavailable"),
            ):
                execution = invoke_ask_graph(
                    WorkflowInvokeRequest(
                        thread_id="thread_checkpoint_save_failure",
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    settings=settings,
                    thread_id="thread_checkpoint_save_failure",
                    run_id="run_checkpoint_save_failure",
                )

            self.assertEqual(execution.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertTrue(
                any(
                    error["source"] == "checkpoint_save"
                    for error in execution.state.get("errors", [])
                )
            )
            self.assertTrue(trace_path.exists())

    def test_invoke_ask_graph_sqlite_trace_failure_does_not_block_ask(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = self._build_index_fixture(Path(temp_dir))
            trace_path = Path(temp_dir) / "traces" / "ask_runtime.jsonl"
            settings = replace(
                get_settings(),
                index_db_path=db_path,
                ask_runtime_trace_path=trace_path,
                cloud_base_url="",
                cloud_chat_model="",
                local_chat_model="",
            )
            trace_events: list[dict[str, object]] = []

            def _broken_sqlite_sink(_event: dict[str, object]) -> None:
                raise OSError("sqlite sink unavailable")

            with patch(
                "app.graphs.runtime.build_sqlite_trace_hook",
                return_value=_broken_sqlite_sink,
            ):
                execution = invoke_ask_graph(
                    WorkflowInvokeRequest(
                        thread_id="thread_sqlite_trace_failure",
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    settings=settings,
                    thread_id="thread_sqlite_trace_failure",
                    run_id="run_sqlite_trace_failure",
                    trace_hook=trace_events.append,
                )

            self.assertEqual(execution.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)
            self.assertEqual(len(trace_events), 3)
            self.assertTrue(trace_path.exists())
            persisted_events = [
                json.loads(line)
                for line in trace_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(persisted_events), 3)

    def test_invoke_workflow_trace_write_failure_does_not_block_ask(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            db_path = self._build_index_fixture(temp_root)
            blocked_parent = temp_root / "trace_parent_is_a_file"
            blocked_parent.write_text("occupied", encoding="utf-8")
            response = Response()

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    index_db_path=db_path,
                    ask_runtime_trace_path=blocked_parent / "ask_runtime.jsonl",
                    cloud_base_url="",
                    cloud_chat_model="",
                    local_chat_model="",
                ),
            ):
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.ASK_QA,
                        user_query="Roadmap",
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertIsNotNone(result.ask_result)
            self.assertEqual(result.ask_result.mode, AskResultMode.RETRIEVAL_ONLY)

    def test_invoke_workflow_rejects_resume_without_explicit_thread_id(self) -> None:
        with self.assertRaises(HTTPException) as context:
            invoke_workflow(
                WorkflowInvokeRequest(
                    action_type=WorkflowAction.ASK_QA,
                    user_query="Roadmap",
                    resume_from_checkpoint=True,
                ),
                Response(),
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("explicit thread_id", context.exception.detail)

    def test_invoke_workflow_rejects_blank_ask_query(self) -> None:
        with self.assertRaises(HTTPException) as context:
            invoke_workflow(
                WorkflowInvokeRequest(
                    action_type=WorkflowAction.ASK_QA,
                    user_query="   ",
                ),
                Response(),
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("non-empty user_query", context.exception.detail)

    @staticmethod
    def _build_index_fixture(temp_root: Path) -> Path:
        vault_path = temp_root / "vault"
        vault_path.mkdir()
        db_path = temp_root / "knowledge_steward.sqlite3"

        (vault_path / "Roadmap.md").write_text(
            "# Roadmap\n\nThe roadmap details live here.\n\n## Ask\n\nAsk response should carry citations.\n",
            encoding="utf-8",
        )
        ingest_vault(vault_path=vault_path, db_path=db_path)
        return db_path


if __name__ == "__main__":
    unittest.main()
