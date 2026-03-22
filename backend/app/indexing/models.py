from __future__ import annotations

from pydantic import BaseModel, Field


class HeadingInfo(BaseModel):
    level: int
    text: str
    line_no: int
    heading_path: str


class NoteChunk(BaseModel):
    chunk_id: str
    chunk_type: str
    heading_path: str | None = None
    start_line: int
    end_line: int
    text: str
    task_count: int = 0
    wikilinks: list[str] = Field(default_factory=list)


class ParsedNote(BaseModel):
    path: str
    title: str
    note_type: str
    template_family: str
    daily_note_date: str | None = None
    headings: list[HeadingInfo] = Field(default_factory=list)
    chunks: list[NoteChunk] = Field(default_factory=list)
    wikilinks: list[str] = Field(default_factory=list)
    task_count: int = 0
    has_frontmatter: bool = False
