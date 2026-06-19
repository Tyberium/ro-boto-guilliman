"""System prompts and context formatting for roboto-guilliman."""

from __future__ import annotations

import re
from dataclasses import dataclass

_LEGACY_EDITION_RE = re.compile(
    r"""
    \b(?:
        (?:9th|10th|8th|7th|6th|5th|4th|3rd|2nd|1st)\s+edition
        |(?:ninth|tenth|eighth|seventh|sixth|fifth|fourth|third|second|first)\s+edition
        |edition\s+(?:9|10|8|7|6|5|4|3|2|1)\b
        |(?:old|previous|legacy|superseded|outdated|prior)\s+(?:edition\s+)?rules\b
        |rules\s+from\s+(?:9th|10th|8th|7th)\b
        |(?:9th|10th|8th)\s+ed\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

LEGACY_EDITION_REFUSAL = (
    "**What sort of heresy is this?** "
    "roboto-guilliman adjudicates **Warhammer 40,000 11th edition** rules only. "
    "I have no mandate to consult superseded editions, and I shall not."
)


SYSTEM_PERSONA = """You are roboto-guilliman, a precise and unflappable Warhammer rules arbiter.
Your goal is to answer queries based strictly on the provided rules chunks.

Rules of engagement:
- No hallucinations: if the answer is not in the context, state exactly:
  "The provided rules do not cover this specific interaction."
- If the player asks about a prior edition (9th, 10th, etc.) or superseded rules, refuse in
  character. Open with "What sort of heresy is this?" and state that only 11th edition is in scope.
- Citation: always cite the section header or page index from the provided text.
- Logic: use step-by-step reasoning to resolve complex interactions.
- Tone: stoic, analytical, yet helpful - like a Primarch reviewing a battle plan.
- Formatting: use Markdown. Bold key terms (e.g., **Battle-shock test**)."""


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    page: int | None
    section_hint: str | None
    source: str | None
    distance: float | None = None


def format_context(chunks: list[RetrievedChunk]) -> str:
    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        citation_parts = []
        if chunk.section_hint:
            citation_parts.append(chunk.section_hint)
        if chunk.page is not None:
            citation_parts.append(f"page {chunk.page}")
        if chunk.source:
            citation_parts.append(chunk.source)
        citation = " | ".join(citation_parts) or f"chunk {index}"

        blocks.append(f"### Context {index} ({citation})\n{chunk.text.strip()}")
    return "\n\n".join(blocks)


def build_user_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    context = format_context(chunks)
    return f"""Use ONLY the rules below to answer the player's question.

## Rules context
{context}

## Player question
{query}

Answer with citations. If the context is insufficient, say so explicitly."""


def build_cache_key(query: str) -> str:
    return query.strip().lower()


def is_legacy_edition_query(query: str) -> bool:
    """True when the player is asking about a superseded edition or old rules corpus."""
    return bool(_LEGACY_EDITION_RE.search(query))


def legacy_edition_refusal() -> str:
    return LEGACY_EDITION_REFUSAL
