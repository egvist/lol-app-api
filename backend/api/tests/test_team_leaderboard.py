from api.services.team_leaderboard import build_team_leaderboard


def make_team(team_id, tier, lp, count=5):
    return {
        "team_id": team_id,
        "roster": [
            {"solo_queue": {"tier": tier, "lp": lp}}
            for _ in range(count)
        ],
    }


def test_team_leaderboard_order():
    teams = [
        make_team(1, "MASTER", 1000),
        make_team(2, "CHALLENGER", 500),
        make_team(3, "GRANDMASTER", 1500),
    ]

    result = build_team_leaderboard(teams)

    assert [team["team_id"] for team in result] == [2, 3, 1]
    assert [team["position"] for team in result] == [1, 2, 3]


def test_ineligible_team_goes_last():
    teams = [
        make_team(1, "CHALLENGER", 2000, count=2),
        make_team(2, "MASTER", 500, count=5),
    ]

    result = build_team_leaderboard(teams)

    assert result[0]["team_id"] == 2
    assert result[0]["position"] == 1

    assert result[1]["team_id"] == 1
    assert result[1]["position"] is None