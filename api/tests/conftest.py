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
# Önerim: Önce B ile başla (router mantığını test et), sonra A'ya geç.
#
# ÇALIŞTIRMA: Kök dizinde `py -m pytest api/tests -v`
# =============================================================================
