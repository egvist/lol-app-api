# =============================================================================
# tests/test_players.py — /players testleri (Adım 7)
# =============================================================================
# Her test fonksiyonu "test_" ile başlar ve conftest.py'deki `client`
# fixture'ını parametre olarak alır.
#
# Bir test genelde 3 bölümden oluşur: Arrange (hazırla), Act (isteği at),
# Assert (sonucu kontrol et). "AAA pattern" diye araştır.
#
# GÖREV: Aşağıdaki testleri yaz. Her biri için önce beklenen sonucu kendin
#   tahmin et, sonra testi yaz, sonra çalıştır.
#
#   1. test_health_returns_ok
#        GET /health → 200, cevapta status == "ok"
#
#   2. test_list_players_default_pagination
#        GET /players → 200, cevapta items, total, limit, offset var;
#        len(items) <= limit
#
#   3. test_list_players_rejects_invalid_role
#        GET /players?role=ADC → 422
#
#   4. test_list_players_rejects_too_large_limit
#        GET /players?limit=100000 → 422
#
#   5. test_get_player_not_found
#        GET /players/bu-oyuncu-yok → 404, detail mesajı doğru
#
#   6. test_get_player_detail_shape
#        GET /players/<var olan slug> → 200, socials ve accounts liste
#
#   7. test_search_is_case_insensitive
#        ?search=VLA ile ?search=vla aynı sonucu veriyor mu?
#
#   8. test_sql_injection_is_harmless
#        GET /players/x' OR '1'='1 → 404 olmalı (500 ya da bütün oyuncular DEĞİL)
#        Bu test, repository'de parametreli sorgu kullandığını kanıtlar.
#
# ARAŞTIR: pytest.mark.parametrize — 3 ve 4 numaralı testleri tek test
#   fonksiyonunda birden fazla geçersiz değerle çalıştırmak için.
#
# CEVAP: @pytest.mark.parametrize aynı testi farklı girdilerle birden fazla
#   kez çalıştırır; her değer raporda ayrı bir test olarak görünür ve hangi
#   değerin bozulduğu yazar:
#     @pytest.mark.parametrize("query", ["role=ADC", "role=middle",
#                                        "limit=0", "limit=100000", "offset=-1"])
#     def test_list_players_rejects_invalid_params(client, query):
#         assert client.get(f"/players?{query}").status_code == 422
#
# SONRA: test_accounts.py, test_leaderboard.py, test_matches.py dosyalarını
#   kendin oluştur. Aynı kalıbı izle: mutlu yol (200), bulunamadı (404),
#   geçersiz girdi (422).
# =============================================================================
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
    assert response.json()["detail"] == "Player not found"


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