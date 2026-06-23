"""Entry point for the Discord bot process."""

from __future__ import annotations

import asyncio
import logging
import sys

from discord_integration.bot import RobotoGuillimanBot
from discord_integration.rate_limiter import RateLimiter
from discord_integration.settings import get_discord_settings
from roboto_guilliman.api.main import AppState
from roboto_guilliman.config import get_settings


async def _run() -> None:
    core_settings = get_settings()
    discord_settings = get_discord_settings()
    logging.basicConfig(level=core_settings.log_level.upper())
    logger = logging.getLogger(__name__)

    if not discord_settings.discord_bot_token:
        raise SystemExit("DISCORD_BOT_TOKEN is required.")

    logger.info("Initializing rules engine (Firestore + Vertex)...")
    app_state = AppState(core_settings)
    rate_limiter = RateLimiter(core_settings, discord_settings)
    bot = RobotoGuillimanBot(
        app_state=app_state,
        discord_settings=discord_settings,
        rate_limiter=rate_limiter,
    )

    logger.info("Connecting to Discord...")
    async with bot:
        await bot.start(discord_settings.discord_bot_token)


def main() -> None:
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
