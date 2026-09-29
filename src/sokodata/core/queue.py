"""Simple SQLite-based task queue with retries and dead-letter support.

Designed for scraper tasks: fetch_url, parse_html, extract_pdf.
"""

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sokodata.datasets.markets.store import connect

log = logging.getLogger(__name__)

QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS task_queue (
    id          TEXT PRIMARY KEY,
    task_type   TEXT NOT NULL,          -- 'fetch_html', 'fetch_pdf', 'scrape_rbz', etc.
    payload     TEXT NOT NULL,          -- JSON payload
    priority    INTEGER DEFAULT 0,      -- higher = more urgent
    status      TEXT DEFAULT 'pending', -- 'pending', 'running', 'done', 'failed', 'dead'
    attempts    INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    created_at  TEXT NOT NULL,
    started_at  TEXT,
    finished_at TEXT,
    error       TEXT,
    result      TEXT                    -- JSON result
);
CREATE INDEX IF NOT EXISTS idx_queue_status_priority ON task_queue(status, priority DESC, created_at);
CREATE INDEX IF NOT EXISTS idx_queue_dead ON task_queue(status) WHERE status = 'dead';
"""


@dataclass
class Task:
    id: str
    task_type: str
    payload: dict
    priority: int = 0
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 3
    created_at: str = ""
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    result: dict | None = None


def init_queue(db_path: Path | str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(QUEUE_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def enqueue(db_path: Path | str, task_type: str, payload: dict, priority: int = 0, max_attempts: int = 3) -> str:
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO task_queue (id, task_type, payload, priority, max_attempts, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task_id, task_type, json.dumps(payload), priority, max_attempts, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("enqueued %s:%s (priority=%d)", task_type, task_id[:8], priority)
    return task_id


def dequeue(db_path: Path | str, worker_id: str, limit: int = 10) -> list[Task]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT * FROM task_queue
               WHERE status = 'pending'
               ORDER BY priority DESC, created_at
               LIMIT ?""",
            (limit,),
        ).fetchall()
        if not rows:
            return []
        task_ids = [r["id"] for r in rows]
        placeholders = ",".join("?" * len(task_ids))
        conn.execute(
            f"""UPDATE task_queue SET status='running', started_at=?, attempts=attempts+1
                WHERE id IN ({placeholders})""",
            [datetime.utcnow().isoformat()] + task_ids,
        )
        conn.commit()
        return [Task(**dict(r)) for r in rows]
    finally:
        conn.close()


def complete(db_path: Path | str, task_id: str, result: dict | None = None) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """UPDATE task_queue SET status='done', finished_at=?, result=? WHERE id=?""",
            (datetime.utcnow().isoformat(), json.dumps(result) if result else None, task_id),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("task %s completed", task_id[:8])


def fail(db_path: Path | str, task_id: str, error: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT attempts, max_attempts FROM task_queue WHERE id=?", (task_id,)).fetchone()
        if not row:
            return
        attempts, max_attempts = row
        if attempts >= max_attempts:
            conn.execute(
                """UPDATE task_queue SET status='dead', finished_at=?, error=? WHERE id=?""",
                (datetime.utcnow().isoformat(), error, task_id),
            )
            log.warning("task %s moved to dead letter after %d attempts: %s", task_id[:8], attempts, error)
        else:
            conn.execute(
                """UPDATE task_queue SET status='pending', error=? WHERE id=?""",
                (error, task_id),
            )
            log.info("task %s failed (attempt %d/%d): %s", task_id[:8], attempts, max_attempts, error)
        conn.commit()
    finally:
        conn.close()


def dead_letter(db_path: Path | str, limit: int = 100) -> list[Task]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM task_queue WHERE status='dead' ORDER BY finished_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [Task(**dict(r)) for r in rows]
    finally:
        conn.close()


def retry_dead(db_path: Path | str, task_id: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """UPDATE task_queue SET status='pending', attempts=0, error=NULL, finished_at=NULL WHERE id=?""",
            (task_id,),
        )
        conn.commit()
    finally:
        conn.close()
    log.info("task %s retried from dead letter", task_id[:8])