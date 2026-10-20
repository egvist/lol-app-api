# =============================================================================
# routers/players.py — /players endpoint'leri (Adım 6)
# =============================================================================
# İlk gerçek router'ın bu. Diğer router'lar da aynı kalıbı izleyecek.
# Bunu iyi yaparsan geri kalanlar tekrar olacak.
#
# HAZIRLIK:
#   - APIRouter oluştur: prefix="/players", tags=["players"]
#   - İhtiyacın olanlar: Depends, HTTPException, Query, Path (fastapi'den),
#     get_conn (api.db), settings (api.config), schemas ve repositories modülleri.
#
# -----------------------------------------------------------------------------
# ENDPOINT 1: GET /players
# -----------------------------------------------------------------------------
# Örnek istek: GET /players?search=vla&role=MIDDLE&country=GR&limit=20&offset=0
# Cevap: Page[PlayerSummary]
#
# GÖREV:
#   - Query parametreleri: search, role (Role enum), country, limit, offset
#   - limit için alt ve üst sınır koy (ör. 1 ile settings.max_page_size arası).
#     offset negatif olamaz.
#   - country 2 harf olmalı. Küçük harf gelirse büyüğe çevir.
#   - repositories.players.list_players'ı çağır, sonucu Page olarak döndür.
#
# ARAŞTIR:
#   - FastAPI docs: "Query Parameters and String Validations",
#     "Query Parameters and Numeric Validations" (ge=, le=, min_length=, ...)
#   - Sınırları aşan bir istekte FastAPI hangi durum kodunu döndürür? (422)
#     422 ile 400 farkı ne?
#   - Neden limit'e üst sınır koymak zorundasın? limit=1000000 isteği sunucuya
#     ne yapar?
#
# -----------------------------------------------------------------------------
# ENDPOINT 2: GET /players/{slug}
# -----------------------------------------------------------------------------
# Örnek: GET /players/vladi
# Cevap: PlayerDetail (oyuncu + socials + accounts)
#
# GÖREV:
#   - Repository'den oyuncuyu al. None ise HTTPException(status_code=404,
#     detail="Player not found") fırlat.
#   - Socials ve accounts'u al, hepsini PlayerDetail'de birleştir.
#
# ARAŞTIR:
#   - Path parametresi nedir, query parametresinden farkı ne? Bir kaynağı
#     tanımlayan değer (slug) neden path'te, filtre (role) neden query'de?
#     "REST resource naming" araştır.
#   - response_model parametresi ne yapıyor? Repository fazladan bir alan
#     döndürürse (ör. created_at) cevapta görünür mü?
#
# -----------------------------------------------------------------------------
# ENDPOINT 3: GET /players/{slug}/ranks?season=2026
# -----------------------------------------------------------------------------
# GÖREV: Oyuncunun BÜTÜN hesaplarının o sezondaki rank'lerini döndür.
#   Oyuncu yoksa 404. Hesapları yoksa boş liste (404 değil!).
#   DÜŞÜN: "Oyuncu yok" ile "oyuncunun hiç rank'i yok" neden farklı cevaplar?
#
# -----------------------------------------------------------------------------
# ENDPOINT 4 (Bonus): GET /players/{slug}/live
# -----------------------------------------------------------------------------
# GÖREV: Oyuncu şu an oyundaysa canlı oyunu döndür, değilse ne dönmeli?
#   Seçenekler: 404, 204 No Content, ya da {"in_game": false}. Araştır ve seç.
#
# KONTROL: /docs sayfasından her endpoint'i "Try it out" ile dene.
#   /players/vladi, /players/bu-oyuncu-yok, /players?limit=0, /players?role=ADC
# =============================================================================
