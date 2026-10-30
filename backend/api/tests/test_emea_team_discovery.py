from api.services.team_discovery import discover_emea_teams


class FakeClient:
    def get_league_series(self, league_id, page=1, per_page=100):
        if page > 1:
            return []

        if league_id == 4197:
            return [
                {
                    "id": 101,
                    "begin_at": "2026-01-01T00:00:00Z",
                    "end_at": "2026-03-01T00:00:00Z",
                },
                {
                    "id": 102,
                    "begin_at": "2025-01-01T00:00:00Z",
                    "end_at": "2025-03-01T00:00:00Z",
                },
            ]

        if league_id == 4292:
            return [
                {
                    "id": 201,
                    "begin_at": "2026-04-01T00:00:00Z",
                    "end_at": "2026-06-01T00:00:00Z",
                },
            ]

        return []

    def get_series_teams(self, series_id, page=1, per_page=100):
        if page > 1:
            return []

        teams = {
            101: [
                {"id": 88, "name": "G2 Esports"},
                {"id": 200, "name": "Team B"},
            ],
            201: [
                {"id": 200, "name": "Team B"},
                {"id": 300, "name": "Team C"},
            ],
        }

        return teams.get(series_id, [])


def test_emea_team_discovery():
    result = discover_emea_teams(
        FakeClient(),
        league_ids=[4197, 4292],
        season=2026,
    )

    assert len(result) == 3

    teams = {team["id"]: team for team in result}

    assert set(teams) == {88, 200, 300}

    assert teams[200]["league_ids"] == [4197, 4292]
    assert teams[200]["series_ids"] == [101, 201]


def test_excludes_previous_seasons():
    result = discover_emea_teams(
        FakeClient(),
        league_ids=[4197],
        season=2025,
    )

    assert result == []