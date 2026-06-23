"""Tests for Discord mention and routing logic."""

from discord_integration.message_handler import (
    bot_is_mentioned,
    channel_allowed,
    guild_allowed,
    should_process_message,
    strip_bot_mention,
    validate_query,
)
from discord_integration.settings import DiscordSettings


def test_strip_bot_mention():
    assert strip_bot_mention("<@123456789> When does coherency apply?", 123456789) == (
        "When does coherency apply?"
    )
    assert strip_bot_mention("<@!123456789> coherency?", 123456789) == "coherency?"
    assert (
        strip_bot_mention("@roboto-guilliman When does coherency apply?", 123456789)
        == "When does coherency apply?"
    )


def test_bot_is_mentioned():
    assert bot_is_mentioned("@roboto-guilliman hello", [], 123456789)
    assert bot_is_mentioned("hello", [123456789], 123456789)
    assert not bot_is_mentioned("hello", [], 123456789)


def test_should_process_only_when_mentioned():
    settings = DiscordSettings(discord_require_mention=True)
    assert should_process_message(
        author_is_bot=False,
        bot_is_mentioned=True,
        settings=settings,
    )
    assert not should_process_message(
        author_is_bot=False,
        bot_is_mentioned=False,
        settings=settings,
    )
    assert not should_process_message(
        author_is_bot=True,
        bot_is_mentioned=True,
        settings=settings,
    )


def test_guild_and_channel_allowlists():
    settings = DiscordSettings(
        discord_allowed_guild_ids="111,222",
        discord_allowed_channel_ids="999",
    )
    assert guild_allowed(111, settings)
    assert not guild_allowed(333, settings)
    assert channel_allowed(999, settings)
    assert not channel_allowed(888, settings)


def test_validate_query():
    assert validate_query("ab") is not None
    assert validate_query("When does coherency apply?") is None
