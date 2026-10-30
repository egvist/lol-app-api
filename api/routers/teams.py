from fastapi import APIRouter, HTTPException, Query

from api.schemas.teams import TeamSummary, TeamDetail, RosterPlayer
from api.services.team_service import get_team_list, get_team_detail
from api.services.pandascore_client import PandaScoreError
from fastapi import Depends
from psycopg import Connection
from api.schemas.team_leaderboard import TeamLeaderboardResponse
from api.services.team_leaderboard import get_teams_leaderboard
from api.db import get_conn
from api.repositories import leaderboard as leaderboard_repo
from api.schemas.team_leaderboard import TeamSoloQResponse
from api.services.team_leaderboard import get_team_soloq
from fastapi import Query
from api.schemas.team_catalog import TeamCatalogResponse
from api.services.team_catalog import list_team_catalog
from typing import Literal

from api.schemas.matches import MatchesResponse
from api.services.match_service import fetch_matches
from api.services.pandascore_limiter import PandaScoreRateLimitError

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=list[TeamSummary])
def list_teams(
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
):
    try:
        return get_team_list(search, page, per_page)
    except PandaScoreError:
        raise HTTPException(503, "Team data unavailable")
@router.get(
    "/leaderboard",
    response_model=TeamLeaderboardResponse,
)
def team_leaderboard(
    limit: int = Query(default=10, ge=1, le=20),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_conn),
):
    season = leaderboard_repo.get_active_season_year(conn)

    if season is None:
        raise HTTPException(
            status_code=503,
            detail="Active ranked season unavailable",
        )

    try:
        return get_teams_leaderboard(
            conn=conn,
            season=season,
            limit=limit,
            offset=offset,
        )
    except PandaScoreError as exc:
        raise HTTPException(
            status_code=503,
            detail="Team leaderboard unavailable",
        ) from exc
    
@router.get(
    "/catalog",
    response_model=TeamCatalogResponse,
)
def team_catalog(
    season: int = Query(default=2026, ge=2020),
    league_id: int | None = Query(default=None, ge=1),
    search: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return list_team_catalog(
            season=season,
            league_id=league_id,
            search=search,
            limit=limit,
            offset=offset,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc



    
@router.get("/{team_id}", response_model=TeamDetail)
def team_detail(team_id: int):
    try:
        return get_team_detail(team_id)
    except PandaScoreError as exc:
        raise HTTPException(503, "Team data unavailable") from exc


@router.get("/{team_id}/roster", response_model=list[RosterPlayer])
def team_roster(team_id: int):
    try:
        team = get_team_detail(team_id)
        return team["roster"]
    except PandaScoreError as exc:
        raise HTTPException(503, "Roster unavailable") from exc


@router.get(
    "/{team_id}/soloq",
    response_model=TeamSoloQResponse,
)
def team_soloq(
    team_id: int,
    conn: Connection = Depends(get_conn),
):
    season = leaderboard_repo.get_active_season_year(conn)

    if season is None:
        raise HTTPException(
            status_code=503,
            detail="Active ranked season unavailable",
        )

    try:
        return get_team_soloq(
            conn=conn,
            team_id=team_id,
            season=season,
        )

    except PandaScoreError as exc:
        raise HTTPException(
            status_code=503,
            detail="Team SoloQ data unavailable",
        ) from exc


@router.get(
    "/{team_id}/matches",
    response_model=MatchesResponse,
)
def team_matches(
    team_id: int,
    status: Literal["finished", "running", "not_started"] | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return fetch_matches(
            kind="team",
            entity_id=team_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Team matches unavailable",
        ) from exc