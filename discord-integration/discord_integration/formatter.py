"""Format LLM answers for Discord delivery."""

from __future__ import annotations

from roboto_guilliman.prompts import RetrievedChunk

_MAX_LENGTH = 2000


def format_for_discord(answer: str, *, chunks: list[RetrievedChunk] | None = None) -> str:
    text = answer.strip()

    if chunks:
        sources = sorted({chunk.source for chunk in chunks if chunk.source})
        if sources:
            text = f"{text}\n\n*Source: {', '.join(sources)}*"

    if len(text) <= _MAX_LENGTH:
        return text

    return text[: _MAX_LENGTH - 3].rstrip() + "..."
