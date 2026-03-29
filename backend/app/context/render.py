from __future__ import annotations

import json

from app.contracts.workflow import ContextBundle


def render_tool_selection_prompt(bundle: ContextBundle) -> str:
    return "\n".join(
        [
            f"User intent: {bundle.user_intent}",
            f"Allowed tools: {', '.join(bundle.allowed_tool_names)}",
            *[
                f"[{index}] {item.source_path} :: {item.text}"
                for index, item in enumerate(bundle.evidence_items, start=1)
            ],
        ]
    )


def render_grounded_answer_prompt(bundle: ContextBundle) -> str:
    retrieval_items = [
        item for item in bundle.evidence_items if item.source_kind == "retrieval"
    ]
    tool_results = [
        result
        for result in bundle.tool_results
        if result.ok and result.allow_context_reentry
    ]

    lines = [f"用户问题：{bundle.user_intent}", "", "可用检索证据如下："]
    if retrieval_items:
        for index, item in enumerate(retrieval_items, start=1):
            lines.extend(
                [
                    f"[{index}] path: {item.source_path}",
                    f"source_note_title: {item.source_note_title or item.source_path}",
                    f"heading_path: {item.heading_path or item.source_path}",
                    f"position_hint: {item.position_hint or '1/1'}",
                    "content:",
                    item.text,
                    "",
                ]
            )
    else:
        lines.extend(["(无可用检索证据)", ""])

    if tool_results:
        lines.extend(
            [
                "补充工具结果如下：",
                "这些结果用于补充理解，但回答中的 [n] 引用必须仍然指向上面的检索证据编号。",
            ]
        )
        for result in tool_results:
            lines.extend(
                [
                    f"- tool: {result.tool_name}",
                    json.dumps(result.data, ensure_ascii=False, sort_keys=True),
                ]
            )
        lines.append("")

    lines.append("请用中文给出简洁回答，并确保每个关键结论都带引用编号。")
    return "\n".join(lines)
