from collections import deque
from threading import Lock
from time import monotonic


class PandaScoreRateLimitError(Exception):
    pass


class PandaScoreRateLimiter:
    def __init__(self):
        self.minute_requests = deque()
        self.hour_requests = deque()
        self.lock = Lock()
        self.cooldown_until = 0.0

    def set_cooldown(self, seconds: float):
        with self.lock:
            self.cooldown_until = max(
                self.cooldown_until,
                monotonic() + max(0, seconds),
            )
    def acquire(self):
        now = monotonic()

        with self.lock:
            if now < self.cooldown_until:
                raise PandaScoreRateLimitError(
                    "PandaScore cooldown is active"
                )
            while (
                self.minute_requests
                and now - self.minute_requests[0] >= 60
            ):
                self.minute_requests.popleft()

            while (
                self.hour_requests
                and now - self.hour_requests[0] >= 3600
            ):
                self.hour_requests.popleft()

            if (
                len(self.minute_requests) >= 50
                or len(self.hour_requests) >= 900
            ):
                raise PandaScoreRateLimitError(
                    "Local PandaScore rate limit reached"
                )

            self.minute_requests.append(now)
            self.hour_requests.append(now)


pandascore_limiter = PandaScoreRateLimiter()