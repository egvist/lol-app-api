from api.services.team_discovery import discover_running_teams


class FakePandaScoreClient:
    def get_running_lol_series(self, page=1, per_page=20):
        if page == 1:
            return [
                {"id": 100},
                {"id": 200},
            ]
        return []

    def get_series_teams(self, series_id, page=1, per_page=100):
        if page > 1:
            return []

        if series_id == 100:
            return [
                {
                    "id": 88,
                    "name": "G2 Esports",
                    "acronym": "G2",
                    "players": [{}, {}, {}, {}, {}],
                },
                {
                    "id": 126061,
                    "name": "T1",
                    "acronym": "T1",
                    "players": [{}, {}, {}, {}, {}],
                },
            ]

        if series_id == 200:
            return [
                {
                    "id": 88,
                    "name": "G2 Esports",
                    "acronym": "G2",
                    "players": [{}, {}, {}, {}, {}],
                },
                {
                    "id": 2882,
                    "name": "Gen.G",
                    "acronym": "GEN",
                    "players": [{}, {}, {}, {}, {}],
                },
            ]

        return []


def test_discover_running_teams():
    client = FakePandaScoreClient()

    teams = discover_running_teams(client)

    assert len(teams) == 3
    assert {team["id"] for team in teams} == {
        88,
        126061,
        2882,
    }


def test_discovery_respects_series_limit():
    client = FakePandaScoreClient()

    teams = discover_running_teams(
        client,
        max_series=1,
    )

    assert len(teams) == 2
    assert {team["id"] for team in teams} == {
        88,
        126061,
    }