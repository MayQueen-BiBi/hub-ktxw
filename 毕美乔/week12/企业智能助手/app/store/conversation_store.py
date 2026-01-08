# app/store/conversation_store.py
import sqlite3
from typing import List, Dict


class ConversationStore:
    def __init__(self, db_path="conversation.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_table()

    def _init_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def load(self, conversation_id: str) -> List[Dict]:
        cursor = self.conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id=? ORDER BY ts",
            (conversation_id,)
        )
        return [{"role": r, "content": c} for r, c in cursor.fetchall()]

    def append(self, conversation_id: str, role: str, content: str):
        self.conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content)
        )
        self.conn.commit()


conversation_store = ConversationStore()
