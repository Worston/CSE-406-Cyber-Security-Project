"""Failed-login tracking used by the webapp's lockout defense."""
import time

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 30
LOCKOUT_SECONDS = 60


class LockoutTracker:
    def __init__(self):
        self._failures = {}      # username -> list[timestamp]
        self._locked_until = {}  # username -> timestamp

    def is_locked(self, username: str) -> bool:
        until = self._locked_until.get(username)
        return until is not None and time.time() < until

    def record_failure(self, username: str) -> None:
        now = time.time()
        attempts = [t for t in self._failures.get(username, []) if now - t < WINDOW_SECONDS]
        attempts.append(now)
        self._failures[username] = attempts
        if len(attempts) >= MAX_ATTEMPTS:
            self._locked_until[username] = now + LOCKOUT_SECONDS

    def record_success(self, username: str) -> None:
        self._failures.pop(username, None)
        self._locked_until.pop(username, None)
