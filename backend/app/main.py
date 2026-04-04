from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import get_settings
from app.contracts.workflow import (
    AskResultMode,
    HealthResponse,
    ModelProviderDescriptor,
    PendingApprovalItem,
    RunStatus,
    SampleVaultStats,
    WorkflowAction,
    WorkflowInvokeRequest,
    WorkflowInvokeResponse,
    WorkflowPendingApprovalsResponse,
    WorkflowRollbackRequest,
    WorkflowRollbackResponse,
    WorkflowResumeRequest,
    WorkflowResumeResponse,
)
from app.graphs.ask_graph import AskGraphExecution, invoke_ask_graph
from app.graphs.digest_graph import DigestGraphExecution, invoke_digest_graph
from app.graphs.ingest_graph import IngestGraphExecution, invoke_ingest_graph
from app.indexing.store import connect_sqlite, initialize_index_db, list_pending_approval_records
from app.services.resume_workflow import (
    ResumeWorkflowConflictError,
    ResumeWorkflowNotFoundError,
    ResumeWorkflowValidationError,
    resume_workflow,
)
from app.services.rollback_workflow import rollback_workflow
from app.services.sample_vault import describe_sample_vault


settings = get_settings()
app = FastAPI(
    title="Knowledge Steward Backend",
    version=settings.version,
    summary="Backend baseline for Obsidian Knowledge Steward",
)
app.add_middleware(
    CORSMiddleware,
    # Obsidian desktop plugins run in an Electron/webview origin and may issue
    # browser-style preflight requests to the local backend. This backend does
    # not rely on browser cookies, so permissive local cross-origin access keeps
    # the plugin transport usable without coupling it to a single origin shape.
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def build_provider_descriptors() -> list[ModelProviderDescriptor]:
    return [
        ModelProviderDescriptor(
            name=settings.cloud_provider_name,
            priority=1,
            enabled=bool(
                settings.cloud_base_url
                and (settings.cloud_chat_model or settings.cloud_embedding_model)
            ),
            purpose="primary",
            base_url=settings.cloud_base_url or None,
            chat_model=settings.cloud_chat_model or None,
            embedding_model=settings.cloud_embedding_model or None,
        ),
        ModelProviderDescriptor(
            name=settings.local_provider_name,
            priority=2,
            enabled=bool(
                settings.local_base_url
                and (settings.local_chat_model or settings.local_embedding_model)
            ),
            purpose="fallback_or_baseline",
            base_url=settings.local_base_url or None,
            chat_model=settings.local_chat_model or None,
            embedding_model=settings.local_embedding_model or None,
        ),
    ]


def get_sample_vault_stats() -> SampleVaultStats:
    if not settings.sample_vault_dir.exists():
        return SampleVaultStats(
            path=str(settings.sample_vault_dir),
            note_count=0,
            frontmatter_note_count=0,
            wikilink_count=0,
            task_checkbox_count=0,
            template_family_counts={},
        )
    return describe_sample_vault(settings.sample_vault_dir)


SupportedWorkflowExecution = AskGraphExecution | IngestGraphExecution | DigestGraphExecution
WorkflowInvoker = Callable[[WorkflowInvokeRequest, str, str], SupportedWorkflowExecution]
WorkflowOutcomeBuilder = Callable[
    [WorkflowInvokeRequest, SupportedWorkflowExecution],
    "WorkflowInvokeOutcome",
]


@dataclass(frozen=True)
class WorkflowInvokeOutcome:
    http_status_code: int
    status: RunStatus
    message: str
    approval_required: bool = False
    response_fields: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowInvokeHandler:
    invoke: WorkflowInvoker
    build_outcome: WorkflowOutcomeBuilder


def _invoke_ask_execution(
    request: WorkflowInvokeRequest,
    thread_id: str,
    run_id: str,
) -> AskGraphExecution:
    return invoke_ask_graph(
        request,
        settings=settings,
        thread_id=thread_id,
        run_id=run_id,
    )


def _invoke_ingest_execution(
    request: WorkflowInvokeRequest,
    thread_id: str,
    run_id: str,
) -> IngestGraphExecution:
    return invoke_ingest_graph(
        request,
        settings=settings,
        thread_id=thread_id,
        run_id=run_id,
    )


def _invoke_digest_execution(
    request: WorkflowInvokeRequest,
    thread_id: str,
    run_id: str,
) -> DigestGraphExecution:
    return invoke_digest_graph(
        request,
        settings=settings,
        thread_id=thread_id,
        run_id=run_id,
    )


def _approval_proposal_requested(request: WorkflowInvokeRequest) -> bool:
    return request.metadata.get("approval_mode") == "proposal"


def _build_ask_outcome(
    request: WorkflowInvokeRequest,
    execution: SupportedWorkflowExecution,
) -> WorkflowInvokeOutcome:
    ask_execution = execution
    assert isinstance(ask_execution, AskGraphExecution)
    ask_result = ask_execution.ask_result
    if ask_execution.checkpoint_used:
        message = "Ask workflow resumed from checkpoint."
    elif ask_result.mode == AskResultMode.GENERATED_ANSWER:
        message = "Ask workflow completed with a grounded answer."
    elif ask_result.mode == AskResultMode.RETRIEVAL_ONLY:
        message = "Ask workflow completed with retrieval-only fallback."
    else:
        message = "Ask workflow completed without matching evidence."

    return WorkflowInvokeOutcome(
        http_status_code=200,
        status=RunStatus.COMPLETED,
        message=message,
        response_fields={"ask_result": ask_result},
    )


def _build_ingest_outcome(
    request: WorkflowInvokeRequest,
    execution: SupportedWorkflowExecution,
) -> WorkflowInvokeOutcome:
    ingest_execution = execution
    assert isinstance(ingest_execution, IngestGraphExecution)
    approval_proposal_requested = _approval_proposal_requested(request)

    if ingest_execution.approval_required and ingest_execution.proposal is not None:
        return WorkflowInvokeOutcome(
            http_status_code=202,
            status=RunStatus.WAITING_FOR_APPROVAL,
            message="Ingest workflow generated a proposal and is waiting for approval.",
            approval_required=True,
            response_fields={
                "proposal": ingest_execution.proposal,
                "ingest_result": ingest_execution.ingest_result,
                "analysis_result": ingest_execution.analysis_result,
            },
        )

    if ingest_execution.checkpoint_used:
        message = "Ingest workflow resumed from checkpoint."
    elif approval_proposal_requested:
        if request.note_path or request.note_paths:
            message = "Ingest workflow completed with scoped note sync; no approval proposal was generated."
        else:
            message = "Ingest workflow completed with full-vault sync; no approval proposal was generated."
    elif request.note_path or request.note_paths:
        message = "Ingest workflow completed with scoped note sync."
    else:
        message = "Ingest workflow completed with full-vault sync."

    return WorkflowInvokeOutcome(
        http_status_code=200,
        status=RunStatus.COMPLETED,
        message=message,
        response_fields={
            "proposal": ingest_execution.proposal,
            "ingest_result": ingest_execution.ingest_result,
            "analysis_result": ingest_execution.analysis_result,
        },
    )


def _build_digest_outcome(
    request: WorkflowInvokeRequest,
    execution: SupportedWorkflowExecution,
) -> WorkflowInvokeOutcome:
    digest_execution = execution
    assert isinstance(digest_execution, DigestGraphExecution)
    approval_proposal_requested = _approval_proposal_requested(request)

    if digest_execution.approval_required and digest_execution.proposal is not None:
        return WorkflowInvokeOutcome(
            http_status_code=202,
            status=RunStatus.WAITING_FOR_APPROVAL,
            message="Digest workflow generated a proposal and is waiting for approval.",
            approval_required=True,
            response_fields={
                "proposal": digest_execution.proposal,
                "digest_result": digest_execution.digest_result,
            },
        )

    if digest_execution.checkpoint_used:
        message = "Digest workflow resumed from checkpoint."
    elif digest_execution.digest_result.fallback_used:
        if approval_proposal_requested:
            message = "Digest workflow completed with safe fallback; no approval proposal was generated."
        else:
            message = "Digest workflow completed with safe fallback."
    elif approval_proposal_requested:
        message = "Digest workflow completed without a pending approval item."
    else:
        message = "Digest workflow completed with indexed note digest."

    return WorkflowInvokeOutcome(
        http_status_code=200,
        status=RunStatus.COMPLETED,
        message=message,
        response_fields={"digest_result": digest_execution.digest_result},
    )


WORKFLOW_INVOKE_HANDLERS: dict[WorkflowAction, WorkflowInvokeHandler] = {
    WorkflowAction.ASK_QA: WorkflowInvokeHandler(
        invoke=_invoke_ask_execution,
        build_outcome=_build_ask_outcome,
    ),
    WorkflowAction.INGEST_STEWARD: WorkflowInvokeHandler(
        invoke=_invoke_ingest_execution,
        build_outcome=_build_ingest_outcome,
    ),
    WorkflowAction.DAILY_DIGEST: WorkflowInvokeHandler(
        invoke=_invoke_digest_execution,
        build_outcome=_build_digest_outcome,
    ),
}


def _build_workflow_invoke_response(
    execution: SupportedWorkflowExecution,
    outcome: WorkflowInvokeOutcome,
) -> WorkflowInvokeResponse:
    # 这里统一收口公共响应字段，避免每新增一条 workflow 就在 API 层重新拼
    # `thread_id/run_id/status/message/approval_required` 这套控制面样板。
    return WorkflowInvokeResponse(
        run_id=execution.run_id,
        thread_id=execution.thread_id,
        action_type=execution.action_type,
        status=outcome.status,
        message=outcome.message,
        approval_required=outcome.approval_required,
        **outcome.response_fields,
    )


def _build_not_implemented_workflow_response(
    request: WorkflowInvokeRequest,
    *,
    thread_id: str,
    run_id: str,
) -> WorkflowInvokeResponse:
    return WorkflowInvokeResponse(
        run_id=run_id,
        thread_id=thread_id,
        action_type=request.action_type,
        status=RunStatus.NOT_IMPLEMENTED,
        message=(
            "Workflow baseline accepted. Graph execution is not implemented yet; "
            "next step is to attach LangGraph nodes and checkpointing."
        ),
        approval_required=request.require_approval and request.action_type != WorkflowAction.ASK_QA,
    )


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"message": "Knowledge Steward backend baseline is running."}


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        service_name=settings.service_name,
        version=settings.version,
        status="ok",
        model_strategy="cloud_primary_local_compatible",
        supported_actions=[
            WorkflowAction.ASK_QA,
            WorkflowAction.INGEST_STEWARD,
            WorkflowAction.DAILY_DIGEST,
        ],
        providers=build_provider_descriptors(),
        sample_vault=get_sample_vault_stats(),
    )


