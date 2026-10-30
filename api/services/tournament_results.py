from api.services.pandascore_client import PandaScoreClient


def normalize_team(team: dict) -> dict:
    return {
        "id": team["id"],
        "name": team["name"],
        "acronym": team.get("acronym"),
        "image_url": team.get("image_url"),
    }


def normalize_standing(entry: dict) -> dict:
    return {
        "rank": entry["rank"],
        "team": normalize_team(entry["team"]),
    }


def normalize_match(match: dict) -> dict:
    scores = {
        result["team_id"]: result["score"]
        for result in match.get("results") or []
        if result.get("team_id") is not None
    }

    opponents = []

    for entry in match.get("opponents") or []:
        team = entry.get("opponent")

        if not team:
            continue

        opponents.append({
            "team": normalize_team(team),
            "score": scores.get(team["id"]),
        })

    games = []

    for game in match.get("games") or []:
        winner = game.get("winner") or {}

        games.append({
            "id": game["id"],
            "position": game["position"],
            "status": game.get("status"),
            "winner_id": winner.get("id"),
        })

    games.sort(key=lambda game: game["position"])

    return {
        "id": match["id"],
        "name": match.get("name"),
        "status": match["status"],
        "scheduled_at": match.get("scheduled_at"),
        "begin_at": match.get("begin_at"),
        "end_at": match.get("end_at"),
        "winner_id": match.get("winner_id"),
        "number_of_games": match.get("number_of_games"),
        "league_id": match.get("league_id"),
        "serie_id": match.get("serie_id"),
        "tournament_id": match["tournament_id"],
        "opponents": opponents,
        "games": games,
    }


def get_all_tournament_records(
    client: PandaScoreClient,
    tournament_id: int,
    kind: str,
) -> list[dict]:
    records = []
    page = 1

    while True:
        if kind == "standings":
            batch = client.get_tournament_standings(
                tournament_id=tournament_id,
                page=page,
                per_page=100,
            )

        elif kind == "matches":
            batch = client.get_tournament_matches(
                tournament_id=tournament_id,
                page=page,
                per_page=100,
            )

        else:
            raise ValueError(f"Unsupported record kind: {kind}")

        if not batch:
            break

        records.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return records


def list_tournament_standings(
    tournament_id: int,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    with PandaScoreClient() as client:
        standings = get_all_tournament_records(
            client,
            tournament_id,
            "standings",
        )

    standings.sort(key=lambda entry: entry["rank"])

    return {
        "tournament_id": tournament_id,
        "total": len(standings),
        "limit": limit,
        "offset": offset,
        "items": [
            normalize_standing(entry)
            for entry in standings[offset:offset + limit]
        ],
    }


def list_tournament_matches(
    tournament_id: int,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    with PandaScoreClient() as client:
        matches = get_all_tournament_records(
            client,
            tournament_id,
            "matches",
        )

    matches.sort(
        key=lambda match: (
            match.get("scheduled_at") or "",
            match["id"],
        ),
        reverse=True,
    )

    return {
        "tournament_id": tournament_id,
        "total": len(matches),
        "limit": limit,
        "offset": offset,
        "items": [
            normalize_match(match)
            for match in matches[offset:offset + limit]
        ],
    }