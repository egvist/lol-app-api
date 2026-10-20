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
# SONRA: test_accounts.py, test_leaderboard.py, test_matches.py dosyalarını
#   kendin oluştur. Aynı kalıbı izle: mutlu yol (200), bulunamadı (404),
#   geçersiz girdi (422).
# =============================================================================
