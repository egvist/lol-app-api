
from fastapi import Query
from fastapi import APIRouter, Query, Depends, HTTPException, Path, BackgroundTasks
from api.db import get_conn
from api.services.rank_refresh import refresh_player_ranks
from api.config import settings
from api.schemas.common import Page, Role
from api.schemas.player import PlayerSummary, PlayerDetail
from api.schemas.account import SeasonRank
from api.repositories import players as player_repo
from psycopg import Connection
from api.schemas.pro import ProProfileResponse
from api.services.player_enrichment import get_pro_profile
from api.schemas.career import CareerHistoryResponse
from api.services.player_career import get_player_career
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
def get_player_ranks(
    background_tasks: BackgroundTasks,
    slug: str = Path(min_length=1),
    season: int = Query(...),
    conn: Connection = Depends(get_conn),
):
    player = player_repo.get_player_by_slug(conn, slug)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    # Yalnızca ACTIVE sezon isteklerinde otomatik yenile.
    with conn.cursor() as cur:
        cur.execute("SELECT season_year FROM ranked_seasons WHERE status='ACTIVE'")
        active = cur.fetchone()
    if active is not None:
        active_year = active["season_year"] if isinstance(active, dict) else active[0]
        if active_year == season:
            background_tasks.add_task(refresh_player_ranks, player["id"])

    # Stale-while-revalidate: ilk istekte eski veri (veya []) gelir.
    return player_repo.get_player_ranks(conn, player["id"], season)

@router.get("/{slug}/pro-profile", response_model = ProProfileResponse)
def get_player_pro_profile(slug: str, conn: Connection = Depends(get_conn)):
    player = player_repo.get_player_by_slug(conn, slug)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )
    print("PLAYER:", player)
    print("PLAYER TYPE:", type(player))
    return get_pro_profile(dict(player))

@router.get(
    "/{slug}/career",
    response_model=CareerHistoryResponse,
)
def get_player_career_endpoint(
    slug: str,
    limit: int = Query(default=5, ge=1, le=5),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_conn),
):
    player = player_repo.get_player_by_slug(conn, slug)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    return get_player_career(
        local_player=dict(player),
        limit=limit,
        offset=offset,
    )
