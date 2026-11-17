"""会话与消息的 SQLite 持久化。"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "robot.db"
UPLOAD_DIR = DATA_DIR / "uploads"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _db():
    conn = _connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                pinned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                text TEXT NOT NULL DEFAULT '',
                model_text TEXT NOT NULL DEFAULT '',
                attachments TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id);
            """
        )

        # 兼容旧数据库：补充置顶字段。
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(conversations)")
        }
        if "pinned" not in columns:
            conn.execute(
                "ALTER TABLE conversations ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0"
            )


def list_conversations() -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, title, pinned, created_at, updated_at FROM conversations "
            "ORDER BY pinned DESC, updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def create_conversation(title: str) -> str:
    conv_id = uuid.uuid4().hex
    now = _now()
    with _db() as conn:
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now),
        )
    return conv_id


def delete_conversation(conv_id: str) -> None:
    with _db() as conn:
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    shutil.rmtree(UPLOAD_DIR / conv_id, ignore_errors=True)


def touch_conversation(conv_id: str) -> None:
    with _db() as conn:
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (_now(), conv_id),
        )


def set_pinned(conv_id: str, pinned: bool) -> None:
    with _db() as conn:
        conn.execute(
            "UPDATE conversations SET pinned = ? WHERE id = ?",
            (1 if pinned else 0, conv_id),
        )


def add_message(
    conv_id: str,
    role: str,
    text: str,
    model_text: str = "",
    attachments: list[dict] | None = None,
) -> None:
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO messages
                (conversation_id, role, text, model_text, attachments, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                conv_id,
                role,
                text,
                model_text or text,
                json.dumps(attachments or [], ensure_ascii=False),
                _now(),
            ),
        )


def get_messages(conv_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, role, text, model_text, attachments, created_at "
            "FROM messages WHERE conversation_id = ? ORDER BY id",
            (conv_id,),
        ).fetchall()

    messages = []
    for row in rows:
        item = dict(row)
        item["attachments"] = json.loads(item["attachments"] or "[]")
        messages.append(item)
    return messages


def save_upload(conv_id: str, filename: str, data: bytes) -> str:
    """保存上传文件，返回相对 DATA_DIR 的路径。"""
    folder = UPLOAD_DIR / conv_id
    folder.mkdir(parents=True, exist_ok=True)

    name = Path(filename).name
    safe_name = re.sub(r"[^\w.\-一-鿿]", "_", name) or "file"
    stored = folder / f"{uuid.uuid4().hex[:8]}_{safe_name}"
    stored.write_bytes(data)
    return stored.relative_to(DATA_DIR).as_posix()


def make_title(text: str, filenames: list[str]) -> str:
    title = " ".join(text.split())[:20]
    if not title and filenames:
        title = filenames[0][:20]
    return title or "新会话"
