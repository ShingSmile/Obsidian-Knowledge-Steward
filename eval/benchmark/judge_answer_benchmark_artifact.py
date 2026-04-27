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

from app.benchmark.ask_answer_benchmark_judge import (  # noqa: E402
    JudgeConfigOverrides,
    resolve_judge_provider_config,
)
from app.benchmark.ask_answer_benchmark_replay import judge_answer_benchmark_artifact  # noqa: E402
from app.config import get_settings  # noqa: E402


def _build_arg_parser() -> "argparse.ArgumentParser":
    import argparse

    parser = argparse.ArgumentParser(prog="judge_answer_benchmark_artifact.py")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--judge-provider-name", default="")
    parser.add_argument("--judge-base-url", default="")
    parser.add_argument("--judge-api-key", default="")
    parser.add_argument("--judge-model", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    try:
        args = parser.parse_args(argv)
        if args.input is None:
            print("ERROR: --input is required", file=sys.stderr)
            return 1
        if args.output is None:
            print("ERROR: --output is required", file=sys.stderr)
            return 1

        settings = get_settings()
        judge_provider_config = resolve_judge_provider_config(
            settings,
            JudgeConfigOverrides(
                provider_name=args.judge_provider_name or "",
                base_url=args.judge_base_url or "",
                api_key=args.judge_api_key or "",
                model=args.judge_model or "",
            ),
        )

        if not judge_provider_config.base_url.strip():
            print("ERROR: judge base URL is required", file=sys.stderr)
            return 1
        if not judge_provider_config.model_name.strip():
            print("ERROR: judge model is required", file=sys.stderr)
            return 1

        judge_answer_benchmark_artifact(
            input_path=args.input,
            output_path=args.output,
            settings=settings,
            dataset_path=args.dataset,
            judge_provider_config=judge_provider_config,
        )
        return 0
    except SystemExit as exc:
        return 0 if exc.code == 0 else 1
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
