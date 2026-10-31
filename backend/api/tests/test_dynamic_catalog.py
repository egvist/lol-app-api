from api.services import league_catalog, team_catalog


class FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def get_lol_leagues(self, page=1, per_page=100):
        return [{'id': 8, 'name': 'New League', 'slug': 'new-league'}, {'id': 4, 'name': 'Old League'}] if page == 1 else []

    def get_teams(self, page=1, per_page=100, search=None):
        return [{'id': 10, 'name': 'New Team', 'image_url': None}] if page == 1 else []

    def get_league_series(self, league_id, page=1, per_page=100):
        return [{'id': 100, 'begin_at': '2026-01-01', 'end_at': '2026-03-01'},
                {'id': 101, 'begin_at': '2025-01-01', 'end_at': '2025-03-01'}] if page == 1 else []

    def get_series_teams(self, series_id, page=1, per_page=100):
        return [{'id': 10, 'name': 'New Team'}] if series_id == 100 and page == 1 else []


def test_leagues_without_json(monkeypatch):
    monkeypatch.setattr(league_catalog, 'PandaScoreClient', FakeClient)
    assert league_catalog.list_leagues(search='New')['items'][0]['id'] == 8
    assert league_catalog.get_league_detail(4)['name'] == 'Old League'
    assert league_catalog.get_league_detail(999) is None


def test_general_teams_without_json(monkeypatch):
    monkeypatch.setattr(team_catalog, 'PandaScoreClient', FakeClient)
    result = team_catalog.list_team_catalog(season=2026)
    assert result['items'][0]['id'] == 10
    assert result['items'][0]['league_ids'] == []


def test_league_teams_from_current_series(monkeypatch):
    monkeypatch.setattr(team_catalog, 'PandaScoreClient', FakeClient)
    result = team_catalog.list_team_catalog(season=2026, league_id=8)
    assert result['total'] == 1
    assert result['items'][0]['series_ids'] == [100]
    assert team_catalog.list_team_catalog(season=2027, league_id=8)['total'] == 0
