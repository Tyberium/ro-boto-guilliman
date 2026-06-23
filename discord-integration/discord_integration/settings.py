"""Discord integration settings loaded from environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DiscordSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    discord_bot_token: str = ""
    discord_require_mention: bool = True
    discord_allowed_guild_ids: str = ""
    discord_allowed_channel_ids: str = ""
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60


@lru_cache
def get_discord_settings() -> DiscordSettings:
    return DiscordSettings()
