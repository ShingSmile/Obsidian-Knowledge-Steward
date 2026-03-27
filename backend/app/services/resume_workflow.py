from __future__ import annotations

from dataclasses import dataclass
import json

from app.config import Settings
from app.contracts.workflow import (
    ApprovalDecision,
    AuditEvent,
    IngestWorkflowResult,
    PatchOp,
    PostWritebackSyncResult,
    Proposal,
    WorkflowAction,
    WorkflowResumeRequest,
    WritebackResult,
)
from app.graphs.checkpoint import (
    PersistedGraphCheckpoint,
    WorkflowCheckpointStatus,
    list_graph_checkpoints_for_thread,
    save_graph_checkpoint_record,
)
from app.graphs.state import StewardState
from app.indexing.ingest import ingest_vault
from app.indexing.store import (
    append_audit_log_event,
    connect_sqlite,
    initialize_index_db,
    load_proposal,
)
from app.services.proposal_validation import (
    ProposalValidationError,
    validate_proposal_for_persistence,
)


class ResumeWorkflowError(ValueError):
    """Base error for workflow resume validation failures."""


class ResumeWorkflowValidationError(ResumeWorkflowError):
    """The caller payload is malformed for the current workflow state."""


class ResumeWorkflowNotFoundError(ResumeWorkflowError):
    """The requested thread/proposal state cannot be found."""


class ResumeWorkflowConflictError(ResumeWorkflowError):
    """The stored workflow state conflicts with the requested resume action."""


@dataclass(frozen=True)
class ResumedWorkflowExecution:
    run_id: str
    thread_id: str
    action_type: WorkflowAction
    proposal: Proposal
    approval_decision: ApprovalDecision
    audit_event_id: str | None
    message: str
    writeback_result: WritebackResult | None
    post_writeback_sync: PostWritebackSyncResult | None


