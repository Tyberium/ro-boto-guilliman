"""Discord bot client for roboto-guilliman."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord

from discord_integration.formatter import format_for_discord
from discord_integration.message_handler import (
    _RATE_LIMIT_REPLY,
    bot_is_mentioned,
    channel_allowed,
    guild_allowed,
    should_process_message,
    strip_bot_mention,
    validate_query,
)
from discord_integration.rate_limiter import RateLimiter
from discord_integration.settings import DiscordSettings
from roboto_guilliman.ask_pipeline import run_ask

if TYPE_CHECKING:
    from roboto_guilliman.api.main import AppState

logger = logging.getLogger(__name__)

_ERROR_REPLY = "Sorry, I hit an error answering that. Check the bot logs and try again."


class RobotoGuillimanBot(discord.Client):
    def __init__(
        self,
        *,
        app_state: AppState,
        discord_settings: DiscordSettings,
        rate_limiter: RateLimiter,
    ) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.app_state = app_state
        self.discord_settings = discord_settings
        self.rate_limiter = rate_limiter

    async def on_ready(self) -> None:
        logger.info("Discord bot online as %s (id=%s)", self.user, self.user.id if self.user else "?")
        logger.info(
            "Gateway intents: message_content=%s messages=%s",
            self.intents.message_content,
            self.intents.messages,
        )
        if not self.intents.message_content:
            logger.warning("message_content intent is disabled in code")

    async def on_message(self, message: discord.Message) -> None:
        if self.user is None or message.author.id == self.user.id:
            return

        mentioned = bot_is_mentioned(message.content or "", message.raw_mentions, self.user.id)
        if not mentioned:
            return

        guild_id = message.guild.id if message.guild else None
        if not guild_allowed(guild_id, self.discord_settings):
            logger.info("Ignored mention from guild %s (not allowlisted)", guild_id)
            return
        if not channel_allowed(message.channel.id, self.discord_settings):
            logger.info("Ignored mention in channel %s (not allowlisted)", message.channel.id)
            return

        if not should_process_message(
            author_is_bot=message.author.bot,
            bot_is_mentioned=mentioned,
            settings=self.discord_settings,
        ):
            return

        logger.info(
            "Processing mention from %s in #%s (raw_mentions=%s content_len=%s)",
            message.author.display_name,
            getattr(message.channel, "name", message.channel.id),
            message.raw_mentions,
            len(message.content or ""),
        )

        try:
            await message.add_reaction("📖")
            await self._answer_message(message, guild_id=guild_id)
        except Exception:
            logger.exception("Failed to handle Discord mention from %s", message.author.id)
            try:
                await message.reply(_ERROR_REPLY, mention_author=False)
            except discord.HTTPException:
                logger.exception("Could not send Discord error reply")

    async def _answer_message(self, message: discord.Message, *, guild_id: int | None) -> None:
        query = strip_bot_mention(message.content or "", self.user.id)
        validation_error = validate_query(query)
        if validation_error:
            await message.reply(validation_error, mention_author=False)
            return

        sender_key = f"discord:{message.author.id}"
        allowed = await asyncio.to_thread(self.rate_limiter.check, sender_key)
        if not allowed:
            await message.reply(_RATE_LIMIT_REPLY, mention_author=False)
            return

        async with message.channel.typing():
            answer, _cached, chunks = await asyncio.to_thread(
                run_ask,
                query,
                retriever=self.app_state.retriever,
                cache=self.app_state.cache,
                arbiter=self.app_state.arbiter,
                use_cache=True,
            )

        formatted = format_for_discord(answer, chunks=chunks)
        await message.reply(formatted, mention_author=False)
        logger.info(
            "Discord answer in #%s (guild=%s, %s chars)",
            getattr(message.channel, "name", message.channel.id),
            guild_id,
            len(formatted),
        )
