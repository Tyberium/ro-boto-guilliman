"""Parse @roboto-guilliman mentions from WhatsApp message bodies."""

from __future__ import annotations

import re

DEFAULT_MENTION_PATTERN = re.compile(r"@roboto-guilliman|@roboto\b", re.IGNORECASE)
GROUP_CHAT_SUFFIX = "@g.us"


def contains_mention(body: str, *, pattern: re.Pattern[str] | None = None) -> bool:
    return bool((pattern or DEFAULT_MENTION_PATTERN).search(body))


def strip_mention(body: str, *, pattern: re.Pattern[str] | None = None) -> str:
    cleaned = (pattern or DEFAULT_MENTION_PATTERN).sub("", body)
    return " ".join(cleaned.split()).strip()


def is_group_chat_id(chat_id: str) -> bool:
    return chat_id.endswith(GROUP_CHAT_SUFFIX)


def should_process_message(
    body: str,
    chat_id: str,
    *,
    require_mention: bool,
    allow_dm_without_mention: bool,
    mention_pattern: re.Pattern[str] | None = None,
) -> bool:
    if not require_mention:
        return True

    mentioned = contains_mention(body, pattern=mention_pattern)
    if is_group_chat_id(chat_id):
        return mentioned

    return mentioned or allow_dm_without_mention
