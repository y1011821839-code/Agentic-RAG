"""
SQLite 会话存储 — 对话持久化
"""
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional


class SessionStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "sessions.db"
            )
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT DEFAULT '新对话',
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id)")

    # =========== 会话 ===========

    def create_session(self, title: str = "新对话") -> str:
        session_id = uuid.uuid4().hex[:12]
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title) VALUES (?, ?)",
                (session_id, title)
            )
        return session_id

    def list_sessions(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    def delete_session(self, session_id: str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def touch_session(self, session_id: str):
        """更新会话的更新时间"""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE sessions SET updated_at = datetime('now', 'localtime') WHERE id = ?",
                (session_id,)
            )

    # =========== 消息 ===========

    def add_message(self, session_id: str, role: str, content: str):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content)
            )
        self.touch_session(session_id)

    def get_messages(self, session_id: str) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            ).fetchall()
        return [
            {"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]}
            for r in rows
        ]

    def save_exchange(self, session_id: str, question: str, answer: str):
        """保存一轮问答"""
        self.add_message(session_id, "user", question)
        self.add_message(session_id, "assistant", answer)

    def get_history_for_llm(self, session_id: str, max_rounds: int = 5) -> List[Dict]:
        """获取对话历史（用于注入 LLM 上下文）"""
        msgs = self.get_messages(session_id)
        return msgs[-max_rounds * 2:]  # 每轮 user+assistant


# 全局实例
session_store = SessionStore()