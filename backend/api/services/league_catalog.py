"""Live PandaScore league catalog; no local JSON data dependency."""
from api.services.pandascore_client import PandaScoreClient
from api.services.team_catalog import list_team_catalog


def load_leagues() -> list[dict]:
    leagues = []
    with PandaScoreClient() as client:
        page = 1
        while True:
            batch = client.get_lol_leagues(page=page, per_page=100)
            leagues.extend(batch)
            if len(batch) < 100:
                break
            page += 1
    return leagues


def list_leagues(search: str | None = None, limit: int = 20, offset: int = 0) -> dict:
    leagues = load_leagues()
    if search:
        query = search.strip().casefold()
        leagues = [league for league in leagues if query in (league.get('name') or '').casefold()]
    leagues.sort(key=lambda league: ((league.get('name') or '').casefold(), league['id']))
    return {
        'total': len(leagues), 'limit': limit, 'offset': offset,
        'items': leagues[offset:offset + limit],
    }


def get_league_detail(league_id: int) -> dict | None:
    # PandaScoreClient already caches pages by parameters for one hour.
    return next((league for league in load_leagues() if league['id'] == league_id), None)


def get_league_teams(league_id: int, season: int, limit: int = 20, offset: int = 0) -> dict:
    result = list_team_catalog(season=season, league_id=league_id, limit=limit, offset=offset)
    return {'league_id': league_id, **result}
