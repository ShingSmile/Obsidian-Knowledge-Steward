from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Sequence
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.config import Settings


EMBEDDING_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class EmbeddingProviderTarget:
    provider_key: str
    provider_name: str
    base_url: str
    model_name: str
    api_key: str | None = None


@dataclass(frozen=True)
class EmbeddingBatchResult:
    embeddings: list[list[float]]
    provider_key: str | None = None
    provider_name: str | None = None
    model_name: str | None = None
    disabled: bool = False
    disabled_reason: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None


class EmbeddingProviderError(RuntimeError):
    """Raised when a configured embedding provider cannot return usable vectors."""


def resolve_embedding_provider_targets(
    *,
    settings: Settings,
    provider_preference: str | None = None,
) -> list[EmbeddingProviderTarget]:
    normalized_preference = (provider_preference or settings.default_model_provider).strip().casefold()
    cloud_target = _build_provider_target(
        provider_key="cloud",
        provider_name=settings.cloud_provider_name,
        base_url=settings.cloud_base_url,
        model_name=settings.cloud_embedding_model,
        api_key=settings.cloud_api_key or None,
    )
    local_target = _build_provider_target(
        provider_key="local",
        provider_name=settings.local_provider_name,
        base_url=settings.local_base_url,
        model_name=settings.local_embedding_model,
        api_key=None,
    )

    available_targets = [target for target in (cloud_target, local_target) if target is not None]
    if not available_targets:
        return []

    if normalized_preference in {"local", settings.local_provider_name.casefold()}:
        preferred_order = ["local", "cloud"]
    else:
        preferred_order = ["cloud", "local"]

    ordered_targets: list[EmbeddingProviderTarget] = []
    for provider_key in preferred_order:
        for target in available_targets:
            if target.provider_key == provider_key:
                ordered_targets.append(target)
    return ordered_targets


def resolve_exact_embedding_provider_target(
    *,
    settings: Settings,
    provider_key: str,
) -> EmbeddingProviderTarget | None:
    normalized_provider_key = provider_key.strip().casefold()
    if normalized_provider_key == "cloud":
        return _build_provider_target(
            provider_key="cloud",
            provider_name=settings.cloud_provider_name,
            base_url=settings.cloud_base_url,
            model_name=settings.cloud_embedding_model,
            api_key=settings.cloud_api_key or None,
        )
    if normalized_provider_key == "local":
        return _build_provider_target(
            provider_key="local",
            provider_name=settings.local_provider_name,
            base_url=settings.local_base_url,
            model_name=settings.local_embedding_model,
            api_key=None,
        )
    return None


def embed_texts(
    texts: Sequence[str],
    *,
    settings: Settings,
    provider_preference: str | None = None,
    provider_targets: Sequence[EmbeddingProviderTarget] | None = None,
) -> EmbeddingBatchResult:
    normalized_texts = [text for text in texts if text]
    if not normalized_texts:
        return EmbeddingBatchResult(embeddings=[])

    targets = list(provider_targets) if provider_targets is not None else resolve_embedding_provider_targets(
        settings=settings,
        provider_preference=provider_preference,
    )
    preferred_target = targets[0] if targets else None
    if not targets:
        return EmbeddingBatchResult(
            embeddings=[],
            disabled=True,
            disabled_reason="no_available_embedding_provider",
        )

    last_error: EmbeddingProviderError | None = None
    for index, target in enumerate(targets):
        try:
            embeddings = _request_embeddings(target, normalized_texts)
        except EmbeddingProviderError as exc:
            last_error = exc
            continue
        return EmbeddingBatchResult(
            embeddings=embeddings,
            provider_key=target.provider_key,
            provider_name=target.provider_name,
            model_name=target.model_name,
            fallback_used=index > 0,
            fallback_reason="preferred_embedding_provider_failed" if index > 0 else None,
        )

    return EmbeddingBatchResult(
        embeddings=[],
        provider_key=preferred_target.provider_key if preferred_target is not None else None,
        provider_name=preferred_target.provider_name if preferred_target is not None else None,
        model_name=preferred_target.model_name if preferred_target is not None else None,
        disabled=True,
        disabled_reason="all_embedding_providers_failed",
        fallback_used=len(targets) > 1,
        fallback_reason="preferred_embedding_provider_failed" if len(targets) > 1 else None,
    )


def _build_provider_target(
    *,
    provider_key: str,
    provider_name: str,
    base_url: str,
    model_name: str,
    api_key: str | None,
) -> EmbeddingProviderTarget | None:
    normalized_base_url = base_url.strip().rstrip("/")
    normalized_model_name = model_name.strip()
    if not normalized_base_url or not normalized_model_name:
        return None

    return EmbeddingProviderTarget(
        provider_key=provider_key,
        provider_name=provider_name,
        base_url=normalized_base_url,
        model_name=normalized_model_name,
        api_key=api_key,
    )


def _request_embeddings(
    provider_target: EmbeddingProviderTarget,
    texts: Sequence[str],
) -> list[list[float]]:
    payload = {
        "model": provider_target.model_name,
        "input": list(texts),
    }
    headers = {
        "Content-Type": "application/json",
    }
    if provider_target.api_key:
        headers["Authorization"] = f"Bearer {provider_target.api_key}"

    request = urllib_request.Request(
        _build_embeddings_url(provider_target.base_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=EMBEDDING_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (urllib_error.HTTPError, urllib_error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise EmbeddingProviderError(str(exc)) from exc

    embeddings = _extract_embeddings(response_payload, expected_count=len(texts))
    if len(embeddings) != len(texts):
        raise EmbeddingProviderError("embedding_response_count_mismatch")
    return embeddings


def _build_embeddings_url(base_url: str) -> str:
    normalized_base_url = base_url.rstrip("/")
    if normalized_base_url.endswith("/embeddings"):
        return normalized_base_url
    if normalized_base_url.endswith("/v1"):
        return f"{normalized_base_url}/embeddings"
    return f"{normalized_base_url}/v1/embeddings"


def _extract_embeddings(
    response_payload: dict[str, object],
    *,
    expected_count: int,
) -> list[list[float]]:
    data = response_payload.get("data")
    if not isinstance(data, list) or not data:
        return []

    indexed_embeddings: dict[int, list[float]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        raw_index = item.get("index", len(indexed_embeddings))
        raw_embedding = item.get("embedding")
        if not isinstance(raw_index, int) or not isinstance(raw_embedding, list):
            continue

        normalized_embedding: list[float] = []
        for raw_value in raw_embedding:
            if not isinstance(raw_value, (int, float)):
                normalized_embedding = []
                break
            normalized_embedding.append(float(raw_value))
        if not normalized_embedding:
            continue
        indexed_embeddings[raw_index] = normalized_embedding

    ordered_embeddings: list[list[float]] = []
    for index in range(expected_count):
        embedding = indexed_embeddings.get(index)
        if embedding is None:
            return []
        ordered_embeddings.append(embedding)
    return ordered_embeddings
