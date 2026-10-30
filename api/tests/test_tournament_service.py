from api.services import tournament_service


class FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def get_series_tournaments(
        self, series_id, page=1, per_page=100
    ):
        if page > 1:
            return []

        return [
            {
                "id": 201,
                "name": "Group Stage",
                "begin_at": "2026-07-01T12:00:00Z",
                "league": {"id": 4197},
                "serie": {"id": series_id},
            },
            {
                "id": 202,
                "name": "Playoffs",
                "begin_at": "2026-08-01T12:00:00Z",
                "league": {"id": 4197},
                "serie": {"id": series_id},
            },
        ]

    def get_tournament(self, tournament_id):
        return {
            "id": tournament_id,
            "name": "Playoffs",
            "league": {"id": 4197},
            "serie": {"id": 10756},
            "winner_id": 88,
        }


def test_series_tournaments(monkeypatch):
    monkeypatch.setattr(
        tournament_service, "PandaScoreClient", FakeClient
    )

    result = tournament_service.list_series_tournaments(
        series_id=10756
    )

    assert result["total"] == 2
    assert result["items"][0]["name"] == "Playoffs"
    assert result["items"][0]["serie_id"] == 10756


def test_tournament_pagination(monkeypatch):
    monkeypatch.setattr(
        tournament_service, "PandaScoreClient", FakeClient
    )

    result = tournament_service.list_series_tournaments(
        series_id=10756,
        limit=1,
        offset=1,
    )

    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == 201


def test_tournament_detail(monkeypatch):
    monkeypatch.setattr(
        tournament_service, "PandaScoreClient", FakeClient
    )

    result = tournament_service.get_tournament_detail(202)

    assert result["id"] == 202
    assert result["league_id"] == 4197
    assert result["serie_id"] == 10756
    assert result["winner_id"] == 88