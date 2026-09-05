"""WhatsApp channel: reply to incoming messages with the live price digest.

Uses the official WhatsApp Cloud API (Meta Graph). Free-tier friendly by
design: the bot only *replies* to user-initiated messages (service
conversations, free) instead of pushing template messages (paid).

Environment (set on Render / GitHub):
    WHATSAPP_TOKEN           — Meta access token for the WhatsApp app
    WHATSAPP_PHONE_NUMBER_ID — the sending phone number's ID
    WHATSAPP_VERIFY_TOKEN    — any string; must match what is typed into the
                               Meta webhook configuration screen
"""

import json
import logging
import urllib.request

from sokodata.alerts import telegram

log = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v21.0"
REQUEST_TIMEOUT = 60


def send_text(token: str, phone_number_id: str, to: str, text: str) -> None:
    """Send a plain-text WhatsApp message via the Cloud API."""
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text[: telegram.MAX_MESSAGE]},
        }
    ).encode()
    req = urllib.request.Request(
        f"{GRAPH_URL}/{phone_number_id}/messages",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        result = json.load(resp)
    if "error" in result:
        raise RuntimeError(f"Graph API error: {result['error']}")
    log.info("whatsapp reply sent to %s", to)


def extract_text_messages(payload: dict) -> list[tuple[str, str]]:
    """Pull (sender, text) pairs from a webhook payload, ignoring read statuses."""
    out: list[tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("type") == "text":
                    body = (msg.get("text") or {}).get("body", "").strip()
                    if body:
                        out.append((msg.get("from", ""), body))
    return out


def build_reply(user_text: str) -> str:
    """Compose the reply for an incoming message. Any text gets the digest."""
    lowered = user_text.lower()
    if lowered in {"hi", "hello", "hey", "menu", "help", "start"}:
        return (
            "👋 Welcome to SokoData!\n\n"
            "Send any message (e.g. *prices*) to get today's Zimbabwe food-price "
            "digest: biggest market movers and unusual prices, from WFP open data."
        )
    movers = telegram.fetch_json(f"{telegram.API_BASE}/v1/insights/movers?window_days=90&limit=10")
    anomalies = telegram.fetch_json(f"{telegram.API_BASE}/v1/insights/anomalies?limit=5")
    coverage = telegram.fetch_json(f"{telegram.API_BASE}/health")["coverage"]
    return telegram.format_digest(
        movers, anomalies, coverage.get("last_date"), markup="whatsapp"
    )


def handle_webhook(payload: dict, token: str, phone_number_id: str) -> int:
    """Reply to every text message in a webhook payload. Never raises:
    webhooks must return 200 quickly or Meta redelivers."""
    for sender, body in extract_text_messages(payload):
        try:
            reply = build_reply(body)
            send_text(token, phone_number_id, sender, reply)
        except Exception:
            log.exception("failed to reply to %s", sender)
    return len(extract_text_messages(payload))


__all__ = ["build_reply", "extract_text_messages", "handle_webhook", "send_text"]