def resume_workflow(
    request: WorkflowResumeRequest,
    *,
    settings: Settings,
    run_id: str,
) -> ResumedWorkflowExecution:
    normalized_db_path = initialize_index_db(settings.index_db_path)
    checkpoints = list_graph_checkpoints_for_thread(
        normalized_db_path,
        thread_id=request.thread_id,
    )
    if not checkpoints:
        raise ResumeWorkflowNotFoundError(
            f"No persisted workflow checkpoint was found for thread_id={request.thread_id!r}."
        )

    connection = connect_sqlite(normalized_db_path)
    try:
        persisted_proposal = load_proposal(connection, proposal_id=request.proposal_id)
        if persisted_proposal is None:
            raise ResumeWorkflowNotFoundError(
                f"No persisted proposal was found for proposal_id={request.proposal_id!r}."
            )
        try:
            validate_proposal_for_persistence(
                persisted_proposal.proposal,
                settings=settings,
            )
        except ProposalValidationError as exc:
            raise ResumeWorkflowValidationError(str(exc)) from exc
        if persisted_proposal.thread_id != request.thread_id:
            raise ResumeWorkflowConflictError(
                "The provided proposal_id does not belong to the supplied thread_id."
            )

        proposal = persisted_proposal.proposal
        approval_decision = _materialize_approval_decision(
            proposal=proposal,
            approval_decision=request.approval_decision,
        )
        writeback_result = _materialize_writeback_result(
            proposal=proposal,
            approval_decision=approval_decision,
            writeback_result=request.writeback_result,
        )
        matching_checkpoint = _select_matching_checkpoint(
            checkpoints=checkpoints,
            proposal_id=proposal.proposal_id,
        )
        if matching_checkpoint is None:
            raise ResumeWorkflowConflictError(
                "No checkpoint for this thread is currently associated with the supplied proposal_id."
            )

        if matching_checkpoint.checkpoint_status == WorkflowCheckpointStatus.COMPLETED:
            checkpoint_decision = matching_checkpoint.state.get("approval_decision")
            if checkpoint_decision is None:
                raise ResumeWorkflowConflictError(
                    "The checkpoint is already marked completed, but it does not contain an approval decision."
                )
            if not _is_same_effective_decision(
                checkpoint_decision,
                approval_decision,
            ):
                raise ResumeWorkflowConflictError(
                    "This workflow thread was already resumed with a different approval decision."
                )
            checkpoint_writeback_result = matching_checkpoint.state.get("writeback_result")
            if (
                writeback_result is not None
                and not _is_same_effective_writeback_result(
                    checkpoint_writeback_result,
                    writeback_result,
                )
            ):
                raise ResumeWorkflowConflictError(
                    "This workflow thread was already resumed with a different writeback result."
                )

            return ResumedWorkflowExecution(
                run_id=run_id,
                thread_id=request.thread_id,
                action_type=matching_checkpoint.action_type,
                proposal=proposal,
                approval_decision=checkpoint_decision,
                audit_event_id=matching_checkpoint.state.get("audit_event_id"),
                message="Workflow resume was already resolved with the same approval decision.",
                writeback_result=checkpoint_writeback_result,
                post_writeback_sync=matching_checkpoint.state.get("post_writeback_sync"),
            )

        if matching_checkpoint.checkpoint_status != WorkflowCheckpointStatus.WAITING_FOR_APPROVAL:
            raise ResumeWorkflowConflictError(
                "The matched workflow checkpoint is not waiting for approval and cannot be resumed."
            )

        audit_event = AuditEvent(
            thread_id=request.thread_id,
            proposal_id=proposal.proposal_id,
            action_type=matching_checkpoint.action_type,
            target_note_path=proposal.target_note_path,
            approval_required=True,
            approval_decision=approval_decision,
            writeback_result=writeback_result,
            model_info={
                "resume_protocol": "workflow_resume_v1",
                "graph_name": matching_checkpoint.graph_name,
                "checkpoint_id": matching_checkpoint.checkpoint_id,
            },
            retrieved_chunk_ids=[
                evidence.chunk_id
                for evidence in proposal.evidence
                if evidence.chunk_id is not None
            ],
        )
        post_writeback_sync = _run_post_writeback_sync(
            proposal=proposal,
            writeback_result=writeback_result,
            settings=settings,
        )

        resumed_state = _build_resumed_state(
            checkpoint=matching_checkpoint,
            run_id=run_id,
            proposal=proposal,
            approval_decision=approval_decision,
            audit_event_id=audit_event.audit_event_id,
            writeback_result=writeback_result,
            post_writeback_sync=post_writeback_sync,
        )

        # 审批恢复至少要同时推进两件事：写入 append-only audit 事实、把 thread 级 checkpoint
        # 从 waiting 改成 completed。两者落在同一个 SQLite 事务里，避免“审计写了但线程还在等待”
        # 或“线程完成了但审计没留下”的分叉状态。
        with connection:
            append_audit_log_event(
                connection,
                audit_event=audit_event,
                run_id=run_id,
            )
            save_graph_checkpoint_record(
                connection,
                graph_name=matching_checkpoint.graph_name,
                checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
                last_completed_node=matching_checkpoint.last_completed_node,
                next_node_name=None,
                state=resumed_state,
            )

        return ResumedWorkflowExecution(
            run_id=run_id,
            thread_id=request.thread_id,
            action_type=matching_checkpoint.action_type,
            proposal=proposal,
            approval_decision=approval_decision,
            audit_event_id=audit_event.audit_event_id,
            message=_build_resume_message(
                approval_decision,
                writeback_result=writeback_result,
                post_writeback_sync=post_writeback_sync,
            ),
            writeback_result=writeback_result,
            post_writeback_sync=post_writeback_sync,
        )
    finally:
        connection.close()


def _select_matching_checkpoint(
    *,
    checkpoints: list[PersistedGraphCheckpoint],
    proposal_id: str,
) -> PersistedGraphCheckpoint | None:
    for checkpoint in checkpoints:
        checkpoint_proposal = checkpoint.state.get("proposal")
        if checkpoint_proposal is None:
            continue
        if checkpoint_proposal.proposal_id == proposal_id:
            return checkpoint
    return None


