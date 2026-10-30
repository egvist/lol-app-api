from api.services import team_leaderboard_cache as cache


def test_cache_roundtrip():
    season = 2098
    teams = [{"team_id": 88, "position": 1}]

    cache.set_cached_leaderboard(season, teams)

    result = cache.get_cached_leaderboard(season)

    assert result == teams


def test_cache_isolation():
    season = 2097
    teams = [{"team_id": 88, "position": 1}]

    cache.set_cached_leaderboard(season, teams)

    teams[0]["position"] = 999

    result = cache.get_cached_leaderboard(season)

    assert result is not None
    assert result[0]["position"] == 1

    result[0]["position"] = 500

    assert (
        cache.get_cached_leaderboard(season)[0]["position"]
        == 1
    )


def test_cache_expiration(monkeypatch):
    season = 2096

    monkeypatch.setattr(cache, "monotonic", lambda: 1000.0)

    cache.set_cached_leaderboard(
        season,
        [{"team_id": 88}],
    )

    monkeypatch.setattr(cache, "monotonic", lambda: 5000.0)

    assert cache.get_cached_leaderboard(season) is None


def test_missing_cache():
    assert cache.get_cached_leaderboard(2095) is None