"""API key management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sokodata.core.auth import (
    AuthContext,
    create_api_key,
    get_auth_context,
    init_auth_db,
    require_tier,
)

router = APIRouter(tags=["auth"], prefix="/auth")


class CreateKeyRequest(BaseModel):
    name: str
    tier: int = 1  # 1 = standard, 2 = premium


class CreateKeyResponse(BaseModel):
    key_id: str
    key: str
    name: str
    tier: int


class KeyInfo(BaseModel):
    key_id: str
    name: str
    tier: int
    created_at: str
    last_used: str | None
    enabled: bool


@router.post("/keys", response_model=CreateKeyResponse)
def create_key(
    req: CreateKeyRequest,
    ctx: AuthContext = Depends(require_tier(2)),  # Only premium can create keys
):
    """Create a new API key. Requires premium tier."""
    from sokodata.datasets.markets.store import connect as db_connect
    db_path = "data/sokodata.db"
    init_auth_db(db_path)
    key_id, raw_key = create_api_key(db_path, req.name, req.tier)
    return CreateKeyResponse(key_id=key_id, key=raw_key, name=req.name, tier=req.tier)


@router.get("/keys", response_model=list[KeyInfo])
def list_keys(ctx: AuthContext = Depends(require_tier(2))):
    """List all API keys. Requires premium tier."""
    from sokodata.datasets.markets.store import connect as db_connect
    db_path = "data/sokodata.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT id, name, tier, created_at, last_used, enabled FROM api_keys ORDER BY created_at DESC").fetchall()
        return [KeyInfo(**dict(r)) for r in rows]
    finally:
        conn.close()


@router.delete("/keys/{key_id}")
def revoke_key(key_id: str, ctx: AuthContext = Depends(require_tier(2))):
    """Revoke an API key. Requires premium tier."""
    from sokodata.datasets.markets.store import connect as db_connect
    db_path = "data/sokodata.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE api_keys SET enabled=0 WHERE id=?", (key_id,))
        conn.commit()
        if conn.total_changes == 0:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"ok": True}
    finally:
        conn.close()


@router.get("/me", response_model=AuthContext)
def get_current_user(ctx: AuthContext = Depends(get_auth_context)):
    """Get current authenticated context (tier, rate limits)."""
    return ctx