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

from app.benchmark.ask_retrieval_benchmark import run_ask_retrieval_benchmark  # noqa: E402
from app.config import get_settings  # noqa: E402


def _build_arg_parser() -> "argparse.ArgumentParser":
    import argparse

    parser = argparse.ArgumentParser(prog="run_retrieval_benchmark.py")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dataset", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    try:
        args = parser.parse_args(argv)
        result = run_ask_retrieval_benchmark(
            settings=get_settings(),
            dataset_path=args.dataset,
            output_path=args.output,
        )
        return 0 if result.get("run_status") == "passed" else 1
    except (OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
