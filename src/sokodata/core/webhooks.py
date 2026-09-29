"""Webhook delivery system for alerts and notifications.

Supports multiple channels: HTTP webhook, Telegram, Slack, Email (via webhook).
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from sokodata.datasets.markets.store import connect as db_connect

log = logging.getLogger(__name__)

WEBHOOK_SCHEMA = """
CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    channel     TEXT NOT NULL,          -- 'http', 'telegram', 'slack', 'email'
    target      TEXT NOT NULL,          -- URL, chat_id, email address
    events      TEXT NOT NULL,          -- JSON array of event types
    secret      TEXT,                   -- HMAC secret for verification
    enabled     INTEGER DEFAULT 1,
    created_at  TEXT NOT NULL,
    last_sent   TEXT,
    retry_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_webhooks_user ON webhook_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_enabled ON webhook_subscriptions(enabled) WHERE enabled = 1;
"""

WEBHOOK_EVENTS = {
    "price_spike",      # price spike detected
    "price_drop",       # significant price drop
    "anomaly_detected", # statistical anomaly
    "new_data",         # new data available
    "etl_complete",     # ETL pipeline completed
    "etl_failed",       # ETL pipeline failed
}


@dataclass
class WebhookSubscription:
    id: str
    user_id: str
    channel: str
    target: str
    events: list[str]
    secret: str | None
    enabled: bool
    created_at: str
    last_sent: str | None
    retry_count: int = 0


def init_webhook_db(db_path: Path | str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(WEBHOOK_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def create_webhook_subscription(
    db_path: Path | str,
    user_id: str,
    channel: str,
    target: str,
    events: list[str],
    secret: str | None = None,
) -> str:
    """Create a new webhook subscription."""
    import secrets
    webhook_id = secrets.token_urlsafe(16)
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO webhook_subscriptions 
               (id, user_id, channel, target, events, secret, enabled, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
            (webhook_id, user_id, channel, target, json.dumps(events), secret, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("Created webhook %s for user %s (%s)", webhook_id, user_id, channel)
    return webhook_id


def list_webhook_subscriptions(db_path: Path | str, user_id: str) -> list[dict]:
    """List all webhook subscriptions for a user."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM webhook_subscriptions WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_webhook_subscription(db_path: Path | str, webhook_id: str, user_id: str) -> bool:
    """Delete a webhook subscription."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM webhook_subscriptions WHERE id=? AND user_id=?",
            (webhook_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


async def send_webhook(
    webhook: WebhookSubscription,
    event: str,
    payload: dict[str, Any],
    timeout: float = 10.0,
) -> bool:
    """Send a webhook notification."""
    if event not in webhook.events:
        return True  # Event not subscribed, skip silently

    payload_with_meta = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "data": payload,
    }

    headers = {"Content-Type": "application/json"}
    if webhook.secret:
        import hmac
        import hashlib
        sig = hmac.new(webhook.secret.encode(), json.dumps(payload_with_meta).encode(), hashlib.sha256).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if webhook.channel == "http":
                response = await client.post(webhook.target, json=payload_with_meta, headers=headers)
                response.raise_for_status()
            elif webhook.channel == "telegram":
                # Telegram Bot API
                chat_id = webhook.target
                text = f"*{event}*\n```json\n{json.dumps(payload, indent=2)[:3000]}\n```"
                await client.post(
                    f"https://api.telegram.org/bot{webhook.secret}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                )
            elif webhook.channel == "slack":
                # Slack webhook
                await client.post(webhook.target, json={"text": f"*{event}*\n```{json.dumps(payload, indent=2)[:3000]}```"})
            elif webhook.channel == "email":
                # Email via webhook (e.g., SendGrid, Mailgun)
                await client.post(webhook.target, json={"to": webhook.target, "subject": f"SokoData Alert: {event}", "text": json.dumps(payload, indent=2)})
            else:
                log.warning("Unknown webhook channel: %s", webhook.channel)
                return False
    except Exception as e:
        log.error("Failed to send webhook %s (%s): %s", webhook.id, webhook.channel, e)
        return False

    return True


async def broadcast_event(
    db_path: Path | str,
    event: str,
    payload: dict[str, Any],
) -> dict[str, int]:
    """Send an event to all subscribed webhooks."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM webhook_subscriptions WHERE enabled=1 AND events LIKE ?",
            (f"%{event}%",),
        ).fetchall()
    finally:
        conn.close()

    webhooks = []
    for row in rows:
        wh = WebhookSubscription(
            id=row["id"],
            user_id=row["user_id"],
            channel=row["channel"],
            target=row["target"],
            events=json.loads(row["events"]),
            secret=row["secret"],
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            last_sent=row["last_sent"],
            retry_count=row["retry_count"] or 0,
        )
        webhooks.append(wh)

    sent = 0
    failed = 0
    for wh in webhooks:
        try:
            ok = await send_webhook(wh, event, payload)
            if ok:
                sent += 1
            else:
                failed += 1
        except Exception as e:
            log.error("Error sending to webhook %s: %s", wh.id, e)
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(webhooks)}