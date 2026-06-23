"""Tests for the whapi.cloud WhatsApp webhook."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from roboto_guilliman.api.main import app
from whatsapp_integration.gateway import (
    WhapiMessage,
    _process_incoming_message,
    get_rate_limiter,
    get_whapi_client,
)
from whatsapp_integration.settings import WhatsappSettings


def _settings(**overrides: object) -> WhatsappSettings:
    defaults = {
        "whapi_enabled": True,
        "whapi_token": "test-token",
        "whapi_webhook_secret": "hook-secret",
        "whatsapp_require_mention": True,
        "whatsapp_allow_dm_without_mention": False,
    }
    defaults.update(overrides)
    return WhatsappSettings(**defaults)


def _group_payload(*, body: str) -> dict[str, object]:
    return {
        "messages": [
            {
                "id": "msg-1",
                "from_me": False,
                "type": "text",
                "chat_id": "120363271212442249@g.us",
                "timestamp": 1713791337,
                "text": {"body": body},
                "from": "447700900123",
                "from_name": "Dave",
            }
        ],
        "event": {"type": "messages", "event": "post"},
        "channel_id": "TEST-CHANNEL",
    }


def test_webhook_rejects_invalid_secret():
    app.state.ro_boto = MagicMock()
    with patch(
        "whatsapp_integration.gateway.get_whatsapp_settings",
        return_value=_settings(),
    ):
        client = TestClient(app)
        response = client.post("/webhook/whatsapp", json=_group_payload(body="@roboto test"))

    assert response.status_code == 403


def test_webhook_accepts_valid_secret_and_returns_200():
    app.state.ro_boto = MagicMock()
    limiter = MagicMock()
    limiter.check.return_value = True
    whapi = MagicMock()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    app.dependency_overrides[get_whapi_client] = lambda: whapi

    with patch(
        "whatsapp_integration.gateway.get_whatsapp_settings",
        return_value=_settings(),
    ):
        with patch("whatsapp_integration.gateway.run_ask") as run_ask:
            run_ask.return_value = ("Battle-shock tests happen in the Command phase.", False, [])
            client = TestClient(app)
            response = client.post(
                "/webhook/whatsapp?secret=hook-secret",
                json=_group_payload(
                    body="@roboto-guilliman When does a unit take a Battle-shock test?"
                ),
            )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    whapi.send_text.assert_called_once()
    assert "Battle-shock" in whapi.send_text.call_args.args[1]


def test_process_incoming_message_ignores_without_mention():
    settings = _settings()
    limiter = MagicMock()
    whapi = MagicMock()
    state = MagicMock()

    _process_incoming_message(
        WhapiMessage.model_validate(_group_payload(body="What is coherency?")["messages"][0]),
        settings=settings,
        rate_limiter=limiter,
        whapi=whapi,
        state=state,
    )

    whapi.send_text.assert_not_called()
    limiter.check.assert_not_called()
