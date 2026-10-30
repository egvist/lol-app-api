import json
from pathlib import Path

from api.services.team_catalog import list_team_catalog


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

LEAGUES_FILE = DATA_DIR / "pandascore_lol_leagues.json"


def load_leagues() -> list[dict]:
    if not LEAGUES_FILE.is_file():
        raise FileNotFoundError(
            "PandaScore league catalog not found"
        )

    return json.loads(
        LEAGUES_FILE.read_text(encoding="utf-8")
    )


def list_leagues(
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:

    leagues = load_leagues()

    if search:
        query = search.strip().casefold()

        leagues = [
            league
            for league in leagues
            if query in (league.get("name") or "").casefold()
        ]

    leagues.sort(
        key=lambda league: (
            (league.get("name") or "").casefold(),
            league["id"],
        )
    )

    return {
        "total": len(leagues),
        "limit": limit,
        "offset": offset,
        "items": leagues[offset:offset + limit],
    }


def get_league_detail(
    league_id: int,
) -> dict | None:

    leagues = load_leagues()

    for league in leagues:
        if league["id"] == league_id:
            return league

    return None


def get_league_teams(
    league_id: int,
    season: int,
    limit: int = 20,
    offset: int = 0,
) -> dict:

    result = list_team_catalog(
        season=season,
        league_id=league_id,
        limit=limit,
        offset=offset,
    )

    return {
        "league_id": league_id,
        **result,
    }