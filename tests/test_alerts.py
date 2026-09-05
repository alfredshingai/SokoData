"""Tests for the Telegram digest: formatting, escaping, skip behavior."""

import json
from unittest import mock

import pytest

from sokodata.alerts import telegram

MOVERS = [
    {"market_id": 1, "market": "Marula", "commodity_id": 1, "commodity": "Fish (kapenta)",
     "unit": "KG", "prev_date": "2026-01-15", "prev_usd": 6.1, "last_date": "2026-05-15",
     "last_usd": 10.53, "pct_change": 72.62},
    {"market_id": 2, "market": "Gokwe", "commodity_id": 2, "commodity": "Maize meal",
     "unit": "KG", "prev_date": "2026-01-15", "prev_usd": 0.7, "last_date": "2026-05-15",
     "last_usd": 0.63, "pct_change": -10.0},
]

ANOMALIES = [
    {"market_id": 3, "market": "Tongogara Refugee Camp 2", "commodity_id": 3,
     "commodity": "Oil (vegetable)", "unit": "L", "date": "2026-05-15", "usdprice": 2.22,
     "recent_median_usd": 1.51, "z": 47.89, "baseline_points": 10},
]


def test_format_digest_contains_rising_and_falling():
    msg = telegram.format_digest(MOVERS, ANOMALIES, "2026-05-15")
    assert "Fish (kapenta)" in msg and "+73%" in msg
    assert "Maize meal" in msg and "-10%" in msg
    assert "above the $1.51 recent norm" in msg
    assert "2026-05-15" in msg
    assert "sokodata.onrender.com" in msg


def test_format_digest_escapes_html_in_data_fields():
    tricky = [dict(MOVERS[0], market="A<b> & friends")]
    msg = telegram.format_digest(tricky, [])
    assert "A<b> & friends" not in msg
    assert "A&lt;b&gt; &amp; friends" in msg


def test_format_digest_empty_data_is_polite():
    msg = telegram.format_digest([], [])
    assert "No notable price movements" in msg


def test_format_digest_respects_telegram_length():
    many = [dict(MOVERS[0], market=f"Market {i}") for i in range(20)]
    msg = telegram.format_digest(many, [], "2026-05-15")
    assert len(msg) <= telegram.MAX_MESSAGE


def test_run_skips_without_secrets(capsys):
    with mock.patch.dict("os.environ", {}, clear=True):
        assert telegram.run() == 0  # exits cleanly, sends nothing


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_send_message_posts_to_bot_api():
    with mock.patch.object(
        telegram.urllib.request, "urlopen", return_value=_FakeResponse({"ok": True})
    ) as fake:
        telegram.send_message("TOKEN", "@soko_prices", "hello")
        req = fake.call_args.args[0]
        assert "api.telegram.org/botTOKEN/sendMessage" in req.full_url
        body = json.loads(req.data)
        assert body["chat_id"] == "@soko_prices"
        assert body["parse_mode"] == "HTML"


def test_send_message_raises_on_api_error():
    with mock.patch.object(
        telegram.urllib.request, "urlopen", return_value=_FakeResponse({"ok": False})
    ):
        with pytest.raises(RuntimeError, match="Telegram API error"):
            telegram.send_message("TOKEN", "@soko_prices", "hello")
