"""Tests for WhatsApp answer formatting."""

from roboto_guilliman.prompts import RetrievedChunk
from whatsapp_integration.formatter import format_for_whatsapp


def test_format_for_whatsapp_bold_and_footer():
    chunks = [
        RetrievedChunk(
            text="Battle-shock tests happen in the Command phase.",
            page=45,
            section_hint="Command Phase",
            rule_number="08.03",
            source="Core Rules",
            figure_description=None,
            distance=0.9,
        )
    ]
    rendered = format_for_whatsapp("A **Battle-shock test** applies.", chunks=chunks)
    assert "*Battle-shock test*" in rendered
    assert "_Source: Core Rules_" in rendered


def test_format_for_whatsapp_truncates_long_answers():
    rendered = format_for_whatsapp("x" * 2000)
    assert len(rendered) == 1600
    assert rendered.endswith("...")
