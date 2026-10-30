

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

