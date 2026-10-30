from api.services.pandascore_client import PandaScoreClient


def normalize_tournament(tournament: dict) -> dict:
    league = tournament.get("league") or {}
    serie = tournament.get("serie") or {}

    return {
        "id": tournament["id"],
        "name": tournament.get("name") or None,
        "slug": tournament.get("slug"),
        "begin_at": tournament.get("begin_at"),
        "end_at": tournament.get("end_at"),
        "league_id": (
            league.get("id")
            or tournament.get("league_id")
        ),
        "serie_id": (
            serie.get("id")
            or tournament.get("serie_id")
        ),
    }


def list_series_tournaments(
    series_id: int,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    tournaments = []

    with PandaScoreClient() as client:
        page = 1

        while True:
            batch = client.get_series_tournaments(
                series_id=series_id,
                page=page,
                per_page=100,
            )

            if not batch:
                break

            tournaments.extend(batch)

            if len(batch) < 100:
                break

            page += 1

    tournaments.sort(
        key=lambda item: (
            item.get("begin_at") or "",
            item["id"],
        ),
        reverse=True,
    )

    return {
        "series_id": series_id,
        "total": len(tournaments),
        "limit": limit,
        "offset": offset,
        "items": [
            normalize_tournament(item)
            for item in tournaments[offset:offset + limit]
        ],
    }


def get_tournament_detail(tournament_id: int) -> dict:
    with PandaScoreClient() as client:
        tournament = client.get_tournament(tournament_id)

    return {
        **normalize_tournament(tournament),
        "winner_id": tournament.get("winner_id"),
    }