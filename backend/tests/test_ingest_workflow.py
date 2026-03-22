from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Response

from app.config import get_settings
from app.contracts.workflow import RunStatus, WorkflowAction, WorkflowInvokeRequest
from app.graphs.checkpoint import WorkflowCheckpointStatus, load_graph_checkpoint
from app.graphs.ingest_graph import invoke_ingest_graph
from app.indexing.ingest import IngestRunStats
from app.indexing.store import connect_sqlite, load_proposal
from app.main import invoke_workflow, list_pending_approvals_endpoint
from app.observability.runtime_trace import query_run_trace_events_in_db
from app.retrieval.embeddings import EmbeddingBatchResult
from app.services.ingest_proposal import build_scoped_ingest_approval_proposal


class IngestWorkflowTests(unittest.TestCase):
    def test_scoped_ingest_proposal_records_context_bundle_summary(self) -> None:
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
            )

            with patch("app.main.settings", settings):
                invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_ingest_summary_prewarm",
                        action_type=WorkflowAction.INGEST_STEWARD,
                    ),
                    Response(),
                )

            build_result = build_scoped_ingest_approval_proposal(
                thread_id="thread_ingest_summary",
                note_paths=[str(vault_path / "Alpha.md")],
                db_path=db_path,
                settings=settings,
            )
            self.assertIsNotNone(build_result.proposal)
            self.assertIn("context_bundle_summary", build_result.note_meta)
            bundle_summary = build_result.note_meta["context_bundle_summary"]
            self.assertIsInstance(bundle_summary, dict)
            self.assertGreaterEqual(bundle_summary.get("evidence_count", 0), 1)

    def test_invoke_ingest_graph_returns_stats_and_trace_events(self) -> None:
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
            )
            trace_events: list[dict[str, object]] = []

            execution = invoke_ingest_graph(
                WorkflowInvokeRequest(
                    thread_id="thread_ingest_graph",
                    action_type=WorkflowAction.INGEST_STEWARD,
                ),
                settings=settings,
                thread_id="thread_ingest_graph",
                run_id="run_ingest_graph",
                trace_hook=trace_events.append,
            )

            self.assertEqual(execution.thread_id, "thread_ingest_graph")
            self.assertEqual(execution.run_id, "run_ingest_graph")
            self.assertEqual(execution.graph_name, "ingest_graph")
            self.assertEqual(execution.action_type, WorkflowAction.INGEST_STEWARD)
            self.assertEqual(execution.state["thread_id"], "thread_ingest_graph")
            self.assertEqual(execution.state["run_id"], "run_ingest_graph")
            self.assertEqual(execution.ingest_result.scanned_notes, 2)
            self.assertEqual(execution.ingest_result.created_notes, 2)
            self.assertEqual(execution.ingest_result.updated_notes, 0)
            self.assertEqual(len(execution.trace_events), 3)
            self.assertEqual(
                [event["node_name"] for event in execution.trace_events],
                ["prepare_ingest", "execute_ingest", "finalize_ingest"],
            )
            self.assertEqual(len(trace_events), 3)
            self.assertTrue(all(event["thread_id"] == "thread_ingest_graph" for event in trace_events))

            persisted_events = [
                json.loads(line)
                for line in trace_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(persisted_events), 3)
            self.assertTrue(all(event["graph_name"] == "ingest_graph" for event in persisted_events))
            self.assertEqual(
                [event["node_name"] for event in persisted_events],
                ["prepare_ingest", "execute_ingest", "finalize_ingest"],
            )

    def test_invoke_workflow_runs_ingest_graph_and_persists_trace_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            response = Response()

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_existing_ingest",
                        action_type=WorkflowAction.INGEST_STEWARD,
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertEqual(result.thread_id, "thread_existing_ingest")
            self.assertEqual(result.message, "Ingest workflow completed with full-vault sync.")
            self.assertIsNotNone(result.ingest_result)
            self.assertEqual(result.ingest_result.scanned_notes, 2)
            self.assertEqual(result.ingest_result.current_chunk_count, 2)

            run_trace_events = query_run_trace_events_in_db(db_path, run_id=result.run_id)
            self.assertEqual(len(run_trace_events), 3)
            self.assertTrue(all(event.graph_name == "ingest_graph" for event in run_trace_events))
            self.assertEqual(
                [event.node_name for event in run_trace_events],
                ["prepare_ingest", "execute_ingest", "finalize_ingest"],
            )
            self.assertIn("scanned_notes", run_trace_events[1].details)
            self.assertTrue(trace_path.exists())

    def test_invoke_workflow_resumes_completed_ingest_from_checkpoint(self) -> None:
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
            )

            with patch("app.main.settings", settings):
                first_result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_resume_ingest",
                        action_type=WorkflowAction.INGEST_STEWARD,
                    ),
                    Response(),
                )

                with patch(
                    "app.graphs.ingest_graph.ingest_vault",
                    side_effect=AssertionError("resume should not rerun full ingest"),
                ):
                    resumed_response = Response()
                    resumed_result = invoke_workflow(
                        WorkflowInvokeRequest(
                            thread_id="thread_resume_ingest",
                            action_type=WorkflowAction.INGEST_STEWARD,
                            resume_from_checkpoint=True,
                        ),
                        resumed_response,
                    )

            self.assertEqual(resumed_response.status_code, 200)
            self.assertEqual(resumed_result.message, "Ingest workflow resumed from checkpoint.")
            self.assertEqual(resumed_result.thread_id, "thread_resume_ingest")
            self.assertNotEqual(resumed_result.run_id, first_result.run_id)
            self.assertIsNotNone(resumed_result.ingest_result)
            self.assertEqual(resumed_result.ingest_result.scanned_notes, 2)

            resumed_trace_events = query_run_trace_events_in_db(
                db_path,
                run_id=resumed_result.run_id,
            )
            self.assertEqual(len(resumed_trace_events), 1)
            self.assertEqual(resumed_trace_events[0].node_name, "checkpoint_resume")
            self.assertEqual(resumed_trace_events[0].event_type, "hit")

    def test_invoke_workflow_runs_scoped_ingest_for_single_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            response = Response()

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        action_type=WorkflowAction.INGEST_STEWARD,
                        note_path="Alpha.md",
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertEqual(result.message, "Ingest workflow completed with scoped note sync.")
            self.assertIsNotNone(result.ingest_result)
            self.assertEqual(result.ingest_result.scanned_notes, 1)
            self.assertEqual(result.ingest_result.created_notes, 1)
            self.assertEqual(result.ingest_result.updated_notes, 0)

            run_trace_events = query_run_trace_events_in_db(db_path, run_id=result.run_id)
            self.assertEqual(len(run_trace_events), 3)
            self.assertEqual(run_trace_events[0].details["ingest_scope"], "scoped_notes")
            self.assertEqual(run_trace_events[0].details["requested_note_count"], 1)

    def test_invoke_workflow_returns_waiting_proposal_for_scoped_ingest_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_ingest_prewarm",
                        action_type=WorkflowAction.INGEST_STEWARD,
                    ),
                    Response(),
                )
                response = Response()
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_ingest_waiting",
                        action_type=WorkflowAction.INGEST_STEWARD,
                        note_path="Alpha.md",
                        require_approval=True,
                        metadata={"approval_mode": "proposal"},
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 202)
            self.assertEqual(result.status, RunStatus.WAITING_FOR_APPROVAL)
            self.assertTrue(result.approval_required)
            self.assertIsNotNone(result.proposal)
            self.assertIsNotNone(result.ingest_result)
            self.assertEqual(result.ingest_result.scanned_notes, 1)
            self.assertEqual(
                Path(result.proposal.target_note_path).resolve(),
                (vault_path / "Alpha.md").resolve(),
            )
            self.assertEqual(len(result.proposal.patch_ops), 2)
            self.assertIsNotNone(result.analysis_result)
            self.assertIn(
                "orphan_hint",
                [finding.finding_type for finding in result.analysis_result.findings],
            )
            self.assertTrue(result.analysis_result.related_candidates)
            self.assertTrue(
                all(
                    Path(candidate.path).resolve() != (vault_path / "Alpha.md").resolve()
                    for candidate in result.analysis_result.related_candidates
                )
            )
            self.assertTrue(
                any(
                    Path(candidate.path).resolve() == (vault_path / "Beta.md").resolve()
                    for candidate in result.analysis_result.related_candidates
                )
            )

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_ingest_waiting",
                graph_name="ingest_graph",
            )
            self.assertIsNotNone(checkpoint)
            self.assertEqual(
                checkpoint.checkpoint_status,
                WorkflowCheckpointStatus.WAITING_FOR_APPROVAL,
            )
            self.assertEqual(checkpoint.last_completed_node, "build_ingest_proposal")
            self.assertEqual(checkpoint.next_node_name, "human_approval")
            self.assertTrue(checkpoint.state["approval_required"])
            self.assertEqual(
                checkpoint.state["proposal"].proposal_id,
                result.proposal.proposal_id,
            )

            connection = connect_sqlite(db_path)
            try:
                persisted_proposal = load_proposal(
                    connection,
                    proposal_id=result.proposal.proposal_id,
                )
            finally:
                connection.close()

            self.assertIsNotNone(persisted_proposal)
            self.assertEqual(persisted_proposal.thread_id, "thread_ingest_waiting")
            self.assertEqual(len(persisted_proposal.proposal.evidence), 3)
            self.assertTrue(
                any(
                    Path(evidence.source_path).resolve() == (vault_path / "Beta.md").resolve()
                    for evidence in persisted_proposal.proposal.evidence
                )
            )

            run_trace_events = query_run_trace_events_in_db(
                db_path,
                run_id=result.run_id,
            )
            self.assertEqual(
                [event.node_name for event in run_trace_events],
                ["prepare_ingest", "execute_ingest", "build_ingest_proposal", "human_approval"],
            )
            self.assertEqual(run_trace_events[-1].event_type, "waiting")
            self.assertGreater(run_trace_events[2].details["related_candidate_count"], 0)

    def test_pending_approvals_endpoint_lists_waiting_ingest_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_ingest_inbox",
                        action_type=WorkflowAction.INGEST_STEWARD,
                        note_path="Alpha.md",
                        require_approval=True,
                        metadata={"approval_mode": "proposal"},
                    ),
                    Response(),
                )
                pending_response = list_pending_approvals_endpoint()

            self.assertEqual(len(pending_response.items), 1)
            pending_item = pending_response.items[0]
            self.assertEqual(pending_item.thread_id, "thread_ingest_inbox")
            self.assertEqual(pending_item.graph_name, "ingest_graph")
            self.assertEqual(pending_item.proposal_id, result.proposal.proposal_id)
            self.assertEqual(pending_item.action_type, WorkflowAction.INGEST_STEWARD)
            self.assertEqual(
                Path(pending_item.target_note_path).resolve(),
                (vault_path / "Alpha.md").resolve(),
            )

    def test_ingest_proposal_analysis_can_consume_hybrid_related_candidates(self) -> None:
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
                cloud_base_url="https://example.com",
                cloud_embedding_model="text-embedding-test",
                local_embedding_model="",
            )

            with patch(
                "app.indexing.ingest.embed_texts",
                side_effect=lambda texts, **_: EmbeddingBatchResult(
                    embeddings=[
                        [1.0, 0.0] if "alpha" in text.casefold() else [0.8, 0.2]
                        for text in texts
                    ],
                    provider_key="cloud",
                    provider_name=settings.cloud_provider_name,
                    model_name=settings.cloud_embedding_model,
                ),
            ):
                with patch(
                    "app.retrieval.sqlite_vector.embed_texts",
                    return_value=EmbeddingBatchResult(
                        embeddings=[[1.0, 0.0]],
                        provider_key="cloud",
                        provider_name=settings.cloud_provider_name,
                        model_name=settings.cloud_embedding_model,
                    ),
                ):
                    with patch("app.main.settings", settings):
                        invoke_workflow(
                            WorkflowInvokeRequest(
                                thread_id="thread_ingest_hybrid_prewarm",
                                action_type=WorkflowAction.INGEST_STEWARD,
                            ),
                            Response(),
                        )
                        response = Response()
                        result = invoke_workflow(
                            WorkflowInvokeRequest(
                                thread_id="thread_ingest_hybrid_waiting",
                                action_type=WorkflowAction.INGEST_STEWARD,
                                note_path="Alpha.md",
                                require_approval=True,
                                metadata={"approval_mode": "proposal"},
                            ),
                            response,
                        )

            self.assertEqual(response.status_code, 202)
            self.assertEqual(result.status, RunStatus.WAITING_FOR_APPROVAL)
            self.assertIsNotNone(result.analysis_result)
            self.assertTrue(result.analysis_result.related_candidates)
            self.assertTrue(
                any(
                    Path(candidate.path).resolve() == (vault_path / "Beta.md").resolve()
                    and candidate.retrieval_source == "hybrid_rrf"
                    for candidate in result.analysis_result.related_candidates
                )
            )

    def test_invoke_workflow_returns_completed_when_ingest_proposal_cannot_be_built(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            (vault_path / "2026-03-18.md").write_text(
                "---\n"
                "tags:\n"
                "  - daily\n"
                "---\n"
                "# Task Planner\n"
                "\n"
                "Review [[Alpha]].\n"
                "\n"
                "# Summary\n"
                "\n"
                "Stable daily note body.\n",
                encoding="utf-8",
            )

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                response = Response()
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_ingest_no_proposal",
                        action_type=WorkflowAction.INGEST_STEWARD,
                        note_path="2026-03-18.md",
                        require_approval=True,
                        metadata={"approval_mode": "proposal"},
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertFalse(result.approval_required)
            self.assertIsNone(result.proposal)
            self.assertEqual(
                result.message,
                "Ingest workflow completed with scoped note sync; no approval proposal was generated.",
            )
            self.assertIsNotNone(result.analysis_result)
            self.assertTrue(result.analysis_result.fallback_used)
            self.assertEqual(
                result.analysis_result.fallback_reason,
                "no_governance_issues_detected",
            )
            self.assertEqual(result.analysis_result.findings, [])

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_ingest_no_proposal",
                graph_name="ingest_graph",
            )
            self.assertIsNotNone(checkpoint)
            self.assertEqual(
                checkpoint.checkpoint_status,
                WorkflowCheckpointStatus.COMPLETED,
            )
            self.assertEqual(checkpoint.last_completed_node, "finalize_ingest")
            self.assertEqual(
                checkpoint.state["note_meta"]["skip_reason"],
                "no_governance_issues_detected",
            )

            run_trace_events = query_run_trace_events_in_db(
                db_path,
                run_id=result.run_id,
            )
            self.assertEqual(
                [event.node_name for event in run_trace_events],
                ["prepare_ingest", "execute_ingest", "build_ingest_proposal", "finalize_ingest"],
            )
            self.assertEqual(run_trace_events[2].event_type, "skipped")

    def test_invoke_workflow_rejects_resume_from_checkpoint_for_waiting_ingest_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_ingest_waiting_resume",
                        action_type=WorkflowAction.INGEST_STEWARD,
                        note_path="Alpha.md",
                        require_approval=True,
                        metadata={"approval_mode": "proposal"},
                    ),
                    Response(),
                )

                with self.assertRaises(HTTPException) as context:
                    invoke_workflow(
                        WorkflowInvokeRequest(
                            thread_id="thread_ingest_waiting_resume",
                            action_type=WorkflowAction.INGEST_STEWARD,
                            note_path="Alpha.md",
                            resume_from_checkpoint=True,
                        ),
                        Response(),
                    )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("waiting for approval", context.exception.detail)

    def test_invoke_workflow_rejects_scoped_note_outside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            outside_path = temp_root / "Outside.md"
            outside_path.write_text("# Outside\n\nbody\n", encoding="utf-8")

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    sample_vault_dir=vault_path,
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                with self.assertRaises(HTTPException) as context:
                    invoke_workflow(
                        WorkflowInvokeRequest(
                            action_type=WorkflowAction.INGEST_STEWARD,
                            note_path=str(outside_path),
                        ),
                        Response(),
                    )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("within the configured vault", context.exception.detail)

    def test_invoke_workflow_does_not_resume_completed_checkpoint_when_scope_changes(self) -> None:
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
            )

            with patch("app.main.settings", settings):
                invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_scope_change",
                        action_type=WorkflowAction.INGEST_STEWARD,
                        note_path="Alpha.md",
                    ),
                    Response(),
                )

                with patch(
                    "app.graphs.ingest_graph.ingest_vault",
                    return_value=IngestRunStats(
                        vault_path=str(vault_path.resolve()),
                        db_path=str(db_path.resolve()),
                        scanned_notes=1,
                        created_notes=0,
                        updated_notes=1,
                        current_chunk_count=1,
                        replaced_chunk_count=1,
                    ),
                ) as mocked_ingest:
                    resumed_response = Response()
                    resumed_result = invoke_workflow(
                        WorkflowInvokeRequest(
                            thread_id="thread_scope_change",
                            action_type=WorkflowAction.INGEST_STEWARD,
                            note_path="Beta.md",
                            resume_from_checkpoint=True,
                        ),
                        resumed_response,
                    )

            self.assertEqual(resumed_response.status_code, 200)
            self.assertEqual(
                resumed_result.message,
                "Ingest workflow completed with scoped note sync.",
            )
            mocked_ingest.assert_called_once()

            resumed_trace_events = query_run_trace_events_in_db(
                db_path,
                run_id=resumed_result.run_id,
            )
            checkpoint_miss_events = [
                event
                for event in resumed_trace_events
                if event.node_name == "checkpoint_resume"
            ]
            self.assertEqual(len(checkpoint_miss_events), 1)
            self.assertEqual(checkpoint_miss_events[0].event_type, "miss")
            self.assertEqual(
                checkpoint_miss_events[0].details["mismatched_resume_fields"],
                ["note_paths"],
            )

    @staticmethod
    def _build_vault_fixture(temp_root: Path) -> Path:
        vault_path = temp_root / "vault"
        vault_path.mkdir()
        (vault_path / "Alpha.md").write_text(
            "# Alpha\n\nBody line.\n",
            encoding="utf-8",
        )
        (vault_path / "Beta.md").write_text(
            "# Beta\n\nReference [[Alpha]] for follow-up context.\n",
            encoding="utf-8",
        )
        return vault_path


if __name__ == "__main__":
    unittest.main()
