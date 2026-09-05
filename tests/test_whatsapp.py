"""Tests for the WhatsApp webhook: verification, parsing, reply flow."""

from unittest import mock

from sokodata.alerts import telegram, whatsapp

MOVERS = [
    {"market_id": 1, "market": "Marula", "commodity_id": 1, "commodity": "Fish (kapenta)",
     "unit": "KG", "prev_date": "2026-01-15", "prev_usd": 6.1, "last_date": "2026-05-15",
     "last_usd": 10.53, "pct_change": 72.62},
]

WEBHOOK_PAYLOAD = {
    "entry": [
        {
            "changes": [
                {
                    "value": {
                        "messages": [
                            {"from": "263771234567", "type": "text",
                             "text": {"body": "prices"}},
                            {"from": "263771234567", "type": "text",
                             "text": {"body": " "}},  # blank -> dropped
                        ],
                        "statuses": [{"status": "delivered"}],  # ignored
                    }
                }
            ]
        }
    ]
}


def test_extract_text_messages_ignores_statuses_and_blanks():
    pairs = whatsapp.extract_text_messages(WEBHOOK_PAYLOAD)
    assert pairs == [("263771234567", "prices")]


def test_format_digest_whatsapp_markup_has_no_html():
    msg = telegram.format_digest(MOVERS, [], "2026-05-15", markup="whatsapp")
    assert "<b>" not in msg and "<a " not in msg and "&amp;" not in msg
    assert "*Fish (kapenta)*" in msg and "*+73%*" in msg
    assert "_2026-05-15_" in msg
    assert "sokodata.onrender.com" in msg


def test_format_digest_unknown_markup_rejected():
    import pytest

    with pytest.raises(ValueError, match="unknown markup"):
        telegram.format_digest(MOVERS, [], markup="markdown")


def test_build_reply_greets_newcomers():
    reply = whatsapp.build_reply("hi")
    assert "Welcome to SokoData" in reply


def test_build_reply_fetches_digest():
    with mock.patch.object(telegram, "fetch_json", side_effect=lambda url: (
        MOVERS if "movers" in url else
        [] if "anomalies" in url else
        {"coverage": {"last_date": "2026-05-15"}}
    )):
        reply = whatsapp.build_reply("prices")
    assert "Fish (kapenta)" in reply and "+73%" in reply


def test_handle_webhook_replies_to_each_sender():
    sent = []

    def fake_fetch(url):
        return (
            MOVERS if "movers" in url else
            [] if "anomalies" in url else
            {"coverage": {"last_date": "2026-05-15"}}
        )

    def fake_send(token, phone_id, to, txt):
        sent.append(to)

    with mock.patch.object(whatsapp, "send_text", side_effect=fake_send):
        with mock.patch.object(whatsapp, "build_reply", return_value="digest!"):
            n = whatsapp.handle_webhook(WEBHOOK_PAYLOAD, "TOKEN", "PHONE_ID")
    assert n == 1
    assert sent == ["263771234567"]


def test_handle_webhook_never_raises_on_send_failure():
    with mock.patch.object(whatsapp, "send_text", side_effect=RuntimeError("network down")):
        with mock.patch.object(whatsapp, "build_reply", return_value="digest!"):
            assert whatsapp.handle_webhook(WEBHOOK_PAYLOAD, "TOKEN", "PHONE_ID") == 1


def test_webhook_verification(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "sekret")
    ok = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "sekret",
            "hub.challenge": "CHALLENGE123",
        },
    )
    assert ok.status_code == 200
    assert ok.text == "CHALLENGE123"

    bad = client.get(
        "/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "wrong"}
    )
    assert bad.status_code == 403


def test_webhook_incoming_unconfigured_returns_ok(client, monkeypatch):
    monkeypatch.delenv("WHATSAPP_TOKEN", raising=False)
    r = client.post("/webhooks/whatsapp", json=WEBHOOK_PAYLOAD)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "handled": 0}


def test_webhook_incoming_configured_replies(client, monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", "TOKEN")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "PHONE_ID")
    with mock.patch.object(whatsapp, "handle_webhook", return_value=1) as handler:
        r = client.post("/webhooks/whatsapp", json=WEBHOOK_PAYLOAD)
    assert r.status_code == 200
    assert r.json() == {"ok": True, "handled": 1}
    handler.assert_called_once()
    assert handler.call_args.args[1:] == ("TOKEN", "PHONE_ID")
