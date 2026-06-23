"""Shared rules Q&A pipeline for HTTP and messaging integrations."""

from __future__ import annotations

from roboto_guilliman.gemini_client import GeminiArbiter
from roboto_guilliman.prompts import RetrievedChunk, is_legacy_edition_query, legacy_edition_refusal
from roboto_guilliman.retriever import ChatHistoryCache, RulesRetriever


def run_ask(
    query: str,
    *,
    retriever: RulesRetriever,
    cache: ChatHistoryCache,
    arbiter: GeminiArbiter,
    use_cache: bool = True,
) -> tuple[str, bool, list[RetrievedChunk]]:
    """Return answer text, cache-hit flag, and retrieved chunks."""
    if is_legacy_edition_query(query):
        return legacy_edition_refusal(), False, []

    if use_cache:
        cached_answer = cache.get(query)
        if cached_answer:
            return cached_answer, True, []

    chunks = retriever.retrieve(query)
    answer = arbiter.answer(query, chunks)

    if use_cache:
        cache.put(query, answer)

    return answer, False, chunks
