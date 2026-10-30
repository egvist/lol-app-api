from copy import deepcopy
from threading import Lock
from time import monotonic


CACHE_TTL_SECONDS = 3600

_cache: dict[int, tuple[float, list[dict]]] = {}
_cache_lock = Lock()


def get_cached_leaderboard(
    season: int,
) -> list[dict] | None:
    with _cache_lock:
        entry = _cache.get(season)

        if entry is None:
            return None

        expires_at, teams = entry

        if monotonic() >= expires_at:
            del _cache[season]
            return None

        return deepcopy(teams)


def set_cached_leaderboard(
    season: int,
    teams: list[dict],
) -> None:
    with _cache_lock:
        _cache[season] = (
            monotonic() + CACHE_TTL_SECONDS,
            deepcopy(teams),
        )