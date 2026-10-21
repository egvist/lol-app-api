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
#       CEVAP: Field(validation_alias="items_json") girdide items_json'u
#       okur, JSON çıktısında items adını kullanır. alias= ise çıktıda da
#       adı değiştirir (FastAPI cevapta alias'ı kullanır), yani cevapta
#       items_json görünür; burada istenen bu değil. En basiti SQL'de
#       "items_json AS items": kolon adı model alanıyla aynı olur, alias
#       gerekmez. Evet, bu yeterli.
#
#   ARAŞTIR:
#     - match_id formatı "PLATFORM_SAYI". Path parametresine regex (pattern=)
#       koyarak saçma istekleri veritabanına gitmeden reddedebilirsin.
#       Bunun avantajı ne?
#     - Bu cevap hiç değişmez (biten bir maç). HTTP cache header'ları
#       (Cache-Control, ETag) nedir? Bonus: bu endpoint'e Cache-Control ekle.
#
#   CEVAP:
#     - pattern=r"^[A-Z0-9]+_[0-9]+$" ile /matches/abc gibi istekler 422 ile
#       hemen reddedilir; repository ve SQL hiç çalışmaz. Hatalı ya da kötü
#       niyetli çok sayıda istek veritabanını meşgul etmez, kullanıcı da
#       "bulunamadı" (404) yerine "format yanlış" (422) diye doğru hatayı alır.
#     - Cache-Control: tarayıcıya ve aradaki proxy/CDN'lere cevabı ne kadar
#       saklayabileceklerini söyler. Biten maç değişmez:
#       "Cache-Control: public, max-age=86400, immutable".
#       ETag: cevabın içeriğinden üretilen bir kimlik. İstemci tekrar sorarken
#       bunu If-None-Match ile gönderir; içerik değişmediyse sunucu gövdesiz
#       304 Not Modified döner.
#       FastAPI'de endpoint'e `response: Response` parametresi ekleyip
#       response.headers["Cache-Control"] = "..." yazarsın.
# =============================================================================
