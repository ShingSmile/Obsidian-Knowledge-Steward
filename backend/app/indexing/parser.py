from __future__ import annotations

from pathlib import Path
import hashlib
import re

from app.indexing.models import HeadingInfo, NoteChunk, ParsedNote


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TASK_RE = re.compile(r"^\s*[-*]\s\[[ xX]\]", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
DATE_IN_NAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _normalize_wikilinks(text: str) -> list[str]:
    seen: set[str] = set()
    links: list[str] = []
    for match in WIKILINK_RE.findall(text):
        cleaned = match.split("|", 1)[0].strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            links.append(cleaned)
    return links


def _infer_template_family(text: str) -> str:
    if "# Task Planner" in text and "# Summary" in text:
        return "daily_en_template"
    if "# 一、工作任务" in text and "# 四、今日总结" in text:
        return "daily_cn_template"
    if "迭代总结" in text or "复盘总结" in text or "周报及任务汇总" in text:
        return "summary_note"
    return "generic"


def _infer_note_type(path: Path, text: str) -> tuple[str, str, str | None]:
    template_family = _infer_template_family(text)
    daily_note_date = None
    date_match = DATE_IN_NAME_RE.search(path.stem)
    if date_match:
        daily_note_date = date_match.group(1)

    if template_family in {"daily_en_template", "daily_cn_template"}:
        return "daily_note", template_family, daily_note_date
    if template_family == "summary_note":
        return "summary_note", template_family, daily_note_date
    return "generic_note", template_family, daily_note_date


def _build_heading_path(stack: list[tuple[int, str]]) -> str:
    return " > ".join(text for _, text in stack)


def parse_markdown_note(note_path: Path) -> ParsedNote:
    text = note_path.read_text(encoding="utf-8")
    has_frontmatter = bool(FRONTMATTER_RE.match(text))
    lines = text.splitlines()

    note_type, template_family, daily_note_date = _infer_note_type(note_path, text)
    wikilinks = _normalize_wikilinks(text)
    task_count = len(TASK_RE.findall(text))
    headings: list[HeadingInfo] = []
    chunks: list[NoteChunk] = []

    heading_stack: list[tuple[int, str]] = []
    current_heading_path: str | None = None
    current_start_line = 1
    current_lines: list[str] = []

    def flush_chunk(end_line: int) -> None:
        nonlocal current_lines, current_start_line, current_heading_path
        body = "\n".join(current_lines).strip()
        if not body:
            current_lines = []
            return
        chunk_id = hashlib.sha1(
            f"{note_path}:{current_heading_path}:{current_start_line}:{end_line}".encode("utf-8")
        ).hexdigest()[:16]
        chunks.append(
            NoteChunk(
                chunk_id=chunk_id,
                chunk_type="section_child" if current_heading_path else "note_body",
                heading_path=current_heading_path,
                start_line=current_start_line,
                end_line=end_line,
                text=body,
                task_count=len(TASK_RE.findall(body)),
                wikilinks=_normalize_wikilinks(body),
            )
        )
        current_lines = []

    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            flush_chunk(index - 1)
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, heading_text))
            heading_path = _build_heading_path(heading_stack)
            headings.append(
                HeadingInfo(
                    level=level,
                    text=heading_text,
                    line_no=index,
                    heading_path=heading_path,
                )
            )
            current_heading_path = heading_path
            current_start_line = index
            current_lines = [line]
        else:
            current_lines.append(line)

    flush_chunk(len(lines))

    title = note_path.stem
    if headings:
        title = headings[0].text if headings[0].level == 1 else note_path.stem

    return ParsedNote(
        path=str(note_path),
        title=title,
        note_type=note_type,
        template_family=template_family,
        daily_note_date=daily_note_date,
        headings=headings,
        chunks=chunks,
        wikilinks=wikilinks,
        task_count=task_count,
        has_frontmatter=has_frontmatter,
    )
