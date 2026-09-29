"""Webhook endpoints - WhatsApp Cloud API + subscription management."""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from sokodata.core.auth import get_auth_context
from sokodata.core.webhooks import (
    WebhookSubscription,
    create_webhook_subscription,
    delete_webhook_subscription,
    init_webhook_db,
    list_webhook_subscriptions,
)

from sokodata.alerts import whatsapp

log = logging.getLogger(__name__)

# WhatsApp Cloud API webhook (no /v1 prefix, at /webhooks/whatsapp)
whatsapp_router = APIRouter(tags=["webhooks"])


@whatsapp_router.get("/webhooks/whatsapp")
def verify(request: Request):
    """Meta's one-time webhook verification handshake."""
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token")
        and params.get("hub.verify_token") == os.environ.get("WHATSAPP_VERIFY_TOKEN")
    ):
        return PlainTextResponse(params.get("hub.challenge", ""))
    return PlainTextResponse("forbidden", status_code=403)


@whatsapp_router.post("/webhooks/whatsapp")
async def incoming(request: Request):
    """Handle Meta webhook deliveries. Always 200 so Meta doesn't redeliver;
    failures are logged instead. Skips silently when not configured."""
    payload = await request.json()
    token = os.environ.get("WHATSAPP_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_number_id:
        log.info("whatsapp webhook received but not configured; ignoring")
        return {"ok": True, "handled": 0}
    handled = whatsapp.handle_webhook(payload, token, phone_number_id)
    return {"ok": True, "handled": handled}


# Webhook subscription management (with /v1/webhooks prefix)
router = APIRouter(tags=["webhooks"], prefix="/v1/webhooks")


class CreateWebhookRequest(BaseModel):
    channel: str  # http, telegram, slack, email
    target: str   # URL, chat_id, email
    events: list[str]
    secret: str | None = None


class WebhookResponse(BaseModel):
    id: str
    user_id: str
    channel: str
    target: str
    events: list[str]
    secret: str | None
    enabled: bool
    created_at: str
    last_sent: str | None
    retry_count: int


@router.post("", response_model=dict)
def create_webhook(
    req: dict,
    ctx = Depends(get_auth_context),
):
    """Create a new webhook subscription."""
    from sokodata.core.webhooks import create_webhook_subscription
    db_path = "data/sokodata.db"
    init_webhook_db(db_path)
    webhook_id = create_webhook_subscription(
        "data/sokodata.db", 
        "anonymous", 
        req.get("channel"), 
        req.get("target"), 
        req.get("events", []), 
        req.get("secret")
    )
    return {"id": webhook_id, "ok": True}


@router.get("", response_model=list[dict])
def list_webhooks(ctx = Depends(get_auth_context)):
    """List all webhook subscriptions for the current user."""
    from sokodata.core.webhooks import list_webhook_subscriptions
    subs = list_webhook_subscriptions("data/sokodata.db", ctx.key_id or "anonymous")
    return subs


@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: str, ctx = Depends(get_auth_context)):
    """Delete a webhook subscription."""
    from sokodata.core.webhooks import delete_webhook_subscription
    ok = delete_webhook_subscription("data/sokodata.db", webhook_id, ctx.key_id or "anonymous")
    if not ok:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"ok": True}


@router.post("/test")
async def test_webhook(
    channel: str,
    target: str,
    event: str = "test_event",
    payload: dict = None,
    ctx = Depends(get_auth_context),
):
    """Send a test webhook."""
    from sokodata.core.webhooks import WebhookSubscription, send_webhook
    wh = WebhookSubscription(
        id="test",
        user_id="test",
        channel=channel,
        target=target,
        events=[event],
        secret=None,
        enabled=True,
        created_at="",
        last_sent=None,
        retry_count=0,
    )
    payload = payload or {"message": "This is a test webhook from SokoData"}
    ok = await send_webhook(wh, event, payload or {})
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send test webhook")
    return {"ok": True}