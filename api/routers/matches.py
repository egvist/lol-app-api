# =============================================================================
# routers/matches.py — /matches endpoint'leri (Adım 9)
# =============================================================================
#
# HAZIRLIK: APIRouter(prefix="/matches", tags=["matches"])
#
# ENDPOINT: GET /matches/{match_id}
#   Örnek: /matches/EUW1_1234567890
#   Cevap: MatchDetail (maç bilgisi + 2 takım + 10 katılımcı)
#
#   GÖREV:
#     - repositories.matches'teki üç fonksiyonu çağır.
#     - Maç yoksa 404.
#     - Katılımcıların items_json alanını modeldeki `items` alanına eşle.
#       ARAŞTIR: Pydantic'te alan adı ile kaynak adı farklıysa ne yapılır?
#       ("alias", "validation_alias") Ya da SQL'de "AS items" demek yeterli mi?
#
#   ARAŞTIR:
#     - match_id formatı "PLATFORM_SAYI". Path parametresine regex (pattern=)
#       koyarak saçma istekleri veritabanına gitmeden reddedebilirsin.
#       Bunun avantajı ne?
#     - Bu cevap hiç değişmez (biten bir maç). HTTP cache header'ları
#       (Cache-Control, ETag) nedir? Bonus: bu endpoint'e Cache-Control ekle.
# =============================================================================
