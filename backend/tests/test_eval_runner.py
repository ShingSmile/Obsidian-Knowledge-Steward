from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT_DIR = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = ROOT_DIR / "eval" / "run_eval.py"


class EvalRunnerTests(unittest.TestCase):
    def test_run_eval_writes_result_file_for_filtered_fixture_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "fixture_eval_result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EVAL_SCRIPT),
                    "--case-id",
                    "ask_fixture_generated_answer_citation_valid",
                    "--case-id",
                    "digest_fixture_empty_index_fallback",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if completed.returncode != 0:
                self.fail(
                    "run_eval fixture cases failed unexpectedly.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}"
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["selected_case_count"], 2)
            self.assertEqual(payload["summary"]["passed_case_count"], 2)
            self.assertEqual(payload["summary"]["failed_case_count"], 0)
            self.assertEqual(
                [case["case_id"] for case in payload["cases"]],
                [
                    "ask_fixture_generated_answer_citation_valid",
                    "digest_fixture_empty_index_fallback",
                ],
            )
            self.assertEqual(
                payload["cases"][0]["actual"]["ask_groundedness"]["bucket"],
                "grounded",
            )

    def test_run_eval_can_execute_sample_vault_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "sample_eval_result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EVAL_SCRIPT),
                    "--case-id",
                    "ask_sample_retrieval_only_daily_notes",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if completed.returncode != 0:
                self.fail(
                    "run_eval sample_vault case failed unexpectedly.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}"
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["selected_case_count"], 1)
            self.assertEqual(payload["summary"]["passed_case_count"], 1)
            self.assertEqual(payload["summary"]["failed_case_count"], 0)
            self.assertEqual(payload["cases"][0]["outcome"], "passed")
            self.assertEqual(
                payload["cases"][0]["actual"]["ask_result"]["mode"],
                "retrieval_only",
            )
            self.assertGreaterEqual(
                payload["cases"][0]["actual"]["ask_result"]["citation_count"],
                1,
            )

    def test_run_eval_can_execute_resume_workflow_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "resume_eval_result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EVAL_SCRIPT),
                    "--case-id",
                    "resume_fixture_reject_waiting_proposal",
                    "--case-id",
                    "resume_fixture_writeback_success",
                    "--case-id",
                    "resume_fixture_writeback_failure",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if completed.returncode != 0:
                self.fail(
                    "run_eval resume cases failed unexpectedly.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}"
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["selected_case_count"], 3)
            self.assertEqual(payload["summary"]["passed_case_count"], 3)
            self.assertEqual(payload["summary"]["failed_case_count"], 0)

            case_map = {case["case_id"]: case for case in payload["cases"]}
            self.assertFalse(
                case_map["resume_fixture_reject_waiting_proposal"]["actual"]["approval_decision"]["approved"]
            )
            self.assertTrue(
                case_map["resume_fixture_writeback_success"]["actual"]["writeback_result"]["applied"]
            )
            self.assertIn(
                "before_hash mismatch",
                case_map["resume_fixture_writeback_failure"]["actual"]["writeback_result"]["error"],
            )

            governance_overview = payload["summary"]["benchmark_overview"]["governance"]
            resume_overview = governance_overview["scenario_overview"]["resume_workflow"]
            self.assertEqual(governance_overview["selected_case_count"], 3)
            self.assertEqual(resume_overview["selected_case_count"], 3)
            self.assertEqual(
                resume_overview["core_metrics"]["approval_decision_breakdown"]["approved"],
                2,
            )
            self.assertEqual(
                resume_overview["core_metrics"]["approval_decision_breakdown"]["rejected"],
                1,
            )
            self.assertEqual(
                resume_overview["core_metrics"]["writeback_outcome_breakdown"]["applied"],
                1,
            )
            self.assertEqual(
                resume_overview["core_metrics"]["writeback_outcome_breakdown"]["failed"],
                1,
            )
            self.assertEqual(
                resume_overview["core_metrics"]["writeback_outcome_breakdown"]["not_present"],
                1,
            )
            self.assertIn(
                "writeback_failure:before_hash_mismatch",
                resume_overview["failure_type_breakdown"],
            )

    def test_run_eval_flags_semantic_overclaim_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "ask_groundedness_eval_result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EVAL_SCRIPT),
                    "--case-id",
                    "ask_fixture_semantic_overclaim_writeback",
                    "--case-id",
                    "ask_fixture_semantic_overclaim_governance",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if completed.returncode != 0:
                self.fail(
                    "run_eval semantic overclaim cases failed unexpectedly.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}"
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["selected_case_count"], 2)
            self.assertEqual(payload["summary"]["passed_case_count"], 2)
            self.assertEqual(payload["summary"]["failed_case_count"], 0)

            case_map = {case["case_id"]: case for case in payload["cases"]}
            self.assertEqual(
                case_map["ask_fixture_semantic_overclaim_writeback"]["actual"]["ask_groundedness"]["bucket"],
                "unsupported_claim",
            )
            self.assertFalse(
                case_map["ask_fixture_semantic_overclaim_writeback"]["actual"]["ask_groundedness"]["consistent"]
            )
            self.assertEqual(
                case_map["ask_fixture_semantic_overclaim_writeback"]["actual"]["ask_result"]["mode"],
                "retrieval_only",
            )
            self.assertEqual(
                case_map["ask_fixture_semantic_overclaim_writeback"]["actual"]["ask_result"]["guardrail_action"],
                "refuse_strong_claim",
            )
            self.assertEqual(
                case_map["ask_fixture_semantic_overclaim_governance"]["actual"]["ask_groundedness"]["bucket"],
                "unsupported_claim",
            )
            self.assertEqual(
                case_map["ask_fixture_semantic_overclaim_governance"]["actual"]["ask_result"]["mode"],
                "retrieval_only",
            )
            self.assertEqual(
                case_map["ask_fixture_semantic_overclaim_governance"]["actual"]["ask_result"]["guardrail_action"],
                "refuse_strong_claim",
            )

    def test_run_eval_reports_tool_and_guardrail_scenario_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "tool_guardrail_eval_result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EVAL_SCRIPT),
                    "--case-id",
                    "ask_fixture_tool_call_load_excerpt_success",
                    "--case-id",
                    "ask_fixture_invalid_tool_request_downgrades",
                    "--case-id",
                    "ask_fixture_injection_guardrail_refusal",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if completed.returncode != 0:
                self.fail(
                    "run_eval tool/guardrail cases failed unexpectedly.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}"
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            scenario_overview = payload["summary"]["benchmark_overview"][
                "question_answering"
            ]["scenario_overview"]["tool_and_guardrail"]
            self.assertEqual(payload["summary"]["selected_case_count"], 3)
            self.assertEqual(scenario_overview["selected_case_count"], 3)
            self.assertEqual(
                scenario_overview["core_metrics"]["tool_call_breakdown"]["attempted"],
                2,
            )
            self.assertIn(
                "guardrail:possible_injection_detected",
                scenario_overview["failure_type_breakdown"],
            )

    def test_run_eval_reports_metric_overview_for_hybrid_and_governance_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "hybrid_governance_eval_result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EVAL_SCRIPT),
                    "--case-id",
                    "ask_fixture_hybrid_retrieval_only",
                    "--case-id",
                    "governance_fixture_waiting_proposal_hybrid",
                    "--case-id",
                    "governance_fixture_no_proposal_fallback",
                    "--case-id",
                    "digest_fixture_structured_result_metrics",
                    "--case-id",
                    "digest_fixture_waiting_proposal_metrics",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if completed.returncode != 0:
                self.fail(
                    "run_eval hybrid/governance metric cases failed unexpectedly.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}"
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["selected_case_count"], 5)
            self.assertEqual(payload["summary"]["passed_case_count"], 5)
            self.assertEqual(payload["summary"]["failed_case_count"], 0)

            metric_overview = payload["summary"]["metric_overview"]
            self.assertGreaterEqual(metric_overview["faithfulness"]["case_count"], 5)
            self.assertGreaterEqual(metric_overview["relevancy"]["average_score"], 1.0)
            self.assertGreaterEqual(metric_overview["context_precision"]["average_score"], 0.7)
            self.assertGreaterEqual(metric_overview["context_recall"]["average_score"], 1.0)

            benchmark_overview = payload["summary"]["benchmark_overview"]
            qa_overview = benchmark_overview["question_answering"]
            governance_overview = benchmark_overview["governance"]
            self.assertEqual(qa_overview["selected_case_count"], 1)
            self.assertEqual(governance_overview["selected_case_count"], 4)
            self.assertEqual(
                qa_overview["scenario_overview"]["ask"]["core_metrics"]["retrieval_only_rate"],
                1.0,
            )
            self.assertEqual(
                governance_overview["scenario_overview"]["governance"]["core_metrics"]["proposal_generation_rate"],
                0.5,
            )
            self.assertEqual(
                governance_overview["scenario_overview"]["digest"]["core_metrics"]["proposal_generation_rate"],
                0.5,
            )
            self.assertEqual(
                governance_overview["scenario_overview"]["governance"]["core_metrics"]["analysis_fallback_reason_breakdown"]["no_governance_issues_detected"],
                1,
            )
            self.assertIn(
                "analysis_fallback:no_governance_issues_detected",
                governance_overview["failure_type_breakdown"],
            )

            case_map = {case["case_id"]: case for case in payload["cases"]}
            self.assertIn(
                "hybrid_rrf",
                case_map["ask_fixture_hybrid_retrieval_only"]["actual"]["ask_result"]["retrieved_candidate_retrieval_sources"],
            )
            self.assertIn(
                "semantic_claim_report",
                case_map["governance_fixture_waiting_proposal_hybrid"]["actual"]["quality_metrics"]["faithfulness"]["reason"],
            )
            self.assertIn(
                "semantic_claim_report",
                case_map["digest_fixture_structured_result_metrics"]["actual"]["quality_metrics"]["faithfulness"]["reason"],
            )
            self.assertIn(
                "hybrid_rrf",
                case_map["governance_fixture_waiting_proposal_hybrid"]["actual"]["analysis_result"]["related_candidate_retrieval_sources"],
            )
            self.assertEqual(
                case_map["governance_fixture_no_proposal_fallback"]["actual"]["analysis_result"]["fallback_reason"],
                "no_governance_issues_detected",
            )

    def test_run_eval_reports_four_dimension_ask_metrics_with_answer_relevancy_alias(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "ask_quality_eval_result.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(EVAL_SCRIPT),
                    "--case-id",
                    "ask_fixture_generated_answer_citation_valid",
                    "--case-id",
                    "ask_fixture_semantic_partial_support",
                    "--case-id",
                    "ask_fixture_semantic_overclaim_writeback",
                    "--case-id",
                    "ask_fixture_semantic_overclaim_governance",
                    "--case-id",
                    "ask_fixture_hybrid_retrieval_only",
                    "--output",
                    str(output_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            if completed.returncode != 0:
                self.fail(
                    "run_eval ask quality cases failed unexpectedly.\n"
                    f"stdout:\n{completed.stdout}\n"
                    f"stderr:\n{completed.stderr}"
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["selected_case_count"], 5)
            self.assertEqual(payload["summary"]["passed_case_count"], 5)
            self.assertEqual(payload["summary"]["failed_case_count"], 0)

            metric_overview = payload["summary"]["metric_overview"]
            self.assertEqual(metric_overview["faithfulness"]["case_count"], 5)
            self.assertEqual(metric_overview["answer_relevancy"]["case_count"], 5)
            self.assertEqual(metric_overview["context_precision"]["case_count"], 5)
            self.assertEqual(metric_overview["context_recall"]["case_count"], 5)
            self.assertEqual(
                metric_overview["answer_relevancy"]["average_score"],
                metric_overview["relevancy"]["average_score"],
            )

            ask_overview = payload["summary"]["benchmark_overview"][
                "question_answering"
            ]["scenario_overview"]["ask"]
            self.assertEqual(ask_overview["selected_case_count"], 5)
            self.assertEqual(
                ask_overview["metric_overview"]["answer_relevancy"]["case_count"],
                5,
            )

            case_map = {case["case_id"]: case for case in payload["cases"]}
            partial_case = case_map["ask_fixture_semantic_partial_support"]
            self.assertEqual(partial_case["actual"]["ask_result"]["mode"], "generated_answer")
            self.assertGreaterEqual(
                partial_case["actual"]["quality_metrics"]["faithfulness"]["score"],
                0.7,
            )
            self.assertLess(
                partial_case["actual"]["quality_metrics"]["faithfulness"]["score"],
                1.0,
            )
            self.assertIn(
                "semantic_claim_report",
                partial_case["actual"]["quality_metrics"]["faithfulness"]["reason"],
            )
            self.assertGreaterEqual(
                partial_case["actual"]["quality_metrics"]["answer_relevancy"]["score"],
                1.0,
            )


if __name__ == "__main__":
    unittest.main()
