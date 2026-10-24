# =============================================================================
# routers/leaderboard.py — /leaderboard ve /seasons endpoint'leri (Adım 8)
# =============================================================================
# Bu dosyada iki router olabilir ya da tek router'da prefix vermeden iki yol
# tanımlayabilirsin. Hangisinin daha düzenli olduğuna karar ver.
#
# ENDPOINT 1: GET /leaderboard?platform=EUW1&queue=RANKED_SOLO_5x5&limit=50&offset=0
#   Cevap: Leaderboard
#   GÖREV:
#     - platform zorunlu mu olmalı, yoksa varsayılanı EUW1 mi? Karar ver.
#     - Aktif sezon yoksa ne olur? Uygun bir hata kodu ve mesaj döndür.
#     - Cevaba "resmî Riot sıralaması değildir" notunu ekle.
#
# ENDPOINT 2: GET /leaderboard/platforms
#   Cevap: platform listesi (["EUW1", "KR", ...])
#
# ENDPOINT 3: GET /seasons
#   Cevap: Season listesi
#
# ENDPOINT 4: GET /seasons/active
#   Cevap: tek Season
#
# ARAŞTIR:
#   - Leaderboard pahalı bir sorgu olabilir ve saniyede değişmiyor. Basit bir
#     bellek içi cache (ör. 60 saniye) nasıl yapılır? functools.lru_cache neden
#     burada tek başına yeterli değil? (İpucu: süre dolması / TTL.)
#
# CEVAP:
#   - Basit TTL cache: bir dict'te anahtar = (platform, queue, limit, offset),
#     değer = (kayıt zamanı, sonuç). İstek gelince time.monotonic() ile kayıt
#     60 saniyeden yeniyse onu dön, değilse sorguyu çalıştırıp kaydet. Hazır
#     paket: cachetools.TTLCache.
#   - lru_cache'in süresi yok: ilk sonucu process yeniden başlayana kadar
#     döner; sync LP'yi güncellese de API eski listeyi gösterir. Ayrıca bütün
#     argümanları anahtar yapar; conn parametresi her istekte farklı bir nesne
#     olduğu için cache hiç tutmaz.
#   - Not: bellek içi cache her worker process'inde ayrıdır. Birden çok worker
#     ya da sunucu için ortak cache gerekirse Redis gibi bir şey kullanılır.
# =============================================================================

from fastapi import APIRouter, Depends, Query
from psycopg import Connection
from fastapi import Request
from api.limiter import limiter
from api.db import get_conn
from api.config import settings
from api.repositories import leaderboard as leaderboard_repo
from api.schemas.common import QueueType
from api.schemas.leaderboard import LeaderboardResponse
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter(
    prefix="/leaderboard",
    tags=["leaderboard"],
)


@router.get("", response_model=LeaderboardResponse)
@limiter.limit("200/minute")
def get_leaderboard(
    request: Request,
    season: int = Query(..., ge=2026),
    queue_type: QueueType = Query(
        default=QueueType.RANKED_SOLO
    ),
    limit: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
    ),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_conn),
):


    if not leaderboard_repo.season_exists(conn, season):
        raise HTTPException(
            status_code=404,
            detail="Season not found",
        )
    entries = leaderboard_repo.list_leaderboard(
        conn=conn,
        season=season,
        queue_type=queue_type.value,
        limit=limit,
        offset=offset,
    )

    total = leaderboard_repo.get_leaderboard_total(
        conn=conn,
        season=season,
        queue_type=queue_type.value,
    )

    return LeaderboardResponse(
        items=entries,
        total=total,
        limit=limit,
        offset=offset,
        season=season,
        queue_type=queue_type.value,
    )

