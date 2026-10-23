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

from fastapi import APIRouter, Query, Depends, HTTPException, Path
from api.db import get_conn
from api.config import settings
from api.schemas.common import Page, Role
from api.schemas.player import PlayerSummary, PlayerDetail
from api.schemas.account import SeasonRank
from api.repositories import players as player_repo
from psycopg import Connection

router = APIRouter(
    prefix="/players",
    tags=["players"]
)

@router.get("", response_model=Page[PlayerSummary])
def get_players(conn: Connection = Depends(get_conn), search: str|None = Query(default=None), role: Role | None = Query(default=None), country: str | None = Query(default=None), limit: int = Query(default=settings.default_page_size, ge=1, le=settings.max_page_size), offset: int = Query(default=0, ge=0)):
    if country is not None:
        country = country.upper()

    players, total = player_repo.list_players(conn, search, role, country, limit, offset)

    page = Page[PlayerSummary](
        items=players,
        total=total,
        limit=limit,
        offset=offset
    )
    return page

@router.get("/{slug}", response_model=PlayerDetail)
def get_player_detail(conn: Connection = Depends(get_conn), slug: str = Path(min_length=1)):

    player = player_repo.get_player_by_slug(conn, slug)
    
    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )
    account = player_repo.get_player_accounts(conn, player["id"])
    social = player_repo.get_player_socials(conn, player["id"])
    detail = PlayerDetail(
        id=player["id"],
        nickname=player["nickname"],
        slug=player["slug"],
        country_code=player["country_code"],
        main_role=player["main_role"],
        profile_image_url=player["profile_image_url"],
        # burada **player yazsak yukaridakileri tek tek yazmaya gerek kalmiyormus
        socials=social,
        accounts=account
    )
    return detail


@router.get("/{slug}/ranks", response_model=list[SeasonRank])
def get_player_ranks(slug: str = Path(min_length=1), season: int = Query(...), conn: Connection = Depends(get_conn)):
    player_detail = player_repo.get_player_by_slug(conn, slug)

    if player_detail is None:
        raise HTTPException(
            status_code=404,
            detail= "Player not found"
        )

    player = player_repo.get_player_ranks(conn, player_detail["id"], season)
    return player
    


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
# CEVAP:
#   - Kurallar parametreye yazılır: Query(ge=1, le=settings.max_page_size),
#     Query(ge=0), Query(min_length=2, max_length=2). FastAPI bunları kontrol
#     eder ve /docs'ta gösterir. Büyük harfe çevirme bir kural değil,
#     endpoint içinde country.upper() ile yapılır.
#   - 422 Unprocessable Entity: istek düzgün biçimli ama içindeki değer
#     kurallara uymuyor; FastAPI/Pydantic doğrulama hataları bunu kullanır.
#     400 Bad Request daha genel: "istek hatalı". Kendi iş kurallarında
#     (ör. "2030 sezonu yok") 400 ya da 404'ü sen seçersin.
#   - Üst sınır yoksa limit=1000000 tek istekte bütün tabloyu okur, hepsini
#     belleğe alır, JSON'a çevirip gönderir. Bellek, CPU ve bir DB bağlantısı
#     uzun süre meşgul olur; birkaç böyle istek API'yi yavaşlatır (kolay bir
#     DoS yolu).
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
# CEVAP:
#   - Path parametresi URL yolunun parçasıdır (/players/{slug}); belirli bir
#     kaynağı gösterir ve zorunludur. Query parametresi ?'den sonra gelir
#     (/players?role=MIDDLE); genelde isteğe bağlıdır ve listeyi filtreler,
#     sıralar ya da sayfalar. REST'te path "hangi kaynak", query "kaynağın
#     hangi alt kümesi" sorusunu cevaplar. slug olmadan oyuncu yoktur; role
#     olmadan da liste vardır, sadece filtresizdir.
#   - response_model dönen veriyi o modele göre doğrular ve filtreler:
#     modelde olmayan alanlar cevaptan atılır. Repository created_at döndürse
#     bile PlayerDetail'de yoksa cevapta görünmez. /docs'taki cevap şeması da
#     bu modelden üretilir.
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
