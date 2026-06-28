"""
Session Service - manages per-session chat history.
In-memory store with optional JSON persistence.
Swap for Redis in production for horizontal scaling.
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

SESSIONS_FILE = "./data/sessions.json"
MAX_HISTORY_TURNS = 20  # Keep last 20 turns per session
_lock = threading.Lock()


class SessionService:
    """Per-session chat history manager."""

    def __init__(self):
        self._path = Path(SESSIONS_FILE)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict:
        if not self._path.exists():
            return {}
        with open(self._path, "r") as f:
            return json.load(f)

    def _save(self, data: Dict):
        with open(self._path, "w") as f:
            json.dump(data, f, indent=2)

    def get_history(self, session_id: str) -> List[Dict]:
        data = self._load()
        session = data.get(session_id, {})
        return session.get("messages", [])

    def add_turn(self, session_id: str, user_msg: str, assistant_msg: str):
        with _lock:
            data = self._load()
            if session_id not in data:
                data[session_id] = {
                    "session_id": session_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "messages":   [],
                }

            messages = data[session_id]["messages"]
            messages.append({"role": "user",      "content": user_msg,      "ts": datetime.utcnow().isoformat()})
            messages.append({"role": "assistant", "content": assistant_msg, "ts": datetime.utcnow().isoformat()})

            # Trim to max turns
            if len(messages) > MAX_HISTORY_TURNS * 2:
                messages = messages[-(MAX_HISTORY_TURNS * 2):]
                data[session_id]["messages"] = messages

            data[session_id]["updated_at"] = datetime.utcnow().isoformat()
            self._save(data)

    def clear(self, session_id: str):
        with _lock:
            data = self._load()
            data.pop(session_id, None)
            self._save(data)
