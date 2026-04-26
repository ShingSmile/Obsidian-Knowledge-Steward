from __future__ import annotations

from pathlib import Path
import json
import sys


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.benchmark.ask_answer_benchmark import run_ask_answer_benchmark  # noqa: E402
from app.benchmark.ask_answer_benchmark_judge import (  # noqa: E402
    JudgeConfigOverrides,
    resolve_judge_provider_config,
)
from app.benchmark.ask_answer_benchmark_preflight import run_answer_benchmark_preflight  # noqa: E402
from app.config import get_settings  # noqa: E402


def _build_arg_parser() -> "argparse.ArgumentParser":
    import argparse

    parser = argparse.ArgumentParser(prog="run_answer_benchmark.py")
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--judge", choices=("enabled", "disabled"), default="disabled")
    parser.add_argument("--judge-provider-name", default="")
    parser.add_argument("--judge-base-url", default="")
    parser.add_argument("--judge-api-key", default="")
    parser.add_argument("--judge-model", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    try:
        args = parser.parse_args(argv)
        settings = get_settings()
        judge_enabled = args.judge == "enabled"
        judge_provider_config = resolve_judge_provider_config(
            settings,
            JudgeConfigOverrides(
                provider_name=args.judge_provider_name or "",
                base_url=args.judge_base_url or "",
                api_key=args.judge_api_key or "",
                model=args.judge_model or "",
            ),
        )
        preflight = run_answer_benchmark_preflight(
            settings=settings,
            mode=args.mode,
            dataset_path=args.dataset,
            smoke_subset_path=(
                ROOT_DIR / "eval" / "benchmark" / "ask_answer_benchmark_smoke_cases.json"
                if args.mode == "smoke"
                else None
            ),
            judge_enabled=judge_enabled,
            judge_provider_config=judge_provider_config,
        )
        if preflight.status != "ok":
            print(f"ERROR: {preflight.message}", file=sys.stderr)
            return 1

        result = run_ask_answer_benchmark(
            settings=settings,
            mode=args.mode,
            dataset_path=args.dataset,
            output_path=args.output,
            judge_enabled=judge_enabled,
            judge_provider_config=judge_provider_config,
        )
        return 0 if result.get("run_status") == "passed" else 1
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
