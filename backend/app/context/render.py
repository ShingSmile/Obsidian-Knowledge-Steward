from __future__ import annotations

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

