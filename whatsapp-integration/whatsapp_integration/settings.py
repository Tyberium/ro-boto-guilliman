"""WhatsApp integration settings loaded from environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WhatsappSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    whapi_enabled: bool = False
    whapi_token: str = ""
    whapi_base_url: str = "https://gate.whapi.cloud"
    whapi_webhook_secret: str = ""
    whatsapp_require_mention: bool = True
    whatsapp_allow_dm_without_mention: bool = False
    whatsapp_allowed_group_ids: str = ""
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60


@lru_cache
def get_whatsapp_settings() -> WhatsappSettings:
    return WhatsappSettings()
