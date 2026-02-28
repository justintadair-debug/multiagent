"""Task queue and shared memory for the multi-agent system."""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "multiagent.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at   TEXT DEFAULT (datetime('now')),
                assigned_to  TEXT NOT NULL,
                task_type    TEXT NOT NULL,
                payload      TEXT,
                status       TEXT DEFAULT 'pending',
                result       TEXT,
                attempts     INTEGER DEFAULT 0,
                updated_at   TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                agent      TEXT NOT NULL,
                key        TEXT NOT NULL,
                value      TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def enqueue_task(assigned_to: str, task_type: str, payload: dict) -> int:
    init_db()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (assigned_to, task_type, payload) VALUES (?, ?, ?)",
            (assigned_to, task_type, json.dumps(payload))
        )
        conn.commit()
        return cur.lastrowid


def get_pending_tasks(assigned_to: str) -> list:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE assigned_to = ? AND status = 'pending' ORDER BY created_at ASC",
            (assigned_to,)
        ).fetchall()
        return [dict(r) for r in rows]


def update_task(task_id: int, status: str, result: str = None):
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET status = ?, result = ?, updated_at = ?, attempts = attempts + 1 WHERE id = ?",
            (status, result, datetime.now().isoformat(), task_id)
        )
        conn.commit()


def get_task(task_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None


def write_memory(agent: str, key: str, value: str):
    init_db()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO memory (agent, key, value) VALUES (?, ?, ?)",
            (agent, key, value)
        )
        conn.commit()


def read_memory(agent: str, key: str) -> str | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM memory WHERE agent = ? AND key = ? ORDER BY created_at DESC LIMIT 1",
            (agent, key)
        ).fetchone()
        return row["value"] if row else None


def list_tasks(limit: int = 20) -> list:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def mark_failed(task_id: int, reason: str = "Unknown"):
    """Mark a task as failed with a reason."""
    update_task(task_id, "failed", reason)
