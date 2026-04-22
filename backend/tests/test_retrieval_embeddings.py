from __future__ import annotations

from dataclasses import replace
import unittest

from app.config import get_settings
from app.retrieval.embeddings import (
    EmbeddingProviderTarget,
    resolve_exact_embedding_provider_target,
)


class ExactEmbeddingProviderTargetTests(unittest.TestCase):
    def test_exact_local_target_ignores_default_provider_preference(self) -> None:
        settings = replace(
            get_settings(),
            default_model_provider="cloud",
            cloud_base_url="https://cloud.example.com",
            cloud_embedding_model="cloud-embedding",
            local_base_url="http://127.0.0.1:11434",
            local_embedding_model="local-embedding",
        )

        target = resolve_exact_embedding_provider_target(settings=settings, provider_key="local")

        self.assertEqual(
            target,
            EmbeddingProviderTarget(
                provider_key="local",
                provider_name=settings.local_provider_name,
                base_url="http://127.0.0.1:11434",
                model_name="local-embedding",
            ),
        )

    def test_exact_local_target_returns_none_when_local_config_is_incomplete(self) -> None:
        settings = replace(
            get_settings(),
            default_model_provider="cloud",
            cloud_base_url="https://cloud.example.com",
            cloud_embedding_model="cloud-embedding",
            local_base_url="",
            local_embedding_model="local-embedding",
        )

        target = resolve_exact_embedding_provider_target(settings=settings, provider_key="local")

        self.assertIsNone(target)

    def test_exact_cloud_target_returns_cloud_target_when_config_is_complete(self) -> None:
        settings = replace(
            get_settings(),
            default_model_provider="local",
            cloud_base_url="https://cloud.example.com",
            cloud_embedding_model="cloud-embedding",
            local_base_url="http://127.0.0.1:11434",
            local_embedding_model="local-embedding",
        )

        target = resolve_exact_embedding_provider_target(settings=settings, provider_key="cloud")

        self.assertEqual(
            target,
            EmbeddingProviderTarget(
                provider_key="cloud",
                provider_name=settings.cloud_provider_name,
                base_url="https://cloud.example.com",
                model_name="cloud-embedding",
                api_key=settings.cloud_api_key or None,
            ),
        )


if __name__ == "__main__":
    unittest.main()
