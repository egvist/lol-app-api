# =============================================================================
# routers/accounts.py — /accounts endpoint'leri (Adım 8)
# =============================================================================
# routers/players.py ile aynı kalıp. Önce onu bitir.
#
# HAZIRLIK: APIRouter(prefix="/accounts", tags=["accounts"])
#
# ENDPOINT 1: GET /accounts/{account_id}
#   Cevap: AccountDetail (hesap + sahibi olan oyuncu + sezon rank'leri)
#   ARAŞTIR: account_id'nin tipini int yaparsan /accounts/abc isteğine ne olur?
#
# ENDPOINT 2: GET /accounts/by-riot-id/{game_name}/{tag_line}
#   Örnek: /accounts/by-riot-id/J1HUIV/000
#   ARAŞTIR:
#     - Riot ID'lerde boşluk ve özel karakter olabilir. URL'de nasıl
#       gönderilir? "URL encoding / percent-encoding" araştır.
#     - SIRALAMA ÖNEMLİ: Bu endpoint'i /{account_id}'den ÖNCE mi SONRA mı
#       tanımlamalısın? Neden? (FastAPI route'ları yukarıdan aşağı eşleştirir.)
#
# ENDPOINT 3: GET /accounts/{account_id}/rank-history?queue=RANKED_SOLO_5x5&season=2026
#   Cevap: RankSnapshot listesi (LP grafiği için)
#   queue için QueueType enum'u kullan, varsayılanı SoloQ olsun.
#
# ENDPOINT 4: GET /accounts/{account_id}/matches?queue_id=420&limit=20&offset=0
#   Cevap: Page[MatchSummary]
#   queue_id sadece 420 veya 440 olabilir. Bunu nasıl doğrularsın?
#   (Enum mu, Literal[420, 440] mi? Araştır: typing.Literal)
#
# ENDPOINT 5: GET /accounts/{account_id}/masteries?limit=10
#   Cevap: ChampionMastery listesi
#
# ORTAK SORUN: 3, 4 ve 5 numaralı endpoint'lerde önce hesabın var olup
#   olmadığını kontrol edip yoksa 404 vermen gerekiyor. Aynı kontrolü üç kere
#   yazmak yerine bir dependency yaz:
#     get_existing_account(account_id, conn) → hesap dict'i ya da 404
#   ve endpoint'lerde Depends(get_existing_account) kullan.
#   ARAŞTIR: FastAPI docs: "Sub-dependencies". Bir dependency başka bir
#   dependency'ye (get_conn) bağımlı olabilir mi?
# =============================================================================