def _materialize_approval_decision(
    *,
    proposal: Proposal,
    approval_decision: ApprovalDecision,
) -> ApprovalDecision:
    if not approval_decision.approved:
        if approval_decision.approved_patch_ops:
            raise ResumeWorkflowValidationError(
                "Rejected approval decisions must not include approved_patch_ops."
            )
        return approval_decision.model_copy(update={"approved_patch_ops": []})

    if not approval_decision.approved_patch_ops:
        return approval_decision.model_copy(update={"approved_patch_ops": proposal.patch_ops})

    if not _patch_ops_match(
        approval_decision.approved_patch_ops,
        proposal.patch_ops,
    ):
        raise ResumeWorkflowValidationError(
            "Partial patch approval is not supported yet; approved_patch_ops must be empty or match the full proposal."
        )
    return approval_decision


def _patch_ops_match(left: list[PatchOp], right: list[PatchOp]) -> bool:
    return [_patch_signature(patch_op) for patch_op in left] == [
        _patch_signature(patch_op) for patch_op in right
    ]


def _patch_signature(patch_op: PatchOp) -> str:
    return json.dumps(
        patch_op.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
    )


def _materialize_writeback_result(
    *,
    proposal: Proposal,
    approval_decision: ApprovalDecision,
    writeback_result: WritebackResult | None,
) -> WritebackResult | None:
    if not approval_decision.approved:
        if writeback_result is not None:
            raise ResumeWorkflowValidationError(
                "Rejected approval decisions must not include writeback_result."
            )
        return None

    if writeback_result is None:
        return None

    if (
        writeback_result.target_note_path is not None
        and writeback_result.target_note_path != proposal.target_note_path
    ):
        raise ResumeWorkflowValidationError(
            "writeback_result.target_note_path must match proposal.target_note_path."
        )

    if writeback_result.applied:
        if not writeback_result.after_hash:
            raise ResumeWorkflowValidationError(
                "Applied writeback_result entries must include after_hash."
            )
        if writeback_result.error is not None:
            raise ResumeWorkflowValidationError(
                "Applied writeback_result entries must not include error."
            )
        if not _patch_ops_match(
            writeback_result.applied_patch_ops,
            approval_decision.approved_patch_ops,
        ):
            raise ResumeWorkflowValidationError(
                "Applied writeback_result.applied_patch_ops must match the approved patch set."
            )
        expected_before_hash = proposal.safety_checks.before_hash
        if (
            expected_before_hash is not None
            and writeback_result.before_hash is not None
            and writeback_result.before_hash != expected_before_hash
        ):
            raise ResumeWorkflowValidationError(
                "Applied writeback_result.before_hash must match proposal.safety_checks.before_hash."
            )
        return writeback_result.model_copy(
            update={
                "target_note_path": proposal.target_note_path,
                "before_hash": writeback_result.before_hash or expected_before_hash,
            }
        )

    if writeback_result.applied_patch_ops:
        raise ResumeWorkflowValidationError(
            "Failed writeback_result entries must not include applied_patch_ops."
        )
    if writeback_result.after_hash is not None:
        raise ResumeWorkflowValidationError(
            "Failed writeback_result entries must not include after_hash."
        )
    if not writeback_result.error:
        raise ResumeWorkflowValidationError(
            "Failed writeback_result entries must include error."
        )
    return writeback_result.model_copy(
        update={"target_note_path": proposal.target_note_path}
    )


def _is_same_effective_decision(
    left: ApprovalDecision,
    right: ApprovalDecision,
) -> bool:
    return (
        left.approved == right.approved
        and left.reviewer == right.reviewer
        and left.comment == right.comment
        and _patch_ops_match(left.approved_patch_ops, right.approved_patch_ops)
    )


