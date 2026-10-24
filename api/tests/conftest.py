# =============================================================================
# tests/conftest.py — Ortak test ayarları (Adım 7)
# =============================================================================
# pytest bu dosyayı otomatik bulur. Buradaki "fixture"lar bütün test
# dosyalarında kullanılabilir.
#
# GÖREV:
#   1. `client` adında bir fixture yaz. FastAPI'nin TestClient'ı ile
#      api.main.app'i sarsın ve testlere versin.
#      ARAŞTIR: FastAPI docs: "Testing". TestClient'ı `with` bloğu içinde
#      kullanmak lifespan'in (havuzun açılmasının) çalışması için neden gerekli?
#      CEVAP: TestClient(app) tek başına lifespan'i çalıştırmaz; istekler
#      havuz açılmadan gider ve get_conn hata verir. `with TestClient(app) as c:`
#      bloğuna girince lifespan'in yield öncesi (havuzu aç), bloktan çıkınca
#      yield sonrası (havuzu kapat) çalışır. Fixture'da bloğun içinde
#      `yield c` yaparsın.
#
# ARAŞTIR (iki farklı test yaklaşımı, ikisini de öğren):
#
#   A) Gerçek veritabanıyla test ("integration test")
#      - Kolay başlangıç: mevcut lolapp veritabanına bağlanır.
#      - Sorun: Veri değişirse testler bozulur. Riot sync çalışınca LP değişir.
#      - Daha iyisi: Ayrı bir "lolapp_test" veritabanı, sql/schema.sql ile
#        kurulmuş ve içine elle birkaç test satırı eklenmiş.
#
#   B) Repository'yi taklit ederek test ("unit test" + mocking)
#      - FastAPI docs: "Testing Dependencies with Overrides"
#        app.dependency_overrides[get_conn] = ... ile gerçek DB yerine sahte
#        bir şey verebilirsin.
#      - Ya da unittest.mock / pytest monkeypatch ile repository
#        fonksiyonlarının sabit veri döndürmesini sağlayabilirsin.
#      - Avantaj: PostgreSQL olmadan çalışır, hızlıdır.
#        Kök dizindeki test_riot_sync_offline.py de ağ olmadan test ediyor;
#        nasıl yaptığına bak.
#
# CEVAP:
#   - A (integration): Gerçek SQL, şema ve bağlantı test edilir; yanlış kolon
#     adı ya da hatalı bir JOIN ancak burada yakalanır. Daha yavaştır,
#     PostgreSQL ister ve veriye bağlıdır. Ayrı bir lolapp_test veritabanı ve
#     sabit test satırlarıyla sonuçlar her seferinde aynı olur.
#   - B (unit + mock): app.dependency_overrides[get_conn] ya da
#     monkeypatch.setattr(players_repo, "get_player_by_slug", lambda c, s: None)
#     ile veritabanına hiç gidilmez. Router mantığı (404, 422, cevap şekli)
#     milisaniyelerde test edilir, ama SQL'in doğru olduğunu kanıtlamaz.
#     Dikkat: monkeypatch, fonksiyonun çağrıldığı yerdeki ada uygulanır.
#     Router "from api.repositories import players" ile import edip
#     players.get_player_by_slug(...) diye çağırıyorsa modülü patch'lersin.
#     B'de `with TestClient(app)` kullanırsan lifespan yine havuzu açmaya
#     çalışır; open_pool/close_pool'u da patch'le ya da `with` kullanma.
#   - İkisi birbirini tamamlar: B router'ı, A repository'yi ve SQL'i test eder.
#
# Önerim: Önce B ile başla (router mantığını test et), sonra A'ya geç.
#
# ÇALIŞTIRMA: Kök dizinde `py -m pytest api/tests -v`
# =============================================================================


import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.db import get_conn

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("api.main.open_pool", lambda: None)
    monkeypatch.setattr("api.main.close_pool", lambda: None)

    def fake_get_conn():
        yield object()

    app.dependency_overrides[get_conn] = fake_get_conn

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_conn, None)