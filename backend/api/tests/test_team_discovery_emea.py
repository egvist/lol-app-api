from api.services.team_discovery import discover_running_teams


class FakeClient:
    def __init__(self):
        self.seen = []

    def get_running_lol_series(self, page=1, per_page=20):
        if page == 1:
            return [
                {"id": 1, "league_id": 593},  # outside EMEA
                {"id": 2, "league_id": 4197},  # LEC
                {"id": 3, "league": {"id": 4292}},  # LFL
                {"id": 4, "league_id": 1003},  # TCL
            ]
        return []

    def get_series_teams(self, series_id, page=1, per_page=100):
        self.seen.append(series_id)
        return [{"id": series_id + 100, "name": f"Team {series_id}"}]


def test_skips_non_emea_and_counts_only_eligible_series():
    client = FakeClient()
    teams = discover_running_teams(client, max_series=2)
    assert client.seen == [2, 3]
    assert [team["id"] for team in teams] == [102, 103]


def test_keeps_emearoster_discovery_without_global_teams():
    client = FakeClient()
    teams = discover_running_teams(client)
    assert client.seen == [2, 3, 4]
    assert {team["id"] for team in teams} == {102, 103, 104}
