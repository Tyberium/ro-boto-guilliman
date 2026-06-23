"""whapi.cloud webhook for WhatsApp group and DM messages."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from roboto_guilliman.ask_pipeline import run_ask
from roboto_guilliman.config import Settings, get_settings
from whatsapp_integration.formatter import format_for_whatsapp
from whatsapp_integration.mentions import (
    is_group_chat_id,
    should_process_message,
    strip_mention,
)
from whatsapp_integration.rate_limiter import RateLimiter
from whatsapp_integration.settings import WhatsappSettings, get_whatsapp_settings
from whatsapp_integration.whapi_client import WhapiClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])

_TEXT_ONLY_REPLY = (
    "I only answer text rules questions. Try:\n"
    "@roboto-guilliman what happens when a unit fails a Battle-shock test?"
)
_RATE_LIMIT_REPLY = "Too many questions too quickly. Please wait a minute and try again."
_TOO_SHORT_REPLY = "Ask a rules question after @roboto-guilliman (at least a few words)."


class WhapiTextBody(BaseModel):
    body: str = ""


class WhapiMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    from_me: bool = False
    type: str = ""
    chat_id: str = ""
    text: WhapiTextBody | None = None
    from_: str = Field(default="", alias="from")
    from_name: str = ""


class WhapiEvent(BaseModel):
    type: str = ""
    event: str = ""


class WhapiWebhookPayload(BaseModel):
    messages: list[WhapiMessage] = Field(default_factory=list)
    event: WhapiEvent | None = None
    channel_id: str = ""


def get_rate_limiter(
    core: Annotated[Settings, Depends(get_settings)],
    whatsapp: Annotated[WhatsappSettings, Depends(get_whatsapp_settings)],
) -> RateLimiter:
    return RateLimiter(core, whatsapp)


def get_whapi_client(
    whatsapp: Annotated[WhatsappSettings, Depends(get_whatsapp_settings)],
) -> WhapiClient:
    return WhapiClient(whatsapp)


def _validate_webhook_secret(
    request: Request,
    settings: WhatsappSettings,
    secret: str | None,
) -> None:
    if not settings.whapi_webhook_secret:
        return

    query_secret = secret or request.query_params.get("secret")
    if query_secret == settings.whapi_webhook_secret:
        return

    auth_header = request.headers.get("Authorization", "")
    if auth_header == f"Bearer {settings.whapi_webhook_secret}":
        return

    raise HTTPException(status_code=403, detail="Invalid webhook secret.")


def _allowed_group_ids(settings: WhatsappSettings) -> set[str]:
    raw = settings.whatsapp_allowed_group_ids.strip()
    if not raw:
        return set()
    return {item.strip() for item in raw.split(",") if item.strip()}


def _chat_allowed(chat_id: str, settings: WhatsappSettings) -> bool:
    allowed = _allowed_group_ids(settings)
    if not allowed:
        return True
    if not is_group_chat_id(chat_id):
        return True
    return chat_id in allowed


def _process_incoming_message(
    message: WhapiMessage,
    *,
    settings: WhatsappSettings,
    rate_limiter: RateLimiter,
    whapi: WhapiClient,
    state: Any,
) -> None:
    if message.from_me:
        return

    chat_id = message.chat_id.strip()
    if not chat_id:
        return

    if not _chat_allowed(chat_id, settings):
        logger.info("Ignoring message from non-allowlisted group %s", chat_id[:24])
        return

    body = (message.text.body if message.text else "").strip()
    sender = message.from_ or "unknown"

    if message.type != "text":
        if body:
            return
        whapi.send_text(chat_id, _TEXT_ONLY_REPLY)
        return

    if not body:
        return

    if not should_process_message(
        body,
        chat_id,
        require_mention=settings.whatsapp_require_mention,
        allow_dm_without_mention=settings.whatsapp_allow_dm_without_mention,
    ):
        logger.info("Ignoring WhatsApp message without @roboto-guilliman from %s", sender[:16])
        return

    query = strip_mention(body)
    if len(query) < 3:
        whapi.send_text(chat_id, _TOO_SHORT_REPLY)
        return

    if not rate_limiter.check(sender):
        whapi.send_text(chat_id, _RATE_LIMIT_REPLY)
        return

    answer, _cached, chunks = run_ask(
        query,
        retriever=state.retriever,
        cache=state.cache,
        arbiter=state.arbiter,
        use_cache=True,
    )
    formatted = format_for_whatsapp(answer, chunks=chunks)
    whapi.send_text(chat_id, formatted)
    logger.info(
        "WhatsApp answer in %s (group=%s, %s chars)",
        chat_id[:24],
        is_group_chat_id(chat_id),
        len(formatted),
    )


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    whapi: Annotated[WhapiClient, Depends(get_whapi_client)],
    secret: Annotated[str | None, Query()] = None,
) -> Response:
    settings = get_whatsapp_settings()
    if not settings.whapi_enabled:
        raise HTTPException(status_code=503, detail="WhatsApp channel is disabled.")

    _validate_webhook_secret(request, settings, secret)

    payload = WhapiWebhookPayload.model_validate(await request.json())
    if payload.event and payload.event.type != "messages":
        return Response(status_code=200)

    state = request.app.state.ro_boto
    for message in payload.messages:
        background_tasks.add_task(
            _process_incoming_message,
            message,
            settings=settings,
            rate_limiter=rate_limiter,
            whapi=whapi,
            state=state,
        )

    return Response(status_code=200)
