import pytest

from api.services.pandascore_limiter import (
    PandaScoreRateLimiter,
    PandaScoreRateLimitError,
)


def test_minute_rate_limit():
    limiter = PandaScoreRateLimiter()

    for _ in range(50):
        limiter.acquire()

    with pytest.raises(PandaScoreRateLimitError):
        limiter.acquire()


def test_requests_below_limit():
    limiter = PandaScoreRateLimiter()

    for _ in range(20):
        limiter.acquire()

    assert len(limiter.minute_requests) == 20
    assert len(limiter.hour_requests) == 20


def test_minute_window_expires(monkeypatch):
    clock = [1000.0]

    monkeypatch.setattr(
        "api.services.pandascore_limiter.monotonic",
        lambda: clock[0],
    )

    limiter = PandaScoreRateLimiter()

    for _ in range(50):
        limiter.acquire()

    clock[0] += 60

    limiter.acquire()

    assert len(limiter.minute_requests) == 1
    assert len(limiter.hour_requests) == 51

def test_hourly_rate_limit(monkeypatch):
    clock = [1000.0]

    monkeypatch.setattr(
        "api.services.pandascore_limiter.monotonic",
        lambda: clock[0],
    )

    limiter = PandaScoreRateLimiter()

    for _ in range(18):
        for _ in range(50):
            limiter.acquire()

        clock[0] += 60

    assert len(limiter.hour_requests) == 900

    with pytest.raises(PandaScoreRateLimitError):
        limiter.acquire()

    clock[0] += 3540

    limiter.acquire()

    assert len(limiter.hour_requests) == 1


def test_cooldown_blocks_requests(monkeypatch):
    clock = [1000.0]

    monkeypatch.setattr(
        "api.services.pandascore_limiter.monotonic",
        lambda: clock[0],
    )

    limiter = PandaScoreRateLimiter()

    limiter.set_cooldown(30)

    with pytest.raises(PandaScoreRateLimitError):
        limiter.acquire()

    clock[0] += 29

    with pytest.raises(PandaScoreRateLimitError):
        limiter.acquire()

    clock[0] += 1

    limiter.acquire()

    assert len(limiter.minute_requests) == 1