def _is_same_effective_writeback_result(
    left: WritebackResult | None,
    right: WritebackResult,
) -> bool:
    if left is None:
        return False
    return (
        left.applied == right.applied
        and left.target_note_path == right.target_note_path
        and left.before_hash == right.before_hash
        and left.after_hash == right.after_hash
        and left.error == right.error
        and _patch_ops_match(left.applied_patch_ops, right.applied_patch_ops)
    )


def _build_resumed_state(
    *,
    checkpoint: PersistedGraphCheckpoint,
    run_id: str,
    proposal: Proposal,
    approval_decision: ApprovalDecision,
    audit_event_id: str,
    writeback_result: WritebackResult | None,
    post_writeback_sync: PostWritebackSyncResult | None,
) -> StewardState:
    resumed_state = dict(checkpoint.state)
    resumed_state["thread_id"] = checkpoint.thread_id
    resumed_state["run_id"] = run_id
    resumed_state["action_type"] = checkpoint.action_type
    resumed_state["proposal"] = proposal
    resumed_state["approval_required"] = False
    resumed_state["approval_decision"] = approval_decision
    resumed_state["audit_event_id"] = audit_event_id
    resumed_state["trace_events"] = []
    resumed_state["transient_prompt_context"] = {}
    # 这里显式把 patch_plan 收敛到“本次审批真正放行的 patch”。
    # 当前任务不支持 partial apply，因此 approve 要么放行全量 patch，要么 reject 后清空。
    resumed_state["patch_plan"] = [
        patch_op.model_dump(mode="json")
        for patch_op in approval_decision.approved_patch_ops
    ]
    resumed_state["writeback_result"] = writeback_result
    resumed_state["post_writeback_sync"] = post_writeback_sync
    return resumed_state


def _build_resume_message(
    approval_decision: ApprovalDecision,
    *,
    writeback_result: WritebackResult | None,
    post_writeback_sync: PostWritebackSyncResult | None,
) -> str:
    if approval_decision.approved:
        if writeback_result is None:
            return (
                "Workflow resume recorded approval. "
                "Writeback execution is still out of scope for the current phase."
            )
        if writeback_result.applied:
            if post_writeback_sync is None:
                return (
                    "Workflow resume recorded approval and persisted a successful writeback result."
                )
            return post_writeback_sync.message
        return (
            "Workflow resume recorded approval, but the plugin reported a failed writeback result."
        )
    return "Workflow resume recorded rejection. No writeback was executed."


def _run_post_writeback_sync(
    *,
    proposal: Proposal,
    writeback_result: WritebackResult | None,
    settings: Settings,
) -> PostWritebackSyncResult | None:
    if writeback_result is None or not writeback_result.applied:
        return None

    try:
        # 写回成功后立刻复用现有 scoped ingest，只刷新 proposal 指向的那篇 note。
        # 这里故意不重新走第二条 approval/workflow 协议，避免把“索引刷新”扩成新的中等任务。
        stats = ingest_vault(
            vault_path=settings.sample_vault_dir,
            db_path=settings.index_db_path,
            note_path=proposal.target_note_path,
            settings=settings,
        )
    except Exception as exc:
        error_message = str(exc)
        return PostWritebackSyncResult(
            succeeded=False,
            target_note_path=proposal.target_note_path,
            message=(
                "Workflow resume recorded approval and persisted a successful writeback result, "
                f"but scoped ingest refresh failed: {error_message}"
            ),
            ingest_result=None,
            error=error_message,
        )

    return PostWritebackSyncResult(
        succeeded=True,
        target_note_path=proposal.target_note_path,
        message=(
            "Workflow resume recorded approval, persisted a successful writeback result, "
            "and refreshed the target note via scoped ingest."
        ),
        ingest_result=IngestWorkflowResult(
            vault_path=stats.vault_path,
            db_path=stats.db_path,
            scanned_notes=stats.scanned_notes,
            created_notes=stats.created_notes,
            updated_notes=stats.updated_notes,
            current_chunk_count=stats.current_chunk_count,
            replaced_chunk_count=stats.replaced_chunk_count,
        ),
        error=None,
    )
