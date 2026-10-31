"""API key authentication with rate limiting tiers.

Tier 0: Anonymous - 60 req/min, 1000 req/day
Tier 1: API Key - 300 req/min, 10000 req/day
Tier 2: Premium - 1000 req/min, 100000 req/day
"""

import hashlib
import logging
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

from sokodata.config import DB_PATH

log = logging.getLogger(__name__)

AUTH_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_keys (
    id          TEXT PRIMARY KEY,
    key_hash    TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    tier        INTEGER DEFAULT 0,          -- 0=anonymous, 1=keyed, 2=premium
    created_at  TEXT NOT NULL,
    last_used   TEXT,
    enabled     INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_keys_hash ON api_keys(key_hash);
"""

# Tier limits: (req_per_min, req_per_day)
TIER_LIMITS = {
    0: (60, 1000),  # Anonymous
    1: (300, 10000),  # API Key
    2: (1000, 100000),  # Premium
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class AuthContext:
    tier: int
    key_id: str | None
    rate_limit_min: int
    rate_limit_day: int


# Configurable database path
_auth_db_path = str(DB_PATH)


def set_auth_db_path(path: str) -> None:
    global _auth_db_path
    _auth_db_path = path


def _get_db_path() -> str:
    return _auth_db_path


def init_auth_db(db_path: Path | str | None = None) -> None:
    path = db_path or _auth_db_path
    conn = sqlite3.connect(path)
    try:
        conn.executescript(AUTH_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def create_api_key(
    name: str = "", tier: int = 1, db_path: Path | str | None = None
) -> tuple[str, str]:
    """Create a new API key. Returns (key_id, raw_key)."""
    path = db_path or _auth_db_path
    raw_key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hash_key(raw_key)
    key_id = secrets.token_urlsafe(16)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "INSERT INTO api_keys (id, key_hash, name, tier, created_at) VALUES (?, ?, ?, ?, ?)",
            (key_id, key_hash, name, tier, time.strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("Created API key %s (tier %d) for %s", key_id, tier, name)
    return key_id, raw_key


def verify_api_key(raw_key: str, db_path: Path | str | None = None) -> tuple[int, str] | None:
    """Verify API key, return (tier, key_id) or None if invalid."""
    key_hash = hash_key(raw_key)
    path = db_path or _auth_db_path
    conn = sqlite3.connect(path)
    try:
        row = conn.execute(
            "SELECT tier, id FROM api_keys WHERE key_hash=? AND enabled=1",
            (key_hash,),
        ).fetchone()
        if row:
            tier, key_id = row
            conn.execute(
                "UPDATE api_keys SET last_used=datetime('now') WHERE id=?",
                (key_id,),
            )
            conn.commit()
            return tier, key_id
    finally:
        conn.close()
    return None


# Simple in-memory rate limiter (per process)
# For production, use Redis or similar
_rate_limit_cache: dict[str, list[float]] = {}  # identity -> [timestamps]
_RATE_LIMIT_MAX_IDENTITIES = 50_000  # guard against memory growth from IP churn


def check_rate_limit(identity: str, tier: int) -> bool:
    """Check if a request from *identity* is within rate limits.

    Callers choose the identity: an API key id, or an "ip:<host>" string
    for anonymous traffic.
    """
    now = time.time()
    min_limit, day_limit = TIER_LIMITS.get(tier, TIER_LIMITS[0])

    if len(_rate_limit_cache) > _RATE_LIMIT_MAX_IDENTITIES:
        for stale in list(_rate_limit_cache)[: _RATE_LIMIT_MAX_IDENTITIES // 5]:
            _rate_limit_cache.pop(stale, None)

    if identity not in _rate_limit_cache:
        _rate_limit_cache[identity] = []

    # Clean old timestamps
    cutoff_min = now - 60
    cutoff_day = now - 86400
    _rate_limit_cache[identity] = [ts for ts in _rate_limit_cache[identity] if ts > cutoff_day]

    # Check limits
    recent_min = sum(1 for ts in _rate_limit_cache[identity] if ts > cutoff_min)
    recent_day = len(_rate_limit_cache[identity])

    if recent_min >= min_limit or recent_day >= day_limit:
        return False

    _rate_limit_cache[identity].append(now)
    return True


async def get_auth_context(
    request: Request,
    api_key: str | None = Depends(api_key_header),
) -> AuthContext:
    if api_key:
        verified = verify_api_key(api_key)
        if verified:
            tier, key_id = verified
            if not check_rate_limit(f"key:{key_id}", tier):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            return AuthContext(
                tier=tier,
                key_id=key_id,
                rate_limit_min=TIER_LIMITS[tier][0],
                rate_limit_day=TIER_LIMITS[tier][1],
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid API key")

    # Anonymous: rate limit per client IP, not one global bucket
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"ip:{client_ip}", 0):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return AuthContext(
        tier=0,
        key_id=None,
        rate_limit_min=TIER_LIMITS[0][0],
        rate_limit_day=TIER_LIMITS[0][1],
    )


def require_tier(min_tier: int):
    """Dependency to require minimum tier."""

    async def checker(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.tier < min_tier:
            raise HTTPException(status_code=403, detail=f"Requires tier {min_tier}+")
        return ctx

    return checker
