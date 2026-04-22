from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.indexing.store import connect_sqlite, initialize_index_db
from app.retrieval.embeddings import (
    embed_texts,
    resolve_exact_embedding_provider_target,
)


@dataclass(frozen=True)
class AskRetrievalPreflightResult:
    status: str
    provider_key: str | None
    provider_name: str | None
    model_name: str | None
    message: str


def run_local_retrieval_preflight(
    *,
    settings: Settings,
    db_path: Path | None = None,
) -> AskRetrievalPreflightResult:
    local_target = resolve_exact_embedding_provider_target(
        settings=settings,
        provider_key="local",
    )
    if local_target is None:
        return AskRetrievalPreflightResult(
            status="provider_not_configured",
            provider_key=None,
            provider_name=None,
            model_name=None,
            message=(
                "Local embedding provider is not configured. "
                "Set KS_LOCAL_BASE_URL and KS_LOCAL_EMBEDDING_MODEL."
            ),
        )

    probe = embed_texts(
        ["task-058 benchmark preflight"],
        settings=settings,
        provider_targets=[local_target],
    )
    if probe.disabled:
        failure_reason = probe.disabled_reason or "probe_failed"
        return AskRetrievalPreflightResult(
            status="provider_unreachable_or_model_unavailable",
            provider_key=local_target.provider_key,
            provider_name=local_target.provider_name,
            model_name=local_target.model_name,
            message=(
                "Local embedding provider probe failed for "
                f"{local_target.provider_name}/{local_target.model_name}: {failure_reason}"
            ),
        )

    initialized_db_path = initialize_index_db(db_path or settings.index_db_path, settings=settings)
    connection = connect_sqlite(initialized_db_path)
    try:
        chunk_count = connection.execute("SELECT COUNT(*) FROM chunk;").fetchone()[0]
        embedding_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM chunk_embedding
            WHERE provider_key = ? AND model_name = ?;
            """,
            (local_target.provider_key, local_target.model_name),
        ).fetchone()[0]
    finally:
        connection.close()

    if chunk_count <= 0 or embedding_count != chunk_count:
        return AskRetrievalPreflightResult(
            status="vector_index_not_ready",
            provider_key=local_target.provider_key,
            provider_name=local_target.provider_name,
            model_name=local_target.model_name,
            message=(
                "Vector index is not ready for local provider "
                f"{local_target.provider_name}/{local_target.model_name}. "
                "Run ingest to build chunk embeddings before benchmarking."
            ),
        )

    return AskRetrievalPreflightResult(
        status="ok",
        provider_key=local_target.provider_key,
        provider_name=local_target.provider_name,
        model_name=local_target.model_name,
        message=(
            "Local embedding preflight passed for "
            f"{local_target.provider_name}/{local_target.model_name}."
        ),
    )
