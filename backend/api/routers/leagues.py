from fastapi import APIRouter, HTTPException, Query

from api.schemas.leagues import (
    LeagueDetail,
    LeagueListResponse,
    LeagueTeamsResponse,
)
from api.services.league_catalog import (
    get_league_detail,
    get_league_teams,
    list_leagues,
)
from typing import Literal

from api.schemas.matches import MatchesResponse
from api.services.match_service import fetch_matches
from api.schemas.series import LeagueSeriesResponse
from api.services.league_series import list_league_series
from api.services.pandascore_client import PandaScoreError
from api.services.pandascore_limiter import PandaScoreRateLimitError

router = APIRouter(
    prefix="/leagues",
    tags=["Leagues"],
)


@router.get(
    "",
    response_model=LeagueListResponse,
)
def leagues_list(
    search: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return list_leagues(
            search=search,
            limit=limit,
            offset=offset,
        )
    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="PandaScore league data unavailable",
        ) from exc


@router.get(
    "/{league_id}/teams",
    response_model=LeagueTeamsResponse,
)
def league_teams(
    league_id: int,
    season: int = Query(default=2026, ge=2020),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        if get_league_detail(league_id) is None:
            raise HTTPException(
                status_code=404,
                detail="League not found",
            )

        return get_league_teams(
            league_id=league_id,
            season=season,
            limit=limit,
            offset=offset,
        )

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="PandaScore league teams unavailable",
        ) from exc
@router.get(
    "/{league_id}/series",
    response_model=LeagueSeriesResponse,
)
def league_series(
    league_id: int,
    season: int | None = Query(default=None, ge=2010),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        league = get_league_detail(league_id)

        if league is None:
            raise HTTPException(
                status_code=404,
                detail="League not found",
            )

        return list_league_series(
            league_id=league_id,
            season=season,
            limit=limit,
            offset=offset,
        )

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="PandaScore series data unavailable",
        ) from exc

@router.get(
    "/{league_id}",
    response_model=LeagueDetail,
)
def league_detail(
    league_id: int,
):
    try:
        league = get_league_detail(league_id)

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="PandaScore league data unavailable",
        ) from exc

    if league is None:
        raise HTTPException(
            status_code=404,
            detail="League not found",
        )

    return league

@router.get(
    "/{league_id}/matches",
    response_model=MatchesResponse,
)
def league_matches(
    league_id: int,
    status: Literal["finished", "running", "not_started"] | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        if get_league_detail(league_id) is None:
            raise HTTPException(
                status_code=404,
                detail="League not found",
            )

        return fetch_matches(
            kind="league",
            entity_id=league_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="League matches unavailable",
        ) from exc