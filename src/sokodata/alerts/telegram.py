"""Telegram daily digest: pull insights from the SokoData API, post to a channel.

Designed to run from a GitHub Actions cron job. Required environment:

    TELEGRAM_BOT_TOKEN  — from @BotFather
    TELEGRAM_CHAT_ID    — channel username ("@soko_prices") or numeric chat id

If either is missing the script exits 0 without sending, so CI on forks
without secrets stays green. Override the API location with SOKODATA_API_URL
(default: the public deployment).
"""

import html
import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)

API_BASE = os.environ.get("SOKODATA_API_URL", "https://sokodata.onrender.com")
REQUEST_TIMEOUT = 60
MAX_MESSAGE = 4000  # Telegram allows 4096; leave headroom
TOP_MOVERS = 4
TOP_ANOMALIES = 3


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "sokodata-alerts/0.1"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.load(resp)


def _fmt_mover(m: dict) -> str:
    return (
        f"• <b>{html.escape(m['commodity'])}</b> at {html.escape(m['market'])}: "
        f"${m['prev_usd']:,.2f} → ${m['last_usd']:,.2f} / {html.escape(m['unit'])} "
        f"(<b>{m['pct_change']:+.0f}%</b>)"
    )


def _fmt_anomaly(a: dict) -> str:
    direction = "above" if a["z"] > 0 else "below"
    return (
        f"• <b>{html.escape(a['commodity'])}</b> at {html.escape(a['market'])}: "
        f"${a['usdprice']:,.2f} / {html.escape(a['unit'])} "
        f"({direction} the ${a['recent_median_usd']:,.2f} recent norm)"
    )


def format_digest(movers: list[dict], anomalies: list[dict], date_iso: str | None = None) -> str:
    """Render the channel message. HTML parse mode; escapes all data fields."""
    lines = ["🌾 <b>SokoData — Zimbabwe food-price digest</b>"]
    if date_iso:
        lines.append(f"<i>{html.escape(date_iso)}</i>")
    lines.append("")

    rising = [m for m in movers if m["pct_change"] > 0][:TOP_MOVERS]
    falling = [m for m in movers if m["pct_change"] < 0][:TOP_MOVERS]
    if rising or falling:
        lines.append("📈 <b>Biggest movers (trailing window)</b>")
        lines += [_fmt_mover(m) for m in rising + falling]
        lines.append("")

    if anomalies:
        lines.append("🚨 <b>Unusual prices (vs 24-month norm)</b>")
        lines += [_fmt_anomaly(a) for a in anomalies[:TOP_ANOMALIES]]
        lines.append("")

    if not rising and not falling and not anomalies:
        lines.append("No notable price movements in this window.")

    lines.append(
        f'Data: WFP via HDX · <a href="{html.escape(API_BASE)}">sokodata.onrender.com</a>'
    )
    message = "\n".join(lines)
    if len(message) > MAX_MESSAGE:  # trim defensively; lists are already capped
        message = message[: MAX_MESSAGE - 1] + "…"
    return message


def send_message(token: str, chat_id: str, text: str) -> None:
    """Post to a Telegram chat via the Bot API. Raises on API-level errors."""
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        result = json.load(resp)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")
    log.info("message sent to %s", chat_id)


def run() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set; skipping digest")
        return 0

    movers = fetch_json(f"{API_BASE}/v1/insights/movers?window_days=90&limit=10")
    anomalies = fetch_json(f"{API_BASE}/v1/insights/anomalies?limit=5")
    coverage = fetch_json(f"{API_BASE}/health")["coverage"]
    message = format_digest(movers, anomalies, coverage.get("last_date"))

    send_message(token, chat_id, message)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    raise SystemExit(run())
