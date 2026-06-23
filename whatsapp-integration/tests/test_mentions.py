"""Tests for @roboto-guilliman mention parsing."""

from whatsapp_integration.mentions import (
    contains_mention,
    is_group_chat_id,
    should_process_message,
    strip_mention,
)


def test_contains_mention_matches_aliases():
    assert contains_mention("@roboto-guilliman when does coherency apply?")
    assert contains_mention("Hey @roboto can we charge?")
    assert not contains_mention("What is coherency?")


def test_strip_mention_removes_tag():
    assert (
        strip_mention("@roboto-guilliman When does a unit take a Battle-shock test?")
        == "When does a unit take a Battle-shock test?"
    )


def test_group_chat_id_detection():
    assert is_group_chat_id("120363271212442249@g.us")
    assert not is_group_chat_id("447700900123@s.whatsapp.net")


def test_should_process_group_only_with_mention():
    group_id = "120363271212442249@g.us"
    assert should_process_message(
        "@roboto-guilliman coherency?",
        group_id,
        require_mention=True,
        allow_dm_without_mention=False,
    )
    assert not should_process_message(
        "coherency?",
        group_id,
        require_mention=True,
        allow_dm_without_mention=False,
    )


def test_should_process_dm_without_mention_when_allowed():
    dm_id = "447700900123@s.whatsapp.net"
    assert should_process_message(
        "coherency?",
        dm_id,
        require_mention=True,
        allow_dm_without_mention=True,
    )
