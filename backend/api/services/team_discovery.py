from api.services.pandascore_client import PandaScoreClient


def discover_running_teams(
    client: PandaScoreClient,
    max_series: int = 20,
) -> list[dict]:
    discovered = {}

    page = 1
    processed_series = 0

    while processed_series < max_series:
        series = client.get_running_lol_series(
            page=page,
            per_page=20,
        )

        if not series:
            break

        for item in series:
            if processed_series >= max_series:
                break

            series_id = item["id"]
            processed_series += 1

            team_page = 1

            while True:
                teams = client.get_series_teams(
                    series_id=series_id,
                    page=team_page,
                    per_page=100,
                )

                if not teams:
                    break

                for team in teams:
                    team_id = team.get("id")

                    if not isinstance(team_id, int):
                        continue

                    if team_id not in discovered:
                        discovered[team_id] = {
                            "id": team_id,
                            "name": team.get("name"),
                            "acronym": team.get("acronym"),
                            "image_url": team.get("image_url"),
                            "players_count": len(
                                team.get("players") or []
                            ),
                        }

                if len(teams) < 100:
                    break

                team_page += 1

        if len(series) < 20:
            break

        page += 1

    return sorted(
        discovered.values(),
        key=lambda team: (
            (team["name"] or "").casefold(),
            team["id"],
        ),
    )

def discover_emea_teams(
    client: PandaScoreClient,
    league_ids: list[int],
    season: int = 2026,
) -> list[dict]:
    discovered: dict[int, dict] = {}

    for league_id in league_ids:
        print(f"Discovering league {league_id}...")

        series_page = 1

        while True:
            series_batch = client.get_league_series(
                league_id=league_id,
                page=series_page,
                per_page=100,
            )

            if not series_batch:
                break

            for series in series_batch:
                begin_at = series.get("begin_at") or ""
                end_at = series.get("end_at") or ""

                if not (
                    begin_at.startswith(str(season))
                    or end_at.startswith(str(season))
                ):
                    continue

                series_id = series["id"]
                team_page = 1

                while True:
                    teams = client.get_series_teams(
                        series_id=series_id,
                        page=team_page,
                        per_page=100,
                    )

                    if not teams:
                        break

                    for team in teams:
                        team_id = team.get("id")

                        if not isinstance(team_id, int):
                            continue

                        if team_id not in discovered:
                            discovered[team_id] = {
                                "id": team_id,
                                "name": team.get("name"),
                                "acronym": team.get("acronym"),
                                "image_url": team.get("image_url"),
                                "league_ids": [],
                                "series_ids": [],
                            }

                        entry = discovered[team_id]

                        if league_id not in entry["league_ids"]:
                            entry["league_ids"].append(league_id)

                        if series_id not in entry["series_ids"]:
                            entry["series_ids"].append(series_id)

                    if len(teams) < 100:
                        break

                    team_page += 1

            if len(series_batch) < 100:
                break

            series_page += 1

    return sorted(
        discovered.values(),
        key=lambda team: (
            (team["name"] or "").casefold(),
            team["id"],
        ),
    )