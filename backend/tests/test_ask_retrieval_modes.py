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


def _candidate() -> RetrievedChunkCandidate:
    return RetrievedChunkCandidate(
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

        cases = [
            (
                RetrievalBenchmarkMode.FTS_ONLY,
                "app.benchmark.ask_retrieval_modes.search_chunks",
                "fts query",
                {"vault_root": settings.sample_vault_dir},
            ),
            (
                RetrievalBenchmarkMode.VECTOR_ONLY,
                "app.benchmark.ask_retrieval_modes.search_chunk_vectors",
                "vector query",
                {"settings": settings},
            ),
            (
                RetrievalBenchmarkMode.HYBRID_RRF,
                "app.benchmark.ask_retrieval_modes.search_hybrid_chunks",
                "hybrid query",
                {"settings": settings},
            ),
        ]

        for mode, patch_target, query, expected_kwargs in cases:
            with self.subTest(mode=mode):
                response = RetrievalSearchResponse(candidates=[candidate])
                with patch(patch_target, return_value=response) as mocked_search:
                    result = run_retrieval_mode(
                        connection=connection,
                        query=query,
                        settings=settings,
                        mode=mode,
                    )

                self.assertEqual(result, [candidate])
                mocked_search.assert_called_once()
                called_args, called_kwargs = mocked_search.call_args
                self.assertEqual(called_args[0], connection)
                self.assertEqual(called_args[1], query)
                self.assertEqual(called_kwargs["limit"], 10)
                for key, value in expected_kwargs.items():
                    self.assertEqual(called_kwargs[key], value)

    def test_run_retrieval_mode_raises_for_disabled_responses(self) -> None:
        settings = get_settings()
        connection = sentinel.connection
        response = RetrievalSearchResponse(
            candidates=[],
            disabled=True,
            disabled_reason="vector_index_not_ready",
        )

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

    def test_run_retrieval_mode_wraps_backend_exceptions(self) -> None:
        settings = get_settings()
        connection = sentinel.connection

        with patch(
            "app.benchmark.ask_retrieval_modes.search_hybrid_chunks",
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


if __name__ == "__main__":
    unittest.main()
