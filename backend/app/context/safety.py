from __future__ import annotations

import re

SUSPICIOUS_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+|any\s+|the\s+|previous\s+|prior\s+)?instructions?"),
    re.compile(r"(?:reveal|show|print|leak)\b.{0,40}\bsystem prompt\b"),
    re.compile(r"(?:bypass|override|disable)\b.{0,40}\b(?:safety|guardrail|policy|instruction)s?\b"),
)


def detect_safety_flags(text: str) -> list[str]:
    lowered = text.lower()
    return [
        "possible_prompt_injection"
        for pattern in SUSPICIOUS_PATTERNS
        if pattern.search(lowered)
    ]
