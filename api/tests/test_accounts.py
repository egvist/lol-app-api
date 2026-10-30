
import pytest
from datetime import datetime, timezone

from api.schemas.account import RankValue, SeasonRank


# ============================================================
# TEST DATA
# ============================================================

FAKE_ACCOUNT = {
    "id": 1191,
    "player_id": 42,
    "game_name": "J1HUIV",
    "tag_line": "EUW",
    "platform_id": "EUW1",
    "summoner_level": 500,
}

FAKE_RANK = SeasonRank(
    account_id=1191,
    season_label="S16",
    queue_type="RANKED_SOLO_5x5",
    current=RankValue(
        tier="CHALLENGER",
        division=None,
        lp=1500,
        wins=120,
        losses=90,
    ),
    peak=RankValue(
        tier="CHALLENGER",
        division=None,
        lp=1600,
    ),
)

FAKE_HISTORY = [
    {
        "tier": "CHALLENGER",
        "division": None,
        "lp": 1400,
        "wins": 110,
        "losses": 85,
        "observed_at": datetime(
            2026, 10, 20, 12, 0, tzinfo=timezone.utc
        ),
    },
    {
        "tier": "CHALLENGER",
        "division": None,
        "lp": 1500,
        "wins": 120,
        "losses": 90,
        "observed_at": datetime(
            2026, 10, 22, 12, 0, tzinfo=timezone.utc
        ),
    },
]


# ============================================================
# HELPERS
# ============================================================

def mock_existing_account(monkeypatch):
    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_by_id",
        lambda conn, account_id: FAKE_ACCOUNT,
    )


def mock_existing_season(monkeypatch):
    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_season_by_year",
        lambda conn, season: {
            "id": 1,
            "label": "S16",
            "season_year": 2026,
        },
    )


# ============================================================
# 1. ACCOUNT DETAIL
# ============================================================

def test_get_account_detail(client, monkeypatch):
    mock_existing_account(monkeypatch)

    response = client.get("/accounts/1191")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1191
    assert data["player_id"] == 42
    assert data["game_name"] == "J1HUIV"
    assert data["platform_id"] == "EUW1"


def test_get_account_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_by_id",
        lambda conn, account_id: None,
    )

    response = client.get("/accounts/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "Account not found"


# ============================================================
# 2. VALIDATION
# ============================================================

@pytest.mark.parametrize(
    "path",
    [
        "/accounts/abc",
        "/accounts/-1",
        "/accounts/1191/ranks",
        "/accounts/1191/ranks?season=2025",
        "/accounts/1191/rank-history?season=2026&queue_type=INVALID",
    ],
)
def test_accounts_invalid_params(client, path):
    response = client.get(path)

    assert response.status_code == 422


# ============================================================
# 3. ACCOUNT RANKS
# ============================================================

def test_get_account_ranks(client, monkeypatch):
    mock_existing_account(monkeypatch)

    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_ranks",
        lambda conn, account_id, season: [FAKE_RANK],
    )

    response = client.get("/accounts/1191/ranks?season=2026")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["account_id"] == 1191
    assert data[0]["season_label"] == "S16"
    assert data[0]["current"]["lp"] == 1500
    assert data[0]["peak"]["lp"] == 1600


def test_get_account_ranks_empty(client, monkeypatch):
    mock_existing_account(monkeypatch)

    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_ranks",
        lambda conn, account_id, season: [],
    )

    response = client.get("/accounts/1191/ranks?season=2026")

    assert response.status_code == 200
    assert response.json() == []


def test_get_account_ranks_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_by_id",
        lambda conn, account_id: None,
    )

    response = client.get("/accounts/999999/ranks?season=2026")

    assert response.status_code == 404


# ============================================================
# 4. RANK HISTORY
# ============================================================

def test_get_account_rank_history(client, monkeypatch):
    mock_existing_account(monkeypatch)
    mock_existing_season(monkeypatch)

    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_rank_history",
        lambda conn, account_id, season, queue_type, limit: FAKE_HISTORY,
    )

    response = client.get(
        "/accounts/1191/rank-history",
        params={
            "season": 2026,
            "queue_type": "RANKED_SOLO_5x5",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["account_id"] == 1191
    assert data["season_label"] == "S16"
    assert data["queue_type"] == "RANKED_SOLO_5x5"
    assert len(data["history"]) == 2
    assert data["history"][0]["lp"] == 1400
    assert "observed_at" in data["history"][0]


def test_get_account_rank_history_empty(client, monkeypatch):
    mock_existing_account(monkeypatch)
    mock_existing_season(monkeypatch)

    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_rank_history",
        lambda conn, account_id, season, queue_type, limit: [],
    )

    response = client.get(
        "/accounts/1191/rank-history",
        params={
            "season": 2026,
            "queue_type": "RANKED_SOLO_5x5",
        },
    )

    assert response.status_code == 200
    assert response.json()["history"] == []


def test_get_account_rank_history_season_not_found(
    client, monkeypatch
):
    mock_existing_account(monkeypatch)

    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_season_by_year",
        lambda conn, season: None,
    )

    response = client.get(
        "/accounts/1191/rank-history",
        params={
            "season": 2030,
            "queue_type": "RANKED_SOLO_5x5",
        },
    )

    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "Season not found"

def test_get_account_rank_history_account_not_found(
    client, monkeypatch
):
    monkeypatch.setattr(
        "api.routers.accounts.account_repo.get_account_by_id",
        lambda conn, account_id: None,
    )

    response = client.get(
        "/accounts/999999/rank-history",
        params={
            "season": 2026,
            "queue_type": "RANKED_SOLO_5x5",
        },
    )

    assert response.status_code == 404


# ============================================================
# 5. HISTORY LIMIT VALIDATION
# ============================================================

@pytest.mark.parametrize(
    "limit",
    [0, -1, 501],
)
def test_rank_history_invalid_limit(client, limit):
    response = client.get(
        "/accounts/1191/rank-history",
        params={
            "season": 2026,
            "queue_type": "RANKED_SOLO_5x5",
            "limit": limit,
        },
    )

    assert response.status_code == 422
