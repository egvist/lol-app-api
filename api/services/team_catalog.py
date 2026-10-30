import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def list_team_catalog(
    season: int,
    league_id: int | None = None,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    path = DATA_DIR / f"emea_teams_{season}.json"

    if not path.is_file():
        raise FileNotFoundError(
            f"Team catalog not found for season {season}"
        )

    teams = json.loads(path.read_text(encoding="utf-8"))

    if league_id is not None:
        teams = [
            team for team in teams
            if league_id in team["league_ids"]
        ]

    if search:
        query = search.strip().casefold()
        teams = [
            team for team in teams
            if query in (team.get("name") or "").casefold()
        ]

    teams.sort(
        key=lambda team: (
            (team.get("name") or "").casefold(),
            team["id"],
        )
    )

    return {
        "season": season,
        "total": len(teams),
        "limit": limit,
        "offset": offset,
        "items": teams[offset:offset + limit],
    }