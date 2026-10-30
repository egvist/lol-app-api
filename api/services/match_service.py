from typing import Literal

from api.services.pandascore_client import PandaScoreClient
from api.services.tournament_results import normalize_match


MatchStatus = Literal["finished", "running", "not_started"]


def fetch_matches(
    kind: Literal["league", "team"],
    entity_id: int,
    limit: int = 20,
    offset: int = 0,
    status: MatchStatus | None = None,
) -> dict:
    if kind not in ("league", "team"):
        raise ValueError("Invalid match resource")

    matches = []
    page = 1

    with PandaScoreClient() as client:
        while True:
            if kind == "league":
                batch = client.get_league_matches(
                    league_id=entity_id,
                    page=page,
                    per_page=100,
                    status=status,
                )
            else:
                batch = client.get_team_matches(
                    team_id=entity_id,
                    page=page,
                    per_page=100,
                    status=status,
                )

            if not batch:
                break

            matches.extend(batch)

            if len(batch) < 100:
                break

            page += 1

    # Defense in depth: filtreyi yerelde de uygula.
    if status is not None:
        matches = [
            match
            for match in matches
            if match.get("status") == status
        ]

    matches.sort(
        key=lambda match: (
            match.get("scheduled_at") or "",
            match["id"],
        ),
        reverse=True,
    )

    return {
        "total": len(matches),
        "limit": limit,
        "offset": offset,
        "items": [
            normalize_match(match)
            for match in matches[offset:offset + limit]
        ],
    }