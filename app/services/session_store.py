import sqlite3
import json
from app.models.session import SessionState, Message, MemoryItem, ReflectionItem

class SQLiteSessionStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            payload TEXT NOT NULL
        )
        """)
        conn.commit()
        conn.close()

    def get_or_create(self, session_id: str) -> SessionState:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT payload FROM sessions WHERE session_id=?", (session_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            session = SessionState(session_id=session_id)
            self.save(session)
            return session

        data = json.loads(row[0])
        return self._deserialize(data)

    def save(self, session: SessionState):
        data = self._serialize(session)
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO sessions(session_id, payload) VALUES (?, ?)",
            (session.session_id, json.dumps(data, ensure_ascii=False))
        )
        conn.commit()
        conn.close()

    def _serialize(self, session: SessionState):
        return {
            "session_id": session.session_id,
            "history": [m.__dict__ for m in session.history],
            "short_memory": [m.__dict__ for m in session.short_memory],
            "long_memory": [m.__dict__ for m in session.long_memory],
            "reflections": [r.__dict__ for r in session.reflections],
            "metadata": session.metadata,
        }

    def _deserialize(self, data):
        session = SessionState(session_id=data["session_id"])
        session.history = [Message(**x) for x in data.get("history", [])]
        session.short_memory = [MemoryItem(**x) for x in data.get("short_memory", [])]
        session.long_memory = [MemoryItem(**x) for x in data.get("long_memory", [])]
        session.reflections = [ReflectionItem(**x) for x in data.get("reflections", [])]
        session.metadata = data.get("metadata", {})
        return session