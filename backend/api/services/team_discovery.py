from api.services.pandascore_client import PandaScoreClient
from api.services.emea_leagues import EMEA_LEAGUES
from api.services.league_series import series_in_season


def discover_running_teams(
    client: PandaScoreClient,
    max_series: int = 20,
    season: int = 2026,
) -> list[dict]:
    discovered = {}
    page = 1
    processed_series = 0
    # Cap the scan to avoid unbounded PandaScore requests when no EMEA series runs.
    max_pages = 5
    per_page = 20

    while processed_series < max_series and page <= max_pages:
        series = client.get_running_lol_series(page=page, per_page=per_page)
        if not series:
            break

        for item in series:
            if processed_series >= max_series:
                break

            # PandaScore series may expose either league_id or a nested league.
            league_id = item.get("league_id")
            if league_id is None:
                league = item.get("league") or {}
                league_id = league.get("id")
            if league_id not in EMEA_LEAGUES:
                continue

            series_id = item["id"]
            processed_series += 1
            team_page = 1
            while True:
                teams = client.get_series_teams(
                    series_id=series_id, page=team_page, per_page=100,
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
                            "players_count": len(team.get("players") or []),
                        }
                if len(teams) < 100:
                    break
                team_page += 1

        if len(series) < per_page:
            break
        page += 1

    # Fall back only when no EMEA running series was found.
    # Cap league calls to leave headroom for roster requests under the 50/min limiter.
    if processed_series == 0 and max_series > 0:
        # Current regional leagues first; older/historical leagues are intentionally omitted.
        fallback_league_ids = [
            4197, 4292, 4302, 1003, 4213, 4405,
            4300, 4411, 4401, 4402, 4426, 4962,
        ]
        seen_series_ids = set()
        for league_id in fallback_league_ids:
            if processed_series >= max_series:
                break
            batch = client.get_league_series(
                league_id=league_id, page=1, per_page=20,
            )
            for item in batch:
                if processed_series >= max_series:
                    break
                series_id = item.get("id")
                if not isinstance(series_id, int) or series_id in seen_series_ids:
                    continue
                if not series_in_season(item, season):
                    continue
                seen_series_ids.add(series_id)
                processed_series += 1
                team_page = 1
                while True:
                    teams = client.get_series_teams(
                        series_id=series_id, page=team_page, per_page=100,
                    )
                    if not teams:
                        break
                    for team in teams:
                        team_id = team.get("id")
                        if not isinstance(team_id, int):
                            continue
                        discovered.setdefault(team_id, {
                            "id": team_id,
                            "name": team.get("name"),
                            "acronym": team.get("acronym"),
                            "image_url": team.get("image_url"),
                            "players_count": len(team.get("players") or []),
                        })
                    if len(teams) < 100:
                        break
                    team_page += 1

    return sorted(
        discovered.values(),
        key=lambda team: ((team["name"] or "").casefold(), team["id"]),
    )
