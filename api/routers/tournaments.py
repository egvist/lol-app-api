from fastapi import APIRouter, HTTPException, Query

from api.schemas.tournaments import (
    SeriesTournamentsResponse,
    TournamentDetail,
)
from api.services.tournament_service import (
    get_tournament_detail,
    list_series_tournaments,
)
from api.services.pandascore_client import PandaScoreError
from api.services.pandascore_limiter import PandaScoreRateLimitError
from api.schemas.tournament_results import (
    TournamentStandingsResponse,
    TournamentMatchesResponse,
)
from api.services.tournament_results import (
    list_tournament_standings,
    list_tournament_matches,
)

router = APIRouter(tags=["Tournaments"])


@router.get(
    "/series/{series_id}/tournaments",
    response_model=SeriesTournamentsResponse,
)
def series_tournaments(
    series_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return list_series_tournaments(
            series_id=series_id,
            limit=limit,
            offset=offset,
        )

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Tournament data unavailable",
        ) from exc


@router.get(
    "/tournaments/{tournament_id}",
    response_model=TournamentDetail,
)
def tournament_detail(tournament_id: int):
    try:
        return get_tournament_detail(tournament_id)

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Tournament data unavailable",
        ) from exc

@router.get(
    "/tournaments/{tournament_id}/standings",
    response_model=TournamentStandingsResponse,
)
def tournament_standings(
    tournament_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return list_tournament_standings(
            tournament_id=tournament_id,
            limit=limit,
            offset=offset,
        )

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Tournament standings unavailable",
        ) from exc


@router.get(
    "/tournaments/{tournament_id}/matches",
    response_model=TournamentMatchesResponse,
)
def tournament_matches(
    tournament_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return list_tournament_matches(
            tournament_id=tournament_id,
            limit=limit,
            offset=offset,
        )

    except (PandaScoreError, PandaScoreRateLimitError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Tournament matches unavailable",
        ) from exc