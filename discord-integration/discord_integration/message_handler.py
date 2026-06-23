"""Pure message handling logic for Discord (testable without discord.py)."""

from __future__ import annotations

import re

from discord_integration.settings import DiscordSettings

_MENTION_PATTERN = re.compile(r"<@!?\d+>")
_TEXT_MENTION_PATTERN = re.compile(r"@roboto-guilliman|@roboto\b", re.IGNORECASE)

_TOO_SHORT_REPLY = "Ask a rules question after mentioning me (at least a few words)."
_RATE_LIMIT_REPLY = "Too many questions too quickly. Please wait a minute and try again."


def parse_id_list(raw: str) -> set[int]:
    if not raw.strip():
        return set()
    return {int(item.strip()) for item in raw.split(",") if item.strip()}


def guild_allowed(guild_id: int | None, settings: DiscordSettings) -> bool:
    allowed = parse_id_list(settings.discord_allowed_guild_ids)
    if not allowed:
        return True
    return guild_id is not None and guild_id in allowed


def channel_allowed(channel_id: int, settings: DiscordSettings) -> bool:
    allowed = parse_id_list(settings.discord_allowed_channel_ids)
    if not allowed:
        return True
    return channel_id in allowed


def bot_is_mentioned(message_content: str, raw_mentions: list[int], bot_user_id: int) -> bool:
    if bot_user_id in raw_mentions:
        return True
    return bool(_TEXT_MENTION_PATTERN.search(message_content or ""))


def strip_bot_mention(content: str, bot_user_id: int) -> str:
    cleaned = content.replace(f"<@{bot_user_id}>", "").replace(f"<@!{bot_user_id}>", "")
    cleaned = _MENTION_PATTERN.sub("", cleaned)
    cleaned = _TEXT_MENTION_PATTERN.sub("", cleaned)
    return " ".join(cleaned.split()).strip()


def should_process_message(
    *,
    author_is_bot: bool,
    bot_is_mentioned: bool,
    settings: DiscordSettings,
) -> bool:
    if author_is_bot:
        return False
    if not settings.discord_require_mention:
        return True
    return bot_is_mentioned


def validate_query(query: str) -> str | None:
    if len(query) < 3:
        return _TOO_SHORT_REPLY
    return None
