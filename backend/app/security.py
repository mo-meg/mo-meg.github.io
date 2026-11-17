"""Abuse protection for the public chat endpoint."""

from __future__ import annotations

import hashlib
import re
import secrets
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

from starlette.requests import Request

_SALT = secrets.token_bytes(16)  # per-process: hashed client keys can't be linked across restarts
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2066-\u2069]")


def sanitize_message(text: str, max_chars: int) -> str:
    """Strip control / bidi-override characters, collapse excessive blank lines, enforce length."""
    text = _CONTROL.sub("", text).replace("\r\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    return text.strip()[:max_chars]


def client_key(request: Request, trust_proxy: bool) -> str:
    """Pseudonymous rate-limit key. The raw IP address is never stored."""
    ip = request.client.host if request.client else "unknown"
    if trust_proxy:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            ip = fwd.split(",")[0].strip()
    return hashlib.sha256(_SALT + ip.encode()).hexdigest()[:24]


@dataclass
class _Bucket:
    minute: deque[float] = field(default_factory=deque)
    day: deque[float] = field(default_factory=deque)


class RateLimiter:
    """Sliding-window limits per client (per minute and per day) plus a global daily budget."""

    def __init__(self, per_minute: int, per_day: int, daily_budget: int, max_keys: int = 50_000) -> None:
        self.per_minute = per_minute
        self.per_day = per_day
        self.daily_budget = daily_budget
        self._max_keys = max_keys
        self._buckets: dict[str, _Bucket] = {}
        self._budget_day = datetime.now(UTC).date()
        self._budget_used = 0

    def _gc(self, now: float) -> None:
        if len(self._buckets) <= self._max_keys:
            return
        for k in [k for k, b in self._buckets.items() if not b.day or now - b.day[-1] > 86_400]:
            del self._buckets[k]

    def check(self, key: str, now: float | None = None) -> tuple[bool, str | None, int]:
        """Returns (allowed, scope_if_blocked, retry_after_seconds) and records the hit if allowed."""
        now = time.time() if now is None else now
        today = datetime.fromtimestamp(now, UTC).date()
        if today != self._budget_day:
            self._budget_day, self._budget_used = today, 0
        if self._budget_used >= self.daily_budget:
            return False, "global", 3600

        b = self._buckets.setdefault(key, _Bucket())
        while b.minute and now - b.minute[0] >= 60:
            b.minute.popleft()
        while b.day and now - b.day[0] >= 86_400:
            b.day.popleft()
        if len(b.minute) >= self.per_minute:
            return False, "minute", max(1, int(60 - (now - b.minute[0])) + 1)
        if len(b.day) >= self.per_day:
            return False, "day", max(1, int(86_400 - (now - b.day[0])) + 1)

        b.minute.append(now)
        b.day.append(now)
        self._budget_used += 1
        self._gc(now)
        return True, None, 0
