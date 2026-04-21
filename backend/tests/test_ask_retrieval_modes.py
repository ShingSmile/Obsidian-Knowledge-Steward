from __future__ import annotations

import unittest
from unittest.mock import patch, sentinel

from app.benchmark.ask_retrieval_modes import (
    RetrievalBenchmarkMode,
    RetrievalBenchmarkModeError,
    run_retrieval_mode,
)
from app.config import get_settings
from app.contracts.workflow import RetrievalSearchResponse, RetrievedChunkCandidate
from app.retrieval.embeddings import EmbeddingProviderTarget


def _candidate(*, retrieval_source: str = "sqlite_fts") -> RetrievedChunkCandidate:
    return RetrievedChunkCandidate(
        retrieval_source=retrieval_source,
        chunk_id="chunk-1",
        note_id="note-1",
        path="Notes/Alpha.md",
        title="Alpha",
        heading_path="Summary",
        note_type="note",
        template_family="default",
        daily_note_date=None,
        source_mtime_ns=1,
        start_line=1,
        end_line=2,
        score=1.0,
        snippet="snippet",
        text="alpha evidence",
    )


class AskRetrievalModesTest(unittest.TestCase):
    def test_run_retrieval_mode_dispatches_each_mode_with_fixed_top_k(self) -> None:
        settings = get_settings()
        connection = sentinel.connection
        candidate = _candidate()
        local_target = EmbeddingProviderTarget(
            provider_key="local",
            provider_name="ollama",
            base_url="http://127.0.0.1:11434",
            model_name="nomic-embed-text",
        )

        with patch(
            "app.benchmark.ask_retrieval_modes.search_chunks",
            return_value=RetrievalSearchResponse(candidates=[candidate]),
        ) as mocked_fts:
            result = run_retrieval_mode(
                connection=connection,
                query="fts query",
                settings=settings,
                mode=RetrievalBenchmarkMode.FTS_ONLY,
            )

        self.assertEqual(result, [candidate])
        mocked_fts.assert_called_once()
        called_args, called_kwargs = mocked_fts.call_args
        self.assertEqual(called_args[0], connection)
        self.assertEqual(called_args[1], "fts query")
        self.assertEqual(called_kwargs["limit"], 10)
        self.assertEqual(called_kwargs["vault_root"], settings.sample_vault_dir)

        with patch(
            "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
            return_value=local_target,
        ) as mocked_resolve_target:
            with patch(
                "app.benchmark.ask_retrieval_modes.search_chunk_vectors",
                return_value=RetrievalSearchResponse(candidates=[candidate]),
            ) as mocked_vector:
                result = run_retrieval_mode(
                    connection=connection,
                    query="vector query",
                    settings=settings,
                    mode=RetrievalBenchmarkMode.VECTOR_ONLY,
                )

        self.assertEqual(result, [candidate])
        mocked_resolve_target.assert_called_once_with(
            settings=settings,
            provider_key="local",
        )
        mocked_vector.assert_called_once()
        called_args, called_kwargs = mocked_vector.call_args
        self.assertEqual(called_args[0], connection)
        self.assertEqual(called_args[1], "vector query")
        self.assertEqual(called_kwargs["limit"], 10)
        self.assertEqual(called_kwargs["settings"], settings)
        self.assertEqual(called_kwargs["provider_targets"], [local_target])
        self.assertNotIn("provider_preference", called_kwargs)

        fts_candidate = _candidate()
        vector_candidate = _candidate()
        vector_candidate = vector_candidate.model_copy(update={"retrieval_source": "sqlite_vector"})
        with patch(
            "app.benchmark.ask_retrieval_modes.search_chunks",
            return_value=RetrievalSearchResponse(candidates=[fts_candidate]),
        ) as mocked_hybrid_fts:
            with patch(
                "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
                return_value=local_target,
            ) as mocked_hybrid_resolve_target:
                with patch(
                    "app.benchmark.ask_retrieval_modes.search_chunk_vectors",
                    return_value=RetrievalSearchResponse(candidates=[vector_candidate]),
                ) as mocked_hybrid_vector:
                    result = run_retrieval_mode(
                        connection=connection,
                        query="hybrid query",
                        settings=settings,
                        mode=RetrievalBenchmarkMode.HYBRID_RRF,
                    )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].chunk_id, fts_candidate.chunk_id)
        self.assertEqual(result[0].retrieval_source, "hybrid_rrf")
        mocked_hybrid_fts.assert_called_once()
        mocked_hybrid_resolve_target.assert_called_once_with(
            settings=settings,
            provider_key="local",
        )
        mocked_hybrid_vector.assert_called_once()
        hybrid_fts_args, hybrid_fts_kwargs = mocked_hybrid_fts.call_args
        self.assertEqual(hybrid_fts_args[0], connection)
        self.assertEqual(hybrid_fts_args[1], "hybrid query")
        self.assertEqual(hybrid_fts_kwargs["limit"], 10)
        self.assertEqual(hybrid_fts_kwargs["vault_root"], settings.sample_vault_dir)
        hybrid_vector_args, hybrid_vector_kwargs = mocked_hybrid_vector.call_args
        self.assertEqual(hybrid_vector_args[0], connection)
        self.assertEqual(hybrid_vector_args[1], "hybrid query")
        self.assertEqual(hybrid_vector_kwargs["limit"], 10)
        self.assertEqual(hybrid_vector_kwargs["settings"], settings)
        self.assertEqual(hybrid_vector_kwargs["provider_targets"], [local_target])
        self.assertNotIn("provider_preference", hybrid_vector_kwargs)

    def test_run_retrieval_mode_raises_for_disabled_responses(self) -> None:
        settings = get_settings()
        connection = sentinel.connection
        response = RetrievalSearchResponse(
            candidates=[],
            disabled=True,
            disabled_reason="vector_index_not_ready",
        )
        local_target = EmbeddingProviderTarget(
            provider_key="local",
            provider_name="ollama",
            base_url="http://127.0.0.1:11434",
            model_name="nomic-embed-text",
        )

        with patch(
            "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
            return_value=local_target,
        ):
            with patch(
                "app.benchmark.ask_retrieval_modes.search_chunk_vectors",
                return_value=response,
            ):
                with self.assertRaises(RetrievalBenchmarkModeError) as ctx:
                    run_retrieval_mode(
                        connection=connection,
                        query="vector query",
                        settings=settings,
                        mode=RetrievalBenchmarkMode.VECTOR_ONLY,
                    )

        self.assertIn("vector_index_not_ready", str(ctx.exception))

    def test_run_retrieval_mode_raises_for_runtime_disabled_hybrid_vector_branch(self) -> None:
        settings = get_settings()
        connection = sentinel.connection
        candidate = _candidate()
        disabled_vector_response = RetrievalSearchResponse(
            candidates=[],
            disabled=True,
            disabled_reason="all_embedding_providers_failed",
        )
        local_target = EmbeddingProviderTarget(
            provider_key="local",
            provider_name="ollama",
            base_url="http://127.0.0.1:11434",
            model_name="nomic-embed-text",
        )

        with patch(
            "app.benchmark.ask_retrieval_modes.search_chunks",
            return_value=RetrievalSearchResponse(candidates=[candidate]),
        ) as mocked_fts:
            with patch(
                "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
                return_value=local_target,
            ):
                with patch(
                    "app.benchmark.ask_retrieval_modes.search_chunk_vectors",
                    return_value=disabled_vector_response,
                ) as mocked_vector_search:
                    with self.assertRaises(RetrievalBenchmarkModeError) as ctx:
                        run_retrieval_mode(
                            connection=connection,
                            query="hybrid query",
                            settings=settings,
                            mode=RetrievalBenchmarkMode.HYBRID_RRF,
                        )

        self.assertEqual(
            str(ctx.exception),
            "Retrieval mode hybrid_rrf is disabled: all_embedding_providers_failed",
        )
        mocked_fts.assert_called_once()
        mocked_vector_search.assert_called_once()

    def test_run_retrieval_mode_preserves_intentional_benchmark_errors(self) -> None:
        settings = get_settings()
        connection = sentinel.connection
        local_target = EmbeddingProviderTarget(
            provider_key="local",
            provider_name="ollama",
            base_url="http://127.0.0.1:11434",
            model_name="nomic-embed-text",
        )

        with patch(
            "app.benchmark.ask_retrieval_modes.search_chunks",
            return_value=RetrievalSearchResponse(candidates=[_candidate()]),
        ):
            with patch(
                "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
                return_value=local_target,
            ):
                with patch(
                    "app.benchmark.ask_retrieval_modes.search_chunk_vectors",
                    side_effect=RetrievalBenchmarkModeError("Retrieval mode hybrid_rrf is disabled: explicit"),
                ):
                    with self.assertRaises(RetrievalBenchmarkModeError) as ctx:
                        run_retrieval_mode(
                            connection=connection,
                            query="hybrid query",
                            settings=settings,
                            mode=RetrievalBenchmarkMode.HYBRID_RRF,
                        )

        self.assertEqual(
            str(ctx.exception),
            "Retrieval mode hybrid_rrf is disabled: explicit",
        )

    def test_run_retrieval_mode_wraps_backend_exceptions(self) -> None:
        settings = get_settings()
        connection = sentinel.connection
        local_target = EmbeddingProviderTarget(
            provider_key="local",
            provider_name="ollama",
            base_url="http://127.0.0.1:11434",
            model_name="nomic-embed-text",
        )

        with patch(
            "app.benchmark.ask_retrieval_modes.search_chunks",
            return_value=RetrievalSearchResponse(candidates=[_candidate()]),
        ):
            with patch(
                "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
                return_value=local_target,
            ):
                with patch(
                    "app.benchmark.ask_retrieval_modes.search_chunk_vectors",
                    side_effect=RuntimeError("backend exploded"),
                ):
                    with self.assertRaises(RetrievalBenchmarkModeError) as ctx:
                        run_retrieval_mode(
                            connection=connection,
                            query="hybrid query",
                            settings=settings,
                            mode=RetrievalBenchmarkMode.HYBRID_RRF,
                        )

        self.assertIn("backend exploded", str(ctx.exception))

    def test_run_retrieval_mode_raises_when_local_target_is_missing_for_vector_only(self) -> None:
        settings = get_settings()
        connection = sentinel.connection

        with patch(
            "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
            return_value=None,
        ):
            with self.assertRaises(RetrievalBenchmarkModeError) as ctx:
                run_retrieval_mode(
                    connection=connection,
                    query="vector query",
                    settings=settings,
                    mode=RetrievalBenchmarkMode.VECTOR_ONLY,
                )

        self.assertEqual(
            str(ctx.exception),
            "Retrieval mode vector_only is disabled: local_embedding_provider_not_configured",
        )

    def test_run_retrieval_mode_raises_when_local_target_is_missing_for_hybrid(self) -> None:
        settings = get_settings()
        connection = sentinel.connection

        with patch(
            "app.benchmark.ask_retrieval_modes.resolve_exact_embedding_provider_target",
            return_value=None,
        ):
            with self.assertRaises(RetrievalBenchmarkModeError) as ctx:
                run_retrieval_mode(
                    connection=connection,
                    query="hybrid query",
                    settings=settings,
                    mode=RetrievalBenchmarkMode.HYBRID_RRF,
                )

        self.assertEqual(
            str(ctx.exception),
            "Retrieval mode hybrid_rrf is disabled: local_embedding_provider_not_configured",
        )


if __name__ == "__main__":
    unittest.main()
