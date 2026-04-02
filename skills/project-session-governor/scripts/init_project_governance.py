#!/usr/bin/env python3
"""
Initialize a new project's governance docs from the project-session-governor starter.

Usage:
    python init_project_governance.py /path/to/target \
      --project-name "My Project" \
      --project-subtitle "Short subtitle" \
      --project-positioning "What this project is for"
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PLACEHOLDER_DEFAULTS = {
    "{{PROJECT_NAME}}": "PROJECT_NAME",
    "{{PROJECT_SUBTITLE}}": "PROJECT_SUBTITLE",
    "{{PROJECT_POSITIONING}}": "PROJECT_POSITIONING",
    "{{CAPABILITY_1}}": "CORE_CAPABILITY_1",
    "{{CAPABILITY_2}}": "CORE_CAPABILITY_2",
    "{{CAPABILITY_3}}": "CORE_CAPABILITY_3",
    "{{CAPABILITY_4}}": "CORE_CAPABILITY_4",
    "{{ENV_REQ_1}}": "ENVIRONMENT_REQUIREMENT_1",
    "{{ENV_REQ_2}}": "ENVIRONMENT_REQUIREMENT_2",
    "{{START_COMMAND}}": "START_COMMAND_HERE",
    "{{HEALTHCHECK_COMMAND}}": "HEALTHCHECK_COMMAND_HERE",
    "{{CURRENT_PHASE}}": "bootstrap",
    "{{CURRENT_SUMMARY}}": "Replace this line with the current project state summary.",
    "{{RECENT_DONE_1}}": "No completed work recorded yet.",
    "{{RECENT_DONE_2}}": "Replace with the second recent completed item if needed.",
    "{{NEXT_TASK_ID}}": "TASK-001",
    "{{NEXT_TASK_TITLE}}": "Define the first executable medium task",
    "{{RISK_1}}": "Replace with the highest current project risk.",
    "{{RISK_2}}": "Replace with the second active risk or remove later.",
    "{{RISK_3}}": "Replace with the third active risk or remove later.",
    "{{FILE_1}}": "path/to/first/relevant/file",
    "{{FILE_2}}": "path/to/second/relevant/file",
    "{{FILE_3}}": "path/to/third/relevant/file",
    "{{TASK_ID}}": "TASK-001",
    "{{TASK_TITLE}}": "Define the first executable medium task",
    "{{TASK_CATEGORY}}": "Bootstrap",
    "{{TASK_PRIORITY}}": "P0",
    "{{TASK_GOAL}}": "Replace with the first task goal.",
    "{{OUT_OF_SCOPE_1}}": "Replace with the first out-of-scope item.",
    "{{OUT_OF_SCOPE_2}}": "Replace with the second out-of-scope item.",
    "{{AC_1}}": "Replace with the first acceptance criterion.",
    "{{AC_2}}": "Replace with the second acceptance criterion.",
    "{{AC_3}}": "Replace with the third acceptance criterion.",
    "{{DEPENDS_ON_1}}": "TASK-000",
    "{{TASK_NOTES}}": "Replace with task notes.",
    "{{SESSION_ID}}": "SES-YYYYMMDD-01",
    "{{SESSION_TITLE}}": "Replace with the first session title",
    "{{DATE}}": "YYYY-MM-DD",
    "{{SESSION_TYPE}}": "Bootstrap",
    "{{STATUS}}": "部分完成",
    "{{ACCEPTANCE_RESULT}}": "部分满足",
    "{{SESSION_GOAL}}": "Replace with the session goal.",
    "{{GOAL_1}}": "Replace with the first session goal detail.",
    "{{DONE_1}}": "Replace with the first completed item.",
    "{{DONE_2}}": "Replace with the second completed item.",
    "{{TODO_1}}": "Replace with remaining work.",
    "{{DECISION_1}}": "Replace with the key decision made in this session.",
    "{{CMD_1}}": "replace with the main validation command",
    "{{TEST_RESULT}}": "Replace with validation result.",
    "{{UNVERIFIED}}": "Replace with what could not be verified yet.",
    "{{STATIC_ONLY}}": "Replace with static-only modifications if any.",
    "{{SCOPE_SHIFT}}": "Replace with scope drift summary, or note there was none.",
    "{{OPEN_ISSUE_1}}": "Replace with the main unresolved issue.",
    "{{NEXT_FILE_1}}": "path/to/first/file-for-next-session",
    "{{NEXT_FILE_2}}": "path/to/second/file-for-next-session",
    "{{INTERVIEW_POINT}}": "Replace with the easiest follow-up challenge point.",
    "{{VERSION}}": "v0.1.0",
    "{{LAST_UPDATED}}": "YYYY-MM-DD",
    "{{CURRENT_STAGE}}": "Bootstrap in progress",
    "{{OWNER}}": "OWNER_NAME",
    "{{PROJECT_DEFINITION}}": "Replace with the project definition.",
    "{{GOAL_2}}": "Replace with the second core goal.",
    "{{NON_GOAL_1}}": "Replace with the first non-goal.",
    "{{NON_GOAL_2}}": "Replace with the second non-goal.",
    "{{ARCHITECTURE}}": "Replace with the high-level architecture.",
    "{{ROADMAP_PRINCIPLE_1}}": "Replace with the first roadmap principle.",
    "{{ROADMAP_PRINCIPLE_2}}": "Replace with the second roadmap principle.",
    "{{ADR_1}}": "Replace with the first key design decision.",
    "{{ADR_2}}": "Replace with the second key design decision.",
    "{{ONE_LINER}}": "Replace with the one-line project pitch.",
    "{{POINT_1}}": "Replace with the first reason this project is not a toy.",
    "{{POINT_2}}": "Replace with the second reason this project is not a toy.",
    "{{QUESTION_1}}": "Replace with the first likely interview question.",
    "{{ANSWER_1}}": "Replace with the answer idea for question one.",
    "{{QUESTION_2}}": "Replace with the second likely interview question.",
    "{{ANSWER_2}}": "Replace with the answer idea for question two.",
    "{{BAD_ANSWER_1}}": "Replace with a weak or misleading answer to avoid.",
    "{{BAD_ANSWER_2}}": "Replace with another weak or misleading answer to avoid.",
    "{{CHANGE_SUMMARY}}": "Initial governance scaffold created.",
}


def build_replacements(args: argparse.Namespace) -> dict[str, str]:
    replacements = dict(PLACEHOLDER_DEFAULTS)
    # 这里优先替换用户最关心的项目元信息，其他字段保留占位值，方便后续人工补齐。
    replacements["{{PROJECT_NAME}}"] = args.project_name
    replacements["{{PROJECT_SUBTITLE}}"] = args.project_subtitle
    replacements["{{PROJECT_POSITIONING}}"] = args.project_positioning
    replacements["{{OWNER}}"] = args.owner

    capabilities = args.capability or []
    for index in range(4):
        key = f"{{{{CAPABILITY_{index + 1}}}}}"
        if index < len(capabilities):
            replacements[key] = capabilities[index]

    return replacements


def copy_tree(src: Path, dst: Path, force: bool) -> None:
    for path in src.rglob("*"):
        relative = path.relative_to(src)
        target = dst / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file without --force: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def replace_placeholders(target_root: Path, replacements: dict[str, str]) -> None:
    for path in target_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        content = path.read_text(encoding="utf-8")
        # 这里用简单字符串替换而不是模板引擎，目的是降低外部依赖并保持脚本可移植。
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize project governance docs from starter templates.")
    parser.add_argument("target_dir", help="Target project directory")
    parser.add_argument("--project-name", required=True, help="Project name")
    parser.add_argument("--project-subtitle", default="Project subtitle", help="Project subtitle")
    parser.add_argument("--project-positioning", default="Replace with project positioning.", help="Project positioning")
    parser.add_argument("--owner", default="OWNER_NAME", help="Owner name")
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Core capability. Repeat up to 4 times.",
    )
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    starter_dir = script_dir.parent / "assets" / "project-starter"
    target_dir = Path(args.target_dir).resolve()

    if not starter_dir.exists():
        raise FileNotFoundError(f"Starter directory not found: {starter_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)
    copy_tree(starter_dir, target_dir, force=args.force)
    replace_placeholders(target_dir, build_replacements(args))
    print(f"[OK] Initialized governance starter in {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
