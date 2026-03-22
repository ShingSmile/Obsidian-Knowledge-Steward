from __future__ import annotations

from pathlib import Path

from app.indexing import parse_markdown_note
from app.contracts.workflow import SampleVaultStats


def describe_sample_vault(root: Path) -> SampleVaultStats:
    notes = sorted(root.rglob("*.md"))
    frontmatter_note_count = 0
    wikilink_count = 0
    task_checkbox_count = 0
    template_family_counts: dict[str, int] = {}

    for note_path in notes:
        parsed = parse_markdown_note(note_path)
        if parsed.has_frontmatter:
            frontmatter_note_count += 1
        wikilink_count += len(parsed.wikilinks)
        task_checkbox_count += parsed.task_count
        family = parsed.template_family
        template_family_counts[family] = template_family_counts.get(family, 0) + 1

    return SampleVaultStats(
        path=str(root),
        note_count=len(notes),
        frontmatter_note_count=frontmatter_note_count,
        wikilink_count=wikilink_count,
        task_checkbox_count=task_checkbox_count,
        template_family_counts=template_family_counts,
    )