@app.post("/workflows/invoke", response_model=WorkflowInvokeResponse, status_code=202, tags=["workflow"])
def invoke_workflow(request: WorkflowInvokeRequest, response: Response) -> WorkflowInvokeResponse:
    if request.resume_from_checkpoint and not request.thread_id:
        raise HTTPException(
            status_code=400,
            detail="resume_from_checkpoint requests must provide an explicit thread_id.",
        )

    thread_id = request.thread_id or f"thread_{uuid4().hex}"
    # `thread_id` 代表同一工作流事务，`run_id` 代表这一次实际执行。
    # 先在 API 入口生成两者，避免 graph 内外各自生成导致审计关联断裂。
    run_id = f"run_{uuid4().hex}"
    handler = WORKFLOW_INVOKE_HANDLERS.get(request.action_type)
    if handler is None:
        return _build_not_implemented_workflow_response(
            request,
            thread_id=thread_id,
            run_id=run_id,
        )

    try:
        execution = handler.invoke(request, thread_id, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    outcome = handler.build_outcome(request, execution)
    response.status_code = outcome.http_status_code
    return _build_workflow_invoke_response(execution, outcome)


@app.post("/workflows/resume", response_model=WorkflowResumeResponse, tags=["workflow"])
def resume_workflow_endpoint(
    request: WorkflowResumeRequest,
    response: Response,
) -> WorkflowResumeResponse:
    run_id = f"run_{uuid4().hex}"
    try:
        resumed_execution = resume_workflow(
            request,
            settings=settings,
            run_id=run_id,
        )
    except ResumeWorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ResumeWorkflowConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ResumeWorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response.status_code = 200
    return WorkflowResumeResponse(
        run_id=resumed_execution.run_id,
        thread_id=resumed_execution.thread_id,
        proposal_id=resumed_execution.proposal.proposal_id,
        action_type=resumed_execution.action_type,
        status=RunStatus.COMPLETED,
        message=resumed_execution.message,
        approval_required=False,
        proposal=resumed_execution.proposal,
        approval_decision=resumed_execution.approval_decision,
        audit_event_id=resumed_execution.audit_event_id,
        resumed_from_checkpoint=True,
        writeback_result=resumed_execution.writeback_result,
        post_writeback_sync=resumed_execution.post_writeback_sync,
    )


@app.post("/workflows/rollback", response_model=WorkflowRollbackResponse, tags=["workflow"])
def rollback_workflow_endpoint(
    request: WorkflowRollbackRequest,
    response: Response,
) -> WorkflowRollbackResponse:
    run_id = f"run_{uuid4().hex}"
    try:
        rolled_back_execution = rollback_workflow(
            thread_id=request.thread_id,
            proposal_id=request.proposal_id,
            rollback_result=request.rollback_result,
            settings=settings,
            run_id=run_id,
        )
    except ResumeWorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ResumeWorkflowConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ResumeWorkflowValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response.status_code = 200
    return WorkflowRollbackResponse(
        run_id=rolled_back_execution.run_id,
        thread_id=rolled_back_execution.thread_id,
        proposal_id=rolled_back_execution.proposal.proposal_id,
        action_type=rolled_back_execution.action_type,
        status=RunStatus.COMPLETED,
        message=rolled_back_execution.message,
        proposal=rolled_back_execution.proposal,
        audit_event_id=rolled_back_execution.audit_event_id,
        rollback_result=rolled_back_execution.rollback_result,
    )


@app.get("/workflows/pending-approvals", response_model=WorkflowPendingApprovalsResponse, tags=["workflow"])
def list_pending_approvals_endpoint() -> WorkflowPendingApprovalsResponse:
    normalized_db_path = initialize_index_db(
        settings.index_db_path,
        settings=settings,
    )
    connection = connect_sqlite(normalized_db_path)
    try:
        pending_records = list_pending_approval_records(connection)
    finally:
        connection.close()

    return WorkflowPendingApprovalsResponse(
        items=[
            PendingApprovalItem(
                thread_id=record.thread_id,
                proposal_id=record.persisted_proposal.proposal.proposal_id,
                action_type=record.persisted_proposal.proposal.action_type,
                graph_name=record.graph_name,
                summary=record.persisted_proposal.proposal.summary,
                target_note_path=record.persisted_proposal.proposal.target_note_path,
                risk_level=record.persisted_proposal.proposal.risk_level,
                proposal=record.persisted_proposal.proposal,
                proposal_created_at=record.persisted_proposal.created_at,
                proposal_updated_at=record.persisted_proposal.updated_at,
                checkpoint_updated_at=record.checkpoint_updated_at,
            )
            for record in pending_records
        ]
    )


def main() -> None:
    """Run the local development server with repository defaults."""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
