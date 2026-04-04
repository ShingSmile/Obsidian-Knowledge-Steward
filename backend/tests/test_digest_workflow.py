from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException, Response

from app.config import get_settings
from app.contracts.workflow import (
    PatchOp,
    Proposal,
    RiskLevel,
    RuntimeFaithfulnessOutcome,
    RunStatus,
    SafetyChecks,
    WorkflowAction,
    WorkflowInvokeRequest,
)
from app.graphs.checkpoint import WorkflowCheckpointStatus, load_graph_checkpoint
from app.graphs.digest_graph import invoke_digest_graph
from app.indexing.ingest import ingest_vault
from app.indexing.store import connect_sqlite, load_proposal
from app.main import invoke_workflow, list_pending_approvals_endpoint
from app.observability.runtime_trace import query_run_trace_events_in_db
from app.services.digest import run_minimal_digest


class DigestWorkflowTests(unittest.TestCase):
    def test_run_minimal_digest_records_context_bundle_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            )

            result = run_minimal_digest(settings=settings)

            self.assertGreaterEqual(result.context_bundle_summary["evidence_count"], 1)

    def test_run_minimal_digest_marks_low_confidence_for_overclaim_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            )

            with patch(
                "app.services.digest._build_digest_markdown",
                return_value="DAILY_DIGEST 已自动写回知识库并完成审批。",
            ):
                result = run_minimal_digest(settings=settings)

            self.assertIsNotNone(result.runtime_faithfulness)
            self.assertEqual(
                result.runtime_faithfulness.outcome,
                RuntimeFaithfulnessOutcome.LOW_CONFIDENCE,
            )
            self.assertEqual(result.runtime_faithfulness.threshold, 0.67)

    def test_invoke_digest_graph_returns_structured_digest_and_trace_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
                ask_runtime_trace_path=trace_path,
            )
            trace_events: list[dict[str, object]] = []

            execution = invoke_digest_graph(
                WorkflowInvokeRequest(
                    thread_id="thread_digest_graph",
                    action_type=WorkflowAction.DAILY_DIGEST,
                ),
                settings=settings,
                thread_id="thread_digest_graph",
                run_id="run_digest_graph",
                trace_hook=trace_events.append,
            )

            self.assertEqual(execution.thread_id, "thread_digest_graph")
            self.assertEqual(execution.run_id, "run_digest_graph")
            self.assertEqual(execution.graph_name, "digest_graph")
            self.assertEqual(execution.action_type, WorkflowAction.DAILY_DIGEST)
            self.assertEqual(execution.state["thread_id"], "thread_digest_graph")
            self.assertEqual(execution.state["run_id"], "run_digest_graph")
            self.assertEqual(execution.digest_result.source_note_count, 3)
            self.assertFalse(execution.digest_result.fallback_used)
            self.assertFalse(hasattr(execution, "used_langgraph"))
            self.assertIn("本次 DAILY_DIGEST 基于最近 3 篇已索引笔记生成。", execution.digest_result.digest_markdown)
            self.assertIn("重点来源", execution.digest_result.digest_markdown)
            self.assertIsNotNone(execution.digest_result.runtime_faithfulness)
            self.assertEqual(len(execution.trace_events), 3)
            self.assertEqual(
                [event["node_name"] for event in execution.trace_events],
                ["prepare_digest", "build_digest", "finalize_digest"],
            )
            self.assertEqual(len(trace_events), 3)
            build_event = next(
                event for event in execution.trace_events if event["node_name"] == "build_digest"
            )
            self.assertIn("runtime_faithfulness_outcome", build_event["details"])
            self.assertIn("runtime_faithfulness_score", build_event["details"])
            self.assertIn("runtime_faithfulness_threshold", build_event["details"])

            persisted_events = [
                json.loads(line)
                for line in trace_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(persisted_events), 3)
            self.assertTrue(all(event["graph_name"] == "digest_graph" for event in persisted_events))

    def test_invoke_digest_graph_persists_langgraph_sqlite_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
            )

            execution = invoke_digest_graph(
                WorkflowInvokeRequest(
                    thread_id="thread_sqlitesaver_digest",
                    action_type=WorkflowAction.DAILY_DIGEST,
                ),
                settings=settings,
                thread_id="thread_sqlitesaver_digest",
                run_id="run_sqlitesaver_digest",
            )

            connection = sqlite3.connect(db_path)
            try:
                checkpoint_rows = connection.execute(
                    """
                    SELECT thread_id, checkpoint_ns, checkpoint_id
                    FROM checkpoints
                    WHERE thread_id = ?
                    ORDER BY checkpoint_id ASC
                    """,
                    ("thread_sqlitesaver_digest",),
                ).fetchall()
            finally:
                connection.close()

            self.assertEqual(execution.digest_result.source_note_count, 3)
            self.assertGreaterEqual(len(checkpoint_rows), 1)

    def test_invoke_workflow_returns_safe_fallback_when_index_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            response = Response()

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_empty_digest",
                        action_type=WorkflowAction.DAILY_DIGEST,
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertEqual(result.thread_id, "thread_empty_digest")
            self.assertEqual(result.message, "Digest workflow completed with safe fallback.")
            self.assertIsNotNone(result.digest_result)
            self.assertEqual(result.digest_result.source_note_count, 0)
            self.assertTrue(result.digest_result.fallback_used)
            self.assertEqual(result.digest_result.fallback_reason, "no_indexed_notes")

            run_trace_events = query_run_trace_events_in_db(db_path, run_id=result.run_id)
            self.assertEqual(len(run_trace_events), 3)
            self.assertTrue(all(event.graph_name == "digest_graph" for event in run_trace_events))

    def test_invoke_workflow_returns_waiting_proposal_for_digest_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            ingest_vault(vault_path=vault_path, db_path=db_path)

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
                        thread_id="thread_digest_waiting",
                        action_type=WorkflowAction.DAILY_DIGEST,
                        require_approval=True,
                        metadata={
                            "trigger": "test_digest_waiting",
                            "approval_mode": "proposal",
                        },
                    ),
                    response,
                )

            self.assertEqual(response.status_code, 202)
            self.assertEqual(result.status, RunStatus.WAITING_FOR_APPROVAL)
            self.assertTrue(result.approval_required)
            self.assertIsNotNone(result.proposal)
            self.assertIsNotNone(result.digest_result)
            self.assertEqual(result.proposal.target_note_path, "2026-03-14.md")

            checkpoint = load_graph_checkpoint(
                db_path,
                thread_id="thread_digest_waiting",
                graph_name="digest_graph",
            )
            self.assertIsNotNone(checkpoint)
            self.assertEqual(
                checkpoint.checkpoint_status,
                WorkflowCheckpointStatus.WAITING_FOR_APPROVAL,
            )
            self.assertEqual(checkpoint.last_completed_node, "build_digest_proposal")
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
            self.assertEqual(persisted_proposal.thread_id, "thread_digest_waiting")
            self.assertEqual(len(persisted_proposal.proposal.patch_ops), 2)

            run_trace_events = query_run_trace_events_in_db(
                db_path,
                run_id=result.run_id,
            )
            self.assertEqual(
                [event.node_name for event in run_trace_events],
                ["prepare_digest", "build_digest", "build_digest_proposal", "human_approval"],
            )
            self.assertEqual(run_trace_events[-1].event_type, "waiting")

    def test_invoke_workflow_rejects_out_of_vault_digest_patch_target_before_persist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            bad_proposal = Proposal(
                proposal_id="prop_digest_out_of_vault_target",
                action_type=WorkflowAction.DAILY_DIGEST,
                target_note_path=str((vault_path / "2026-03-14.md").resolve()),
                summary="Reject a waiting digest proposal with an out-of-vault patch target.",
                risk_level=RiskLevel.MEDIUM,
                patch_ops=[
                    PatchOp(
                        op="merge_frontmatter",
                        target_path=str((temp_root / "outside" / "digest-note.md").resolve()),
                        payload={"ks_pending_digest_review": True},
                    ),
                    PatchOp(
                        op="insert_under_heading",
                        target_path=str((vault_path / "2026-03-14.md").resolve()),
                        payload={
                            "heading": "## Knowledge Steward Digest",
                            "content": "Digest body that should never be persisted.",
                        },
                    ),
                ],
                safety_checks=SafetyChecks(
                    before_hash="sha256:before",
                    max_changed_lines=12,
                    contains_delete=False,
                ),
            )

            with patch(
                "app.graphs.digest_graph.build_digest_approval_proposal",
                return_value=bad_proposal,
            ):
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
                                thread_id="thread_digest_out_of_vault_target",
                                action_type=WorkflowAction.DAILY_DIGEST,
                                require_approval=True,
                                metadata={"approval_mode": "proposal"},
                            ),
                            Response(),
                        )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("within the configured vault", context.exception.detail)

            connection = connect_sqlite(db_path)
            try:
                self.assertIsNone(
                    load_proposal(connection, proposal_id=bad_proposal.proposal_id)
                )
            finally:
                connection.close()

            self.assertIsNone(
                load_graph_checkpoint(
                    db_path,
                    thread_id="thread_digest_out_of_vault_target",
                    graph_name="digest_graph",
                )
            )

    def test_pending_approvals_endpoint_lists_waiting_digest_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            ingest_vault(vault_path=vault_path, db_path=db_path)

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
                        thread_id="thread_digest_inbox",
                        action_type=WorkflowAction.DAILY_DIGEST,
                        require_approval=True,
                        metadata={"approval_mode": "proposal"},
                    ),
                    Response(),
                )
                pending_response = list_pending_approvals_endpoint()

            self.assertEqual(len(pending_response.items), 1)
            pending_item = pending_response.items[0]
            self.assertEqual(pending_item.thread_id, "thread_digest_inbox")
            self.assertEqual(pending_item.proposal_id, result.proposal.proposal_id)
            self.assertEqual(pending_item.proposal.proposal_id, result.proposal.proposal_id)
            self.assertEqual(
                pending_item.target_note_path,
                result.proposal.target_note_path,
            )
            self.assertEqual(
                pending_item.summary,
                result.proposal.summary,
            )

    def test_invoke_workflow_returns_empty_approval_message_when_digest_proposal_cannot_be_built(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            response = Response()

            with patch(
                "app.main.settings",
                replace(
                    get_settings(),
                    index_db_path=db_path,
                    ask_runtime_trace_path=trace_path,
                ),
            ):
                result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_digest_waiting_empty",
                        action_type=WorkflowAction.DAILY_DIGEST,
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
                "Digest workflow completed with safe fallback; no approval proposal was generated.",
            )

    def test_invoke_workflow_resumes_completed_digest_from_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            ingest_vault(vault_path=vault_path, db_path=db_path)
            settings = replace(
                get_settings(),
                sample_vault_dir=vault_path,
                index_db_path=db_path,
                ask_runtime_trace_path=trace_path,
            )

            with patch("app.main.settings", settings):
                first_result = invoke_workflow(
                    WorkflowInvokeRequest(
                        thread_id="thread_resume_digest",
                        action_type=WorkflowAction.DAILY_DIGEST,
                    ),
                    Response(),
                )

                with patch(
                    "app.graphs.digest_graph.run_minimal_digest",
                    side_effect=AssertionError("resume should not rebuild digest"),
                ):
                    resumed_response = Response()
                    with self.assertNoLogs(
                        "langgraph.checkpoint.serde.jsonplus",
                        level="WARNING",
                    ):
                        resumed_result = invoke_workflow(
                            WorkflowInvokeRequest(
                                thread_id="thread_resume_digest",
                                action_type=WorkflowAction.DAILY_DIGEST,
                                resume_from_checkpoint=True,
                            ),
                            resumed_response,
                        )

            self.assertEqual(resumed_response.status_code, 200)
            self.assertEqual(resumed_result.message, "Digest workflow resumed from checkpoint.")
            self.assertEqual(resumed_result.thread_id, "thread_resume_digest")
            self.assertNotEqual(resumed_result.run_id, first_result.run_id)
            self.assertIsNotNone(resumed_result.digest_result)
            self.assertEqual(resumed_result.digest_result.source_note_count, 3)

            resumed_trace_events = query_run_trace_events_in_db(
                db_path,
                run_id=resumed_result.run_id,
            )
            self.assertEqual(len(resumed_trace_events), 1)
            self.assertEqual(resumed_trace_events[0].node_name, "checkpoint_resume")
            self.assertEqual(resumed_trace_events[0].event_type, "hit")

    def test_invoke_workflow_rejects_resume_from_checkpoint_for_waiting_digest_thread(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
            db_path = temp_root / "knowledge_steward.sqlite3"
            trace_path = temp_root / "traces" / "runtime.jsonl"
            ingest_vault(vault_path=vault_path, db_path=db_path)

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
                        thread_id="thread_digest_waiting_resume",
                        action_type=WorkflowAction.DAILY_DIGEST,
                        require_approval=True,
                        metadata={"approval_mode": "proposal"},
                    ),
                    Response(),
                )

                with self.assertRaises(HTTPException) as context:
                    invoke_workflow(
                        WorkflowInvokeRequest(
                            thread_id="thread_digest_waiting_resume",
                            action_type=WorkflowAction.DAILY_DIGEST,
                            resume_from_checkpoint=True,
                        ),
                        Response(),
                    )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("waiting for approval", context.exception.detail)

    def test_invoke_workflow_rejects_scoped_digest_request_until_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            vault_path = self._build_digest_vault_fixture(temp_root)
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
                with self.assertRaises(HTTPException) as context:
                    invoke_workflow(
                        WorkflowInvokeRequest(
                            action_type=WorkflowAction.DAILY_DIGEST,
                            note_path=str(vault_path / "2026-03-14.md"),
                        ),
                        Response(),
                    )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("summarizes the indexed vault as a whole", context.exception.detail)

    @staticmethod
    def _build_digest_vault_fixture(temp_root: Path) -> Path:
        vault_path = temp_root / "vault"
        vault_path.mkdir()
        (vault_path / "2026-03-14.md").write_text(
            "# 一、工作任务\n- [ ] 完成 digest graph\n\n# 四、今日总结\n今天接通了 DAILY_DIGEST。\n",
            encoding="utf-8",
        )
        (vault_path / "2026-03-13.md").write_text(
            "# Task Planner\n- [ ] Review retrieval\n\n# Summary\nClosed the ask checkpoint task.\n",
            encoding="utf-8",
        )
        (vault_path / "迭代总结.md").write_text(
            "# 迭代总结\n\n本周主要完成 ask_graph 与 ingest_graph。\n",
            encoding="utf-8",
        )
        return vault_path


if __name__ == "__main__":
    unittest.main()
