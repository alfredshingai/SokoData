"""WhatsApp Cloud API webhook: Meta verification + incoming message handler."""

import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from sokodata.alerts import whatsapp

log = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])


@router.get("/webhooks/whatsapp")
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


@router.post("/webhooks/whatsapp")
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
