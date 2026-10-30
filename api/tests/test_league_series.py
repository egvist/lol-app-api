from api.services import league_series


class FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def get_league_series(
        self,
        league_id,
        page=1,
        per_page=100,
    ):
        if page > 1:
            return []

        return [
            {
                "id": 101,
                "name": "Winter",
                "begin_at": "2026-01-15T12:00:00Z",
                "end_at": "2026-03-01T12:00:00Z",
            },
            {
                "id": 102,
                "name": "",
                "begin_at": "2026-06-01T12:00:00Z",
                "end_at": "2026-08-01T12:00:00Z",
            },
            {
                "id": 103,
                "name": "Previous",
                "begin_at": "2025-01-01T12:00:00Z",
                "end_at": "2025-03-01T12:00:00Z",
            },
        ]


def test_series_season_filter():
    assert league_series.series_in_season(
        {
            "begin_at": "2025-12-15T00:00:00Z",
            "end_at": "2026-01-20T00:00:00Z",
        },
        2026,
    )

    assert not league_series.series_in_season(
        {
            "begin_at": "2025-01-01T00:00:00Z",
            "end_at": "2025-03-01T00:00:00Z",
        },
        2026,
    )


def test_list_league_series(monkeypatch):
    monkeypatch.setattr(
        league_series,
        "PandaScoreClient",
        FakeClient,
    )

    result = league_series.list_league_series(
        league_id=4197,
        season=2026,
    )

    assert result["total"] == 2
    assert [item["id"] for item in result["items"]] == [
        102,
        101,
    ]

    assert result["items"][0]["name"] is None


def test_series_pagination(monkeypatch):
    monkeypatch.setattr(
        league_series,
        "PandaScoreClient",
        FakeClient,
    )

    result = league_series.list_league_series(
        league_id=4197,
        season=2026,
        limit=1,
        offset=1,
    )

    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == 101


def test_series_no_matches(monkeypatch):
    monkeypatch.setattr(
        league_series,
        "PandaScoreClient",
        FakeClient,
    )

    result = league_series.list_league_series(
        league_id=4197,
        season=2024,
    )

    assert result["total"] == 0
    assert result["items"] == []