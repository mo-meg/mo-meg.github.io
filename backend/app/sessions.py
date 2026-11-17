"""In-memory conversation sessions with TTL expiry and LRU bound.

Deliberately not persisted: only the text of the current conversation is held, for at most
SESSION_TTL_MINUTES of inactivity, and nothing that identifies the visitor is stored.
(For multiple API replicas, swap this for a Redis-backed implementation with the same interface.)
"""

from __future__ import annotations

import secrets
import time
from collections import OrderedDict
from dataclasses import dataclass, field

from app.llm import Turn


@dataclass
class Session:
    id: str
    turns: list[Turn] = field(default_factory=list)
    last_seen: float = field(default_factory=time.monotonic)


class SessionStore:
    def __init__(self, ttl_seconds: float, max_sessions: int, history_turns: int, max_history_chars: int) -> None:
        self._ttl = ttl_seconds
        self._max = max_sessions
        self._history_msgs = history_turns * 2
        self._max_chars = max_history_chars
        self._data: OrderedDict[str, Session] = OrderedDict()

    def _evict(self) -> None:
        now = time.monotonic()
        while self._data:
            _, s = next(iter(self._data.items()))
            if now - s.last_seen > self._ttl or len(self._data) > self._max:
                self._data.popitem(last=False)
            else:
                break

    def get_or_create(self, session_id: str | None) -> Session:
        self._evict()
        if session_id and session_id in self._data:
            s = self._data[session_id]
            s.last_seen = time.monotonic()
            self._data.move_to_end(session_id)
            return s
        # Unknown/expired ids are never adopted — the server issues ids itself.
        s = Session(id=secrets.token_urlsafe(18))
        self._data[s.id] = s
        self._evict()
        return s

    def history(self, s: Session) -> list[Turn]:
        """Most recent turns within the message and character budget."""
        turns = s.turns[-self._history_msgs :] if self._history_msgs else []
        total = 0
        kept: list[Turn] = []
        for t in reversed(turns):
            total += len(t.text)
            if total > self._max_chars:
                break
            kept.append(t)
        kept.reverse()
        # Gemini expects the conversation to start with a user turn.
        while kept and kept[0].role != "user":
            kept.pop(0)
        return kept

    def append_exchange(self, s: Session, user_text: str, model_text: str) -> None:
        s.turns.extend([Turn("user", user_text), Turn("model", model_text)])
        if self._history_msgs and len(s.turns) > self._history_msgs:
            s.turns = s.turns[-self._history_msgs :]
        s.last_seen = time.monotonic()

    def reset(self, session_id: str) -> bool:
        return self._data.pop(session_id, None) is not None

    def __len__(self) -> int:
        return len(self._data)
