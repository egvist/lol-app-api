"""Live PandaScore team catalog and season/league membership discovery.

General team listing is not a season-scoped roster. League-specific membership
is derived from the league's PandaScore series intersecting the requested year.
"""
from api.services.pandascore_client import PandaScoreClient
from api.services.league_series import series_in_season


def _normalize(team: dict, league_ids: list[int] | None = None,
               series_ids: list[int] | None = None) -> dict:
    return {
        'id': team['id'], 'name': team.get('name'),
        'acronym': team.get('acronym'), 'image_url': team.get('image_url'),
        'league_ids': league_ids or [], 'series_ids': series_ids or [],
    }


def _get_league_teams(client: PandaScoreClient, league_id: int, season: int) -> list[dict]:
    # Discover the actual participating teams instead of reading a 2026 snapshot.
    series = []
    page = 1
    while True:
        batch = client.get_league_series(league_id=league_id, page=page, per_page=100)
        series.extend(item for item in batch if series_in_season(item, season))
        if len(batch) < 100:
            break
        page += 1

    teams_by_id: dict[int, dict] = {}
    for serie in series:
        page = 1
        while True:
            batch = client.get_series_teams(series_id=serie['id'], page=page, per_page=100)
            for team in batch:
                if not team or team.get('id') is None:
                    continue
                ident = team['id']
                if ident not in teams_by_id:
                    teams_by_id[ident] = _normalize(team, [league_id], [])
                if serie['id'] not in teams_by_id[ident]['series_ids']:
                    teams_by_id[ident]['series_ids'].append(serie['id'])
            if len(batch) < 100:
                break
            page += 1
    return list(teams_by_id.values())


def list_team_catalog(season: int, league_id: int | None = None,
                      search: str | None = None, limit: int = 20,
                      offset: int = 0) -> dict:
    with PandaScoreClient() as client:
        if league_id is not None:
            teams = _get_league_teams(client, league_id, season)
        else:
            # No calendar-year filter exists on PandaScore's /lol/teams index.
            # This is the global current team index, not historical season membership.
            teams = []
            page = 1
            while True:
                batch = client.get_teams(page=page, per_page=100, search=search)
                teams.extend(_normalize(team) for team in batch)
                if len(batch) < 100:
                    break
                page += 1
    if search:
        query = search.strip().casefold()
        teams = [team for team in teams if query in (team.get('name') or '').casefold()]
    teams.sort(key=lambda team: ((team.get('name') or '').casefold(), team['id']))
    return {'season': season, 'total': len(teams), 'limit': limit,
            'offset': offset, 'items': teams[offset:offset + limit]}
