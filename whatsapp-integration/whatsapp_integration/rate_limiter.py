"""Per-sender rate limiting backed by Firestore."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from google.cloud import firestore

from roboto_guilliman.config import Settings, get_settings
from roboto_guilliman.gcp_auth import optional_local_credentials
from whatsapp_integration.settings import WhatsappSettings, get_whatsapp_settings

logger = logging.getLogger(__name__)

COLLECTION = "rate_limits"


class RateLimiter:
    def __init__(
        self,
        core_settings: Settings | None = None,
        whatsapp_settings: WhatsappSettings | None = None,
    ) -> None:
        self.core_settings = core_settings or get_settings()
        self.whatsapp_settings = whatsapp_settings or get_whatsapp_settings()
        credentials = optional_local_credentials()
        self.db = firestore.Client(
            project=self.core_settings.gcp_project_id,
            database=self.core_settings.firestore_database,
            credentials=credentials,
        )
        self.collection = self.db.collection(COLLECTION)

    def check(self, sender_key: str) -> bool:
        """Return True if the sender is within the configured window limit."""
        doc_ref = self.collection.document(_normalize_key(sender_key))
        now = datetime.now(UTC)
        window_seconds = self.whatsapp_settings.rate_limit_window_seconds
        max_requests = self.whatsapp_settings.rate_limit_requests

        snapshot = doc_ref.get()
        if not snapshot.exists:
            doc_ref.set({"window_start": now, "count": 1, "updated_at": now})
            return True

        data = snapshot.to_dict() or {}
        window_start = data.get("window_start", now)
        count = int(data.get("count", 0))

        if hasattr(window_start, "tzinfo") and window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=UTC)

        elapsed = (now - window_start).total_seconds()
        if elapsed >= window_seconds:
            doc_ref.set({"window_start": now, "count": 1, "updated_at": now})
            return True

        if count >= max_requests:
            logger.info("Rate limit exceeded for %s", sender_key[:12])
            return False

        doc_ref.set(
            {"window_start": window_start, "count": count + 1, "updated_at": now},
            merge=True,
        )
        return True


def _normalize_key(sender_key: str) -> str:
    return sender_key.replace("/", "_").replace(":", "_").replace("@", "_")
