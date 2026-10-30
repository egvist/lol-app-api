from api.services.pandascore_client import PandaScoreClient


def series_in_season(
    series: dict,
    season: int,
) -> bool:
    start = series.get("begin_at")
    end = series.get("end_at")

    year_start = f"{season}-01-01"
    year_end = f"{season + 1}-01-01"

    if not start and not end:
        return False

    # Eksik sınırları mevcut tarih ile doldur.
    start = start or end
    end = end or start

    # Serinin tarih aralığı, istenen yılla kesişiyor mu?
    return start[:10] < year_end and end[:10] >= year_start


def list_league_series(
    league_id: int,
    season: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:

    series = []

    with PandaScoreClient() as client:
        page = 1

        while True:
            batch = client.get_league_series(
                league_id=league_id,
                page=page,
                per_page=100,
            )

            if not batch:
                break

            series.extend(batch)

            if len(batch) < 100:
                break

            page += 1

    if season is not None:
        series = [
            item
            for item in series
            if series_in_season(item, season)
        ]

    series.sort(
        key=lambda item: (
            item.get("begin_at") or "",
            item["id"],
        ),
        reverse=True,
    )

    items = [
        {
            "id": item["id"],
            "name": item.get("name") or None,
            "begin_at": item.get("begin_at"),
            "end_at": item.get("end_at"),
        }
        for item in series[offset:offset + limit]
    ]

    return {
        "league_id": league_id,
        "season": season,
        "total": len(series),
        "limit": limit,
        "offset": offset,
        "items": items,
    }