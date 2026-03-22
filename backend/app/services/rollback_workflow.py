from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.contracts.workflow import AuditEvent, Proposal, WorkflowAction, WritebackResult
from app.graphs.checkpoint import (
    PersistedGraphCheckpoint,
    WorkflowCheckpointStatus,
    list_graph_checkpoints_for_thread,
    save_graph_checkpoint_record,
)
from app.graphs.state import StewardState
from app.indexing.store import (
    append_audit_log_event,
    connect_sqlite,
    initialize_index_db,
    load_proposal,
)
from app.services.resume_workflow import (
    ResumeWorkflowConflictError,
    ResumeWorkflowNotFoundError,
    ResumeWorkflowValidationError,
)


@dataclass(frozen=True)
class RolledBackWorkflowExecution:
    run_id: str
    thread_id: str
    action_type: WorkflowAction
    proposal: Proposal
    audit_event_id: str
    message: str
    rollback_result: WritebackResult


def rollback_workflow(
    *,
    thread_id: str,
    proposal_id: str,
    rollback_result: WritebackResult,
    settings: Settings,
    run_id: str,
) -> RolledBackWorkflowExecution:
    normalized_db_path = initialize_index_db(settings.index_db_path)
    checkpoints = list_graph_checkpoints_for_thread(
        normalized_db_path,
        thread_id=thread_id,
    )
    if not checkpoints:
        raise ResumeWorkflowNotFoundError(
            f"No persisted workflow checkpoint was found for thread_id={thread_id!r}."
        )

    connection = connect_sqlite(normalized_db_path)
    try:
        persisted_proposal = load_proposal(connection, proposal_id=proposal_id)
        if persisted_proposal is None:
            raise ResumeWorkflowNotFoundError(
                f"No persisted proposal was found for proposal_id={proposal_id!r}."
            )
        if persisted_proposal.thread_id != thread_id:
            raise ResumeWorkflowConflictError(
                "The provided proposal_id does not belong to the supplied thread_id."
            )

        proposal = persisted_proposal.proposal
        matching_checkpoint = _select_matching_checkpoint(
            checkpoints=checkpoints,
            proposal_id=proposal.proposal_id,
        )
        if matching_checkpoint is None:
            raise ResumeWorkflowConflictError(
                "No checkpoint for this thread is currently associated with the supplied proposal_id."
            )
        if matching_checkpoint.checkpoint_status != WorkflowCheckpointStatus.COMPLETED:
            raise ResumeWorkflowConflictError(
                "Only completed workflow checkpoints can accept a rollback record."
            )

        forward_writeback_result = matching_checkpoint.state.get("writeback_result")
        if forward_writeback_result is None or not forward_writeback_result.applied:
            raise ResumeWorkflowConflictError(
                "This workflow thread does not contain a successful writeback result to roll back."
            )

        normalized_rollback_result = _materialize_rollback_result(
            proposal=proposal,
            original_writeback_result=forward_writeback_result,
            rollback_result=rollback_result,
        )

        persisted_rollback_result = matching_checkpoint.state.get("rollback_result")
        if persisted_rollback_result is not None:
            if _is_same_effective_writeback_result(
                persisted_rollback_result,
                normalized_rollback_result,
            ):
                return RolledBackWorkflowExecution(
                    run_id=run_id,
                    thread_id=thread_id,
                    action_type=matching_checkpoint.action_type,
                    proposal=proposal,
                    audit_event_id=(
                        matching_checkpoint.state.get("rollback_audit_event_id")
                        or matching_checkpoint.state.get("audit_event_id")
                    ),
                    message="Workflow rollback was already recorded with the same result.",
                    rollback_result=persisted_rollback_result,
                )
            raise ResumeWorkflowConflictError(
                "This workflow thread already contains a different rollback result."
            )

        audit_event = AuditEvent(
            thread_id=thread_id,
            proposal_id=proposal.proposal_id,
            action_type=matching_checkpoint.action_type,
            target_note_path=proposal.target_note_path,
            approval_required=False,
            approval_decision=None,
            writeback_result=normalized_rollback_result,
            model_info={
                "rollback_protocol": "workflow_rollback_v1",
                "event_kind": "rollback",
                "graph_name": matching_checkpoint.graph_name,
                "checkpoint_id": matching_checkpoint.checkpoint_id,
            },
            retrieved_chunk_ids=[],
        )

        # rollback 失败也要留痕，因为这说明用户已经尝试过“撤销副作用”。
        # 但只有真正成功的 rollback 才写回 completed checkpoint，避免一次失败尝试
        # 把后续合法重试永久锁死。
        with connection:
            append_audit_log_event(
                connection,
                audit_event=audit_event,
                run_id=run_id,
            )
            if normalized_rollback_result.applied:
                save_graph_checkpoint_record(
                    connection,
                    graph_name=matching_checkpoint.graph_name,
                    checkpoint_status=WorkflowCheckpointStatus.COMPLETED,
                    last_completed_node=matching_checkpoint.last_completed_node,
                    next_node_name=None,
                    state=_build_rolled_back_state(
                        checkpoint=matching_checkpoint,
                        run_id=run_id,
                        rollback_result=normalized_rollback_result,
                        audit_event_id=audit_event.audit_event_id,
                    ),
                )

        return RolledBackWorkflowExecution(
            run_id=run_id,
            thread_id=thread_id,
            action_type=matching_checkpoint.action_type,
            proposal=proposal,
            audit_event_id=audit_event.audit_event_id,
            message=_build_rollback_message(normalized_rollback_result),
            rollback_result=normalized_rollback_result,
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


def _materialize_rollback_result(
    *,
    proposal: Proposal,
    original_writeback_result: WritebackResult,
    rollback_result: WritebackResult,
) -> WritebackResult:
    if (
        rollback_result.target_note_path is not None
        and rollback_result.target_note_path != proposal.target_note_path
    ):
        raise ResumeWorkflowValidationError(
            "rollback_result.target_note_path must match proposal.target_note_path."
        )

    if rollback_result.applied:
        if not rollback_result.after_hash:
            raise ResumeWorkflowValidationError(
                "Applied rollback_result entries must include after_hash."
            )
        if rollback_result.error is not None:
            raise ResumeWorkflowValidationError(
                "Applied rollback_result entries must not include error."
            )
        if rollback_result.applied_patch_ops:
            raise ResumeWorkflowValidationError(
                "rollback_result.applied_patch_ops must stay empty for rollback records."
            )
        if (
            original_writeback_result.after_hash is not None
            and rollback_result.before_hash is not None
            and rollback_result.before_hash != original_writeback_result.after_hash
        ):
            raise ResumeWorkflowValidationError(
                "Applied rollback_result.before_hash must match the forward writeback after_hash."
            )
        if (
            original_writeback_result.before_hash is not None
            and rollback_result.after_hash != original_writeback_result.before_hash
        ):
            raise ResumeWorkflowValidationError(
                "Applied rollback_result.after_hash must restore the forward writeback before_hash."
            )
        return rollback_result.model_copy(
            update={
                "target_note_path": proposal.target_note_path,
                "before_hash": (
                    rollback_result.before_hash or original_writeback_result.after_hash
                ),
                "applied_patch_ops": [],
            }
        )

    if rollback_result.after_hash is not None:
        raise ResumeWorkflowValidationError(
            "Failed rollback_result entries must not include after_hash."
        )
    if rollback_result.applied_patch_ops:
        raise ResumeWorkflowValidationError(
            "Failed rollback_result entries must not include applied_patch_ops."
        )
    if not rollback_result.error:
        raise ResumeWorkflowValidationError(
            "Failed rollback_result entries must include error."
        )
    return rollback_result.model_copy(
        update={"target_note_path": proposal.target_note_path}
    )


def _is_same_effective_writeback_result(
    left: WritebackResult,
    right: WritebackResult,
) -> bool:
    return (
        left.applied == right.applied
        and left.target_note_path == right.target_note_path
        and left.before_hash == right.before_hash
        and left.after_hash == right.after_hash
        and left.error == right.error
        and [patch.model_dump(mode="json") for patch in left.applied_patch_ops] == [
            patch.model_dump(mode="json") for patch in right.applied_patch_ops
        ]
    )


def _build_rolled_back_state(
    *,
    checkpoint: PersistedGraphCheckpoint,
    run_id: str,
    rollback_result: WritebackResult,
    audit_event_id: str,
) -> StewardState:
    rolled_back_state = dict(checkpoint.state)
    rolled_back_state["thread_id"] = checkpoint.thread_id
    rolled_back_state["run_id"] = run_id
    rolled_back_state["action_type"] = checkpoint.action_type
    rolled_back_state["rollback_result"] = rollback_result
    rolled_back_state["rollback_audit_event_id"] = audit_event_id
    rolled_back_state["trace_events"] = []
    rolled_back_state["transient_prompt_context"] = {}
    return rolled_back_state


def _build_rollback_message(rollback_result: WritebackResult) -> str:
    if rollback_result.applied:
        return (
            "Workflow rollback recorded a successful local rollback result."
        )
    return (
        "Workflow rollback recorded a failed local rollback result. "
        "No content was reverted."
    )
