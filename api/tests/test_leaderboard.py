
import pytest

from api.repositories import leaderboard as leaderboard_repo


SAMPLE_ENTRY = {
    "rank_position": 1,
    "player_id": 3,
    "nickname": "Comp",
    "slug": "comp",
    "account_id": 6,
    "game_name": "Kite Machine",
    "tag_line": "2015",
    "platform_id": "EUW1",
    "queue_type": "RANKED_SOLO_5x5",
    "tier": "CHALLENGER",
    "division": None,
    "lp": 1800,
    "wins": 100,
    "losses": 50,
}


def mock_leaderboard(monkeypatch, entries=None, total=1):
    if entries is None:
        entries = [SAMPLE_ENTRY]

    monkeypatch.setattr(
        leaderboard_repo,
        "list_leaderboard",
        lambda conn, season, queue_type, limit, offset: entries,
    )

    monkeypatch.setattr(
        leaderboard_repo,
        "get_leaderboard_total",
        lambda conn, season, queue_type: total,
    )


def test_leaderboard_success(client, monkeypatch):
    mock_leaderboard(monkeypatch)

    response = client.get("/leaderboard?season=2026")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["nickname"] == "Comp"
    assert data["items"][0]["rank_position"] == 1
    assert data["items"][0]["lp"] == 1800


def test_leaderboard_empty(client, monkeypatch):
    mock_leaderboard(monkeypatch, entries=[], total=0)

    response = client.get("/leaderboard?season=2026")

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


def test_leaderboard_requires_season(client):
    response = client.get("/leaderboard")

    assert response.status_code == 422


@pytest.mark.parametrize(
    "season",
    ["abc", "2025", "-1"],
)
def test_invalid_season(client, season):
    response = client.get(
        "/leaderboard",
        params={"season": season},
    )

    assert response.status_code == 422


def test_invalid_queue_type(client):
    response = client.get(
        "/leaderboard",
        params={
            "season": 2026,
            "queue_type": "INVALID",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "limit,offset",
    [
        (0, 0),
        (101, 0),
        (20, -1),
    ],
)
def test_invalid_pagination(client, limit, offset):
    response = client.get(
        "/leaderboard",
        params={
            "season": 2026,
            "limit": limit,
            "offset": offset,
        },
    )

    assert response.status_code == 422


def test_leaderboard_pagination(client, monkeypatch):
    mock_leaderboard(monkeypatch, total=100)

    response = client.get(
        "/leaderboard",
        params={
            "season": 2026,
            "limit": 10,
            "offset": 20,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["limit"] == 10
    assert data["offset"] == 20
    assert data["total"] == 100


def test_leaderboard_fields(client, monkeypatch):
    mock_leaderboard(monkeypatch)

    response = client.get("/leaderboard?season=2026")

    assert response.status_code == 200

    entry = response.json()["items"][0]

    assert entry["player_id"] == 3
    assert entry["account_id"] == 6
    assert entry["game_name"] == "Kite Machine"
    assert entry["tag_line"] == "2015"
    assert entry["tier"] == "CHALLENGER"
    assert entry["queue_type"] == "RANKED_SOLO_5x5"




def test_leaderboard_without_previous_snapshot(
    client, monkeypatch
):
    entry = {
        **SAMPLE_ENTRY,
        "previous_rank": None,
        "rank_change": None,
    }

    mock_leaderboard(
        monkeypatch,
        entries=[entry],
        total=1,
    )

    response = client.get("/leaderboard?season=2026")

    assert response.status_code == 200

    result = response.json()["items"][0]

    assert result["previous_rank"] is None
    assert result["rank_change"] is None


def test_leaderboard_weekly_rank_change(
    client, monkeypatch
):
    entry = {
        **SAMPLE_ENTRY,
        "rank_position": 7,
        "previous_rank": 12,
        "rank_change": 5,
    }

    mock_leaderboard(
        monkeypatch,
        entries=[entry],
        total=1,
    )

    response = client.get("/leaderboard?season=2026")

    assert response.status_code == 200

    result = response.json()["items"][0]

    assert result["rank_position"] == 7
    assert result["previous_rank"] == 12
    assert result["rank_change"] == 5
