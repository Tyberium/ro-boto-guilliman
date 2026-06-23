"""Format LLM answers for WhatsApp delivery."""

from __future__ import annotations

import re

from roboto_guilliman.prompts import RetrievedChunk

_MAX_LENGTH = 1600
_BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")
_HEADER_PATTERN = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def format_for_whatsapp(answer: str, *, chunks: list[RetrievedChunk] | None = None) -> str:
    text = _HEADER_PATTERN.sub(lambda match: match.group(1).upper(), answer)
    text = _BOLD_PATTERN.sub(r"*\1*", text)
    text = text.strip()

    if chunks:
        sources = sorted({chunk.source for chunk in chunks if chunk.source})
        if sources:
            footer = f"\n\n_Source: {', '.join(sources)}_"
            text = f"{text}{footer}"

    if len(text) <= _MAX_LENGTH:
        return text

    return text[: _MAX_LENGTH - 3].rstrip() + "..."
