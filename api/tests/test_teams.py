import pytest

from api.services import team_service
from api.services.pandascore_client import PandaScoreError


# --------------------------------------------------
# Fake PandaScore Client
# --------------------------------------------------

class FakePandaScoreClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def get_teams(self, search=None, page=1, per_page=20):
        return [
            {
                "id": 88,
                "name": "G2 Esports",
                "acronym": "G2",
                "location": "DE",
                "image_url": "g2.png",
            }
        ]

    def get_team(self, team_id):
        return {
            "id": team_id,
            "name": "G2 Esports",
            "acronym": "G2",
            "location": "DE",
            "image_url": "g2.png",
            "players": [
                {
                    "id": 1718,
                    "name": "BrokenBlade",
                    "first_name": "Sergen",
                    "last_name": "Çelik",
                    "nationality": "DE",
                    "role": "top",
                    "image_url": "bb.png",
                    "active": True,
                }
            ],
        }


# --------------------------------------------------
# Test 1 — Team List
# --------------------------------------------------

def test_team_list(monkeypatch):
    monkeypatch.setattr(
        team_service,
        "PandaScoreClient",
        FakePandaScoreClient,
    )

    teams = team_service.get_team_list(search="G2")

    assert len(teams) == 1
    assert teams[0]["id"] == 88
    assert teams[0]["name"] == "G2 Esports"


# --------------------------------------------------
# Test 2 — Team Detail
# --------------------------------------------------

def test_team_detail(monkeypatch):
    monkeypatch.setattr(
        team_service,
        "PandaScoreClient",
        FakePandaScoreClient,
    )

    team = team_service.get_team_detail(88)

    assert team["id"] == 88
    assert team["name"] == "G2 Esports"
    assert len(team["roster"]) == 1
    assert team["roster"][0]["nickname"] == "BrokenBlade"
    assert team["roster"][0]["active"] is True


# --------------------------------------------------
# Test 3 — Empty Roster
# --------------------------------------------------

def test_empty_roster(monkeypatch):

    class EmptyRosterClient(FakePandaScoreClient):
        def get_team(self, team_id):
            team = super().get_team(team_id)
            team["players"] = []
            return team

    monkeypatch.setattr(
        team_service,
        "PandaScoreClient",
        EmptyRosterClient,
    )

    team = team_service.get_team_detail(88)

    assert team["roster"] == []


# --------------------------------------------------
# Test 4 — PandaScore Error
# --------------------------------------------------

def test_team_service_error(monkeypatch):

    class FailingClient(FakePandaScoreClient):
        def get_team(self, team_id):
            raise PandaScoreError("API unavailable")

    monkeypatch.setattr(
        team_service,
        "PandaScoreClient",
        FailingClient,
    )

    with pytest.raises(PandaScoreError):
        team_service.get_team_detail(88)