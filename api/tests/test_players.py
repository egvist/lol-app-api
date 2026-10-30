
from unittest.mock import MagicMock, patch
import pytest


def test_list_players(client, monkeypatch):
    fake_players = [
        {
            "id": 1,
            "nickname": "Vladi",
            "slug": "vladi",
            "country_code": "GR",
            "main_role": "MIDDLE",
        }
    ]

    def fake_list_players(conn, search, role, country, limit, offset):
        return fake_players, 1

    monkeypatch.setattr("api.routers.players.player_repo.list_players", fake_list_players)

    response = client.get("/players")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["nickname"] == "Vladi"


def test_health_returns_ok(client):
    fake_cursor = MagicMock()
    fake_connection = MagicMock()

    fake_connection.cursor.return_value.__enter__.return_value = fake_cursor

    with patch("api.main.connection_pool.connection") as mock_connection:
        mock_connection.return_value.__enter__.return_value = fake_connection

        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_players_default_pagination(client, monkeypatch):
    def fake_list_players(conn, search, role, country, limit, offset):
        return [], 0

    monkeypatch.setattr(
        "api.routers.players.player_repo.list_players",
        fake_list_players
    )

    response = client.get("/players")

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    assert data["limit"] == 20
    assert data["offset"] == 0
    assert len(data["items"]) <= data["limit"]



@pytest.mark.parametrize(
    "query",
    [
        "role=ADC",
        "role=middle",
        "limit=0",
        "limit=100000",
        "offset=-1",
    ],
)
def test_list_players_rejects_invalid_params(client, query):
    response = client.get(f"/players?{query}")

    assert response.status_code == 422

def test_get_player_not_found(client, monkeypatch):

    def fake_get_player(conn, slug):
        return None

    monkeypatch.setattr(
        "api.routers.players.player_repo.get_player_by_slug",
        fake_get_player
    )

    response = client.get("/players/bu-oyuncu-yok")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "Player not found"


def test_get_player_detail_shape(client, monkeypatch):
    player = {
        "id": 1,
        "nickname": "Vladi",
        "slug": "vladi",
        "country_code": "GR",
        "main_role": "MIDDLE",
        "profile_image_url": None,
    }

    monkeypatch.setattr(
        "api.routers.players.player_repo.get_player_by_slug",
        lambda conn, slug: player
    )

    monkeypatch.setattr(
        "api.routers.players.player_repo.get_player_socials",
        lambda conn, player_id: []
    )

    monkeypatch.setattr(
        "api.routers.players.player_repo.get_player_accounts",
        lambda conn, player_id: []
    )

    response = client.get("/players/vladi")

    assert response.status_code == 200

    data = response.json()

    assert data["slug"] == "vladi"
    assert isinstance(data["socials"], list)
    assert isinstance(data["accounts"], list)



def test_search_is_case_insensitive(client, monkeypatch):
    def fake_list_players(conn, search, role, country, limit, offset):
        if search and search.lower() in "vladi":
            return [
                {
                    "id": 1,
                    "nickname": "Vladi",
                    "slug": "vladi",
                    "country_code": "GR",
                    "main_role": "MIDDLE",
                }
            ], 1

        return [], 0

    monkeypatch.setattr(
        "api.routers.players.player_repo.list_players",
        fake_list_players
    )

    upper = client.get("/players?search=VLA")
    lower = client.get("/players?search=vla")

    assert upper.status_code == 200
    assert lower.status_code == 200
    assert upper.json() == lower.json()


def test_sql_injection_is_harmless(client, monkeypatch):
    monkeypatch.setattr(
        "api.routers.players.player_repo.get_player_by_slug",
        lambda conn, slug: None
    )

    response = client.get(
        "/players/x%27%20OR%20%271%27%3D%271"
    )

    assert response.status_code == 404