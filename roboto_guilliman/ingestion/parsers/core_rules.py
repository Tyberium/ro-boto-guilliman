"""Chunk 11th edition core rules PDFs by numbered rule boundaries (e.g. 01.03)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pathlib import Path

import fitz

RULE_HEADER_RE = re.compile(
    r"([A-Z][A-Z0-9 \-/']{2,100})\s+(\d{2}\.\d{2})",
    re.MULTILINE,
)


@dataclass(frozen=True)
class CoreRuleChunk:
    text: str
    page: int
    chunk_index: int
    rule_number: str
    title: str
    chunk_type: str = "core_rule"


def _page_at_offset(offset: int, page_starts: list[tuple[int, int]]) -> int:
    page = page_starts[0][1]
    for start, page_number in page_starts:
        if start <= offset:
            page = page_number
        else:
            break
    return page


def _join_pages(doc: fitz.Document) -> tuple[str, list[tuple[int, int]]]:
    parts: list[str] = []
    page_starts: list[tuple[int, int]] = []
    offset = 0
    for page_number, page in enumerate(doc, start=1):
        page_starts.append((offset, page_number))
        text = page.get_text("text")
        parts.append(text)
        offset += len(text) + 1
    return "\n".join(parts), page_starts


def parse_core_rules_text(
    full_text: str,
    *,
    page_starts: list[tuple[int, int]],
) -> list[CoreRuleChunk]:
    """Split document text on TITLE + NN.NN rule headers."""
    matches = list(RULE_HEADER_RE.finditer(full_text))
    if not matches:
        return []

    chunks: list[CoreRuleChunk] = []
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        rule_number = match.group(2)
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(full_text)
        rule_body = full_text[body_start:body_end].strip()
        full_chunk = f"{title} {rule_number}\n{rule_body}"
        chunks.append(
            CoreRuleChunk(
                text=full_chunk,
                page=_page_at_offset(match.start(), page_starts),
                chunk_index=index,
                rule_number=rule_number,
                title=title,
            )
        )
    return chunks


def parse_core_rules_pdf(pdf_path: str | Path | fitz.Document) -> list[CoreRuleChunk]:
    """Extract one chunk per numbered core rule across the full PDF."""
    owns_doc = not isinstance(pdf_path, fitz.Document)
    doc = fitz.open(pdf_path) if owns_doc else pdf_path
    try:
        full_text, page_starts = _join_pages(doc)
        return parse_core_rules_text(full_text, page_starts=page_starts)
    finally:
        if owns_doc:
            doc.close()
