from api.services import team_leaderboard as lb
from api.services.pandascore_limiter import PandaScoreRateLimitError


class DummyClient:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def _team(team_id):
    return {
        "team_id": team_id,
        "team_name": f"Team {team_id}",
        "team_image_url": None,
        "season": 2026,
        "roster": [],
        "summary": {
            "total_players": 0,
            "ranked_players": 0,
            "average_lp": None,
            "challenger_count": 0,
            "grandmaster_count": 0,
            "master_count": 0,
        },
    }


def test_progress_resumes_after_rate_limit(monkeypatch):
    lb._leaderboard_progress.clear()
    final_cache = {}
    monkeypatch.setattr(lb, 'get_cached_leaderboard', lambda season: final_cache.get(season))
    monkeypatch.setattr(lb, 'set_cached_leaderboard', lambda season, data: final_cache.__setitem__(season, data))
    monkeypatch.setattr(lb, 'PandaScoreClient', DummyClient)
    calls = []
    monkeypatch.setattr(lb, 'discover_running_teams', lambda client, max_series, season: [{'id': i} for i in range(1, 8)])

    def get_team(conn, team_id, season):
        calls.append(team_id)
        if team_id == 3 and calls.count(3) == 1:
            raise PandaScoreRateLimitError('limit')
        return _team(team_id)

    monkeypatch.setattr(lb, 'get_team_soloq', get_team)
    first = lb.get_teams_leaderboard(None, 2026)
    assert first['total'] == 2
    assert 2026 not in final_cache
    second = lb.get_teams_leaderboard(None, 2026)
    assert second['total'] == 7
    assert len(final_cache[2026]) == 7
    assert calls.count(1) == 1
    assert calls.count(2) == 1
    assert calls.count(3) == 2
    lb._leaderboard_progress.clear()
