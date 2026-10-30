from api.services import match_service


def make_match(match_id, status, date):
    return {
        "id": match_id,
        "name": f"Match {match_id}",
        "status": status,
        "scheduled_at": date,
        "tournament_id": 21813,
        "opponents": [],
        "results": [],
        "games": [],
    }


class FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return False

    def get_league_matches(
        self, league_id, page=1, per_page=100, status=None
    ):
        if page > 1:
            return []

        return [
            make_match(
                1, "finished", "2026-09-10T15:00:00Z"
            ),
            make_match(
                2, "not_started", "2026-11-10T15:00:00Z"
            ),
            make_match(
                3, "finished", "2026-09-20T15:00:00Z"
            ),
        ]

    def get_team_matches(
        self, team_id, page=1, per_page=100, status=None
    ):
        return self.get_league_matches(
            team_id, page, per_page, status
        )


def test_league_matches_sorting(monkeypatch):
    monkeypatch.setattr(
        match_service, "PandaScoreClient", FakeClient
    )

    result = match_service.fetch_matches(
        kind="league",
        entity_id=4197,
    )

    assert result["total"] == 3
    assert [m["id"] for m in result["items"]] == [
        2, 3, 1
    ]


def test_team_matches_filter(monkeypatch):
    monkeypatch.setattr(
        match_service, "PandaScoreClient", FakeClient
    )

    result = match_service.fetch_matches(
        kind="team",
        entity_id=88,
        status="finished",
    )

    assert result["total"] == 2
    assert [m["id"] for m in result["items"]] == [3, 1]


def test_matches_pagination(monkeypatch):
    monkeypatch.setattr(
        match_service, "PandaScoreClient", FakeClient
    )

    result = match_service.fetch_matches(
        kind="league",
        entity_id=4197,
        limit=1,
        offset=1,
    )

    assert result["total"] == 3
    assert result["items"][0]["id"] == 3