from api.services import tournament_results


def test_normalize_standing():
    raw = {
        "rank": 1,
        "team": {
            "id": 88,
            "name": "G2 Esports",
            "acronym": "G2",
        },
    }

    result = tournament_results.normalize_standing(raw)

    assert result["rank"] == 1
    assert result["team"]["id"] == 88


def test_normalize_match():
    raw = {
        "id": 1661680,
        "name": "VIT vs MKOI",
        "status": "finished",
        "tournament_id": 21813,
        "winner_id": 126536,
        "number_of_games": 5,
        "opponents": [
            {
                "opponent": {
                    "id": 115,
                    "name": "Team Vitality",
                }
            },
            {
                "opponent": {
                    "id": 126536,
                    "name": "Movistar KOI",
                }
            },
        ],
        "results": [
            {"team_id": 115, "score": 2},
            {"team_id": 126536, "score": 3},
        ],
        "games": [
            {
                "id": 283830,
                "position": 1,
                "status": "finished",
                "winner": {"id": 126536},
            }
        ],
    }

    result = tournament_results.normalize_match(raw)

    assert result["winner_id"] == 126536
    assert result["opponents"][0]["score"] == 2
    assert result["opponents"][1]["score"] == 3
    assert result["games"][0]["winner_id"] == 126536


class FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get_tournament_standings(
        self, tournament_id, page=1, per_page=100
    ):
        if page > 1:
            return []

        return [
            {"rank": 2, "team": {"id": 134078, "name": "KC"}},
            {"rank": 1, "team": {"id": 88, "name": "G2"}},
        ]

    def get_tournament_matches(
        self, tournament_id, page=1, per_page=100
    ):
        if page > 1:
            return []

        return [
            {
                "id": 10,
                "status": "finished",
                "tournament_id": tournament_id,
                "scheduled_at": "2026-09-10T15:00:00Z",
            },
            {
                "id": 20,
                "status": "finished",
                "tournament_id": tournament_id,
                "scheduled_at": "2026-09-12T15:00:00Z",
            },
        ]


def test_standings_pagination(monkeypatch):
    monkeypatch.setattr(
        tournament_results, "PandaScoreClient", FakeClient
    )

    result = tournament_results.list_tournament_standings(
        21813, limit=1, offset=0
    )

    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["items"][0]["team"]["id"] == 88


def test_matches_pagination(monkeypatch):
    monkeypatch.setattr(
        tournament_results, "PandaScoreClient", FakeClient
    )

    result = tournament_results.list_tournament_matches(
        21813, limit=1, offset=0
    )

    assert result["total"] == 2
    assert result["items"][0]["id"] == 20