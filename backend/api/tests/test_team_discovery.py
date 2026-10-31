from api.services.team_discovery import discover_running_teams


class FakePandaScoreClient:
    def get_running_lol_series(self, page=1, per_page=20):
        if page == 1:
            return [
                {"id": 100, "league_id": 4197},  # LEC
                {"id": 200, "league_id": 593},   # non-EMEA; skipped
                {"id": 300, "league": {"id": 4292}},  # LFL
            ]
        return []

    def get_series_teams(self, series_id, page=1, per_page=100):
        if page > 1:
            return []
        if series_id == 100:
            return [
                {"id": 88, "name": "G2 Esports", "acronym": "G2", "players": [{}, {}, {}, {}, {}]},
                {"id": 126061, "name": "Team A", "acronym": "A", "players": [{}, {}, {}, {}, {}]},
            ]
        if series_id == 300:
            return [
                {"id": 88, "name": "G2 Esports", "acronym": "G2", "players": [{}, {}, {}, {}, {}]},
                {"id": 2882, "name": "Team B", "acronym": "B", "players": [{}, {}, {}, {}, {}]},
            ]
        raise AssertionError(f"Non-EMEA series should not be scanned: {series_id}")


def test_discover_running_teams():
    teams = discover_running_teams(FakePandaScoreClient())
    assert {team["id"] for team in teams} == {88, 126061, 2882}


def test_discovery_respects_series_limit():
    teams = discover_running_teams(FakePandaScoreClient(), max_series=1)
    assert {team["id"] for team in teams} == {88, 126061}
