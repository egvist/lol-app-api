from api.services.team_discovery import discover_running_teams


class FakeClient:
    def __init__(self, running=None, series=None):
        self.running = running or []
        self.series = series or {}
        self.team_ids = []
        self.leagues_checked = []

    def get_running_lol_series(self, page=1, per_page=20):
        return self.running if page == 1 else []

    def get_league_series(self, league_id, page=1, per_page=20):
        self.leagues_checked.append(league_id)
        return self.series.get(league_id, [])

    def get_series_teams(self, series_id, page=1, per_page=100):
        self.team_ids.append(series_id)
        return [{"id": series_id + 10000, "name": f"Team {series_id}"}]


def test_fallback_when_no_running_emea_series():
    client = FakeClient(
        running=[{"id": 9, "league_id": 9999}],
        series={4197: [
            {"id": 11, "begin_at": "2026-06-01", "end_at": "2026-07-01"},
            {"id": 12, "begin_at": "2025-06-01", "end_at": "2025-07-01"},
        ], 4292: [
            {"id": 13, "begin_at": "2026-09-01", "end_at": "2026-10-01"}
        ]},
    )
    teams = discover_running_teams(client, max_series=2, season=2026)
    assert {t["id"] for t in teams} == {10011, 10013}
    assert client.team_ids == [11, 13]


def test_running_emea_skips_fallback():
    client = FakeClient(
        running=[{"id": 7, "league_id": 4197}],
        series={4197: [{"id": 11, "begin_at": "2026-01-01"}]},
    )
    teams = discover_running_teams(client, season=2026)
    assert [t["id"] for t in teams] == [10007]
    assert client.leagues_checked == []


def test_fallback_limit_and_year():
    client = FakeClient(series={4197: [
        {"id": 11, "begin_at": "2025-06-01"},
        {"id": 12, "begin_at": "2026-03-01"},
        {"id": 13, "begin_at": "2026-06-01"},
    ]})
    teams = discover_running_teams(client, max_series=1, season=2026)
    assert [t["id"] for t in teams] == [10012]
