import json

from api.services import league_catalog
from api.services import team_catalog


def test_list_leagues(tmp_path, monkeypatch):
    path = tmp_path / "pandascore_lol_leagues.json"

    path.write_text(
        json.dumps([
            {"id": 4197, "name": "LEC"},
            {"id": 4292, "name": "LFL"},
            {"id": 1003, "name": "TCL"},
        ]),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        league_catalog,
        "LEAGUES_FILE",
        path,
    )

    result = league_catalog.list_leagues(search="L")

    assert result["total"] == 3

    result = league_catalog.list_leagues(search="LFL")

    assert result["total"] == 1
    assert result["items"][0]["id"] == 4292


def test_get_league_detail(tmp_path, monkeypatch):
    path = tmp_path / "pandascore_lol_leagues.json"

    path.write_text(
        json.dumps([
            {"id": 4197, "name": "LEC"},
        ]),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        league_catalog,
        "LEAGUES_FILE",
        path,
    )

    assert league_catalog.get_league_detail(4197)["name"] == "LEC"
    assert league_catalog.get_league_detail(9999) is None


def test_get_league_teams(tmp_path, monkeypatch):
    path = tmp_path / "emea_teams_2026.json"

    path.write_text(
        json.dumps([
            {
                "id": 88,
                "name": "G2 Esports",
                "league_ids": [4197],
                "series_ids": [10756],
            },
            {
                "id": 200,
                "name": "Test Team",
                "league_ids": [4292],
                "series_ids": [10814],
            },
        ]),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        team_catalog,
        "DATA_DIR",
        tmp_path,
    )

    result = league_catalog.get_league_teams(
        league_id=4197,
        season=2026,
    )

    assert result["total"] == 1
    assert result["items"][0]["name"] == "G2 Esports"
    assert result["league_id"] == 4197