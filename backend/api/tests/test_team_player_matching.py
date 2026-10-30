from api.services.team_player_matching import match_roster_player


def test_match_player_with_different_spacing():
    pro_player = {
        "nickname": "BrokenBlade",
        "nationality": "DE",
    }

    local_players = [
        {
            "id": 530,
            "nickname": "Broken Blade",
            "country_code": "DE",
        }
    ]

    result = match_roster_player(pro_player, local_players)

    assert result is not None
    assert result["id"] == 530


def test_match_player_not_found():
    pro_player = {
        "nickname": "UnknownPlayer",
        "nationality": "DE",
    }

    local_players = [
        {
            "id": 530,
            "nickname": "Broken Blade",
            "country_code": "DE",
        }
    ]

    assert match_roster_player(pro_player, local_players) is None


def test_match_player_ambiguous():
    pro_player = {
        "nickname": "Example",
        "nationality": None,
    }

    local_players = [
        {"id": 1, "nickname": "Example", "country_code": "DE"},
        {"id": 2, "nickname": "Example", "country_code": "FR"},
    ]

    assert match_roster_player(pro_player, local_players) is None