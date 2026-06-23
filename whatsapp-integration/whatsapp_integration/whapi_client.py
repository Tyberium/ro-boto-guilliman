"""whapi.cloud client for sending WhatsApp replies."""

from __future__ import annotations

import logging

import httpx

from whatsapp_integration.settings import WhatsappSettings

logger = logging.getLogger(__name__)


class WhapiClient:
    def __init__(self, settings: WhatsappSettings) -> None:
        self.settings = settings
        self.base_url = settings.whapi_base_url.rstrip("/")
        self.token = settings.whapi_token

    def send_text(self, to: str, body: str, *, typing_time: int = 2) -> None:
        if not self.token:
            raise RuntimeError("WHAPI_TOKEN is not configured.")

        url = f"{self.base_url}/messages/text"
        payload = {"to": to, "body": body, "typing_time": typing_time}
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}",
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()

        logger.info("Sent WhatsApp reply to %s (%s chars)", to[:24], len(body))
