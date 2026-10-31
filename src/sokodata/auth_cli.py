"""Manage API keys from the command line.

The /v1/auth/keys endpoints require a premium key to create keys, so the
first key must be minted on the server:

    python -m sokodata.auth_cli create --name admin --tier 2
    python -m sokodata.auth_cli list
    python -m sokodata.auth_cli revoke <key_id>

The raw key is printed once and only its SHA-256 hash is stored.
"""

import argparse
import sqlite3
import sys

from sokodata.config import DB_PATH
from sokodata.core.auth import create_api_key, init_auth_db


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def main() -> int:
    parser = argparse.ArgumentParser(description="SokoData API key management")
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite warehouse path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="create a new API key")
    p_create.add_argument("--name", default="", help="label for the key")
    p_create.add_argument("--tier", type=int, default=1, choices=[1, 2], help="1=keyed, 2=premium")

    sub.add_parser("list", help="list API keys")

    p_revoke = sub.add_parser("revoke", help="disable an API key by id")
    p_revoke.add_argument("key_id")

    args = parser.parse_args()
    init_auth_db(args.db)

    if args.command == "create":
        key_id, raw_key = create_api_key(name=args.name, tier=args.tier, db_path=args.db)
        print(f"key_id: {key_id}")
        print(f"key:    {raw_key}")
        print("(shown once; only its hash is stored)")
        return 0

    conn = _connect(args.db)
    try:
        if args.command == "list":
            rows = conn.execute(
                "SELECT id, name, tier, created_at, last_used, enabled "
                "FROM api_keys ORDER BY created_at"
            ).fetchall()
            if not rows:
                print("no API keys yet; create one: python -m sokodata.auth_cli create")
            for r in rows:
                state = "active" if r["enabled"] else "disabled"
                print(
                    f"{r['id']}  tier={r['tier']}  {state:<8}  {r['name']!r}  created={r['created_at']}"
                )
            return 0

        if args.command == "revoke":
            cur = conn.execute("UPDATE api_keys SET enabled=0 WHERE id=?", (args.key_id,))
            conn.commit()
            if cur.rowcount == 0:
                print(f"no key with id {args.key_id}", file=sys.stderr)
                return 1
            print(f"revoked {args.key_id}")
            return 0
    finally:
        conn.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
