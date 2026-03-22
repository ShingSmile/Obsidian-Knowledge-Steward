from __future__ import annotations

SUSPICIOUS_PATTERNS = (
    "ignore previous instructions",
    "system prompt",
    "tool call",
)


def detect_safety_flags(text: str) -> list[str]:
    lowered = text.lower()
    return [
        "possible_prompt_injection"
        for pattern in SUSPICIOUS_PATTERNS
        if pattern in lowered
    ]

