from api.services.team_soloq_summary import (
    calculate_team_soloq_summary,
)


def test_team_soloq_summary():
    roster = [
        {"solo_queue": {"tier": "CHALLENGER", "lp": 2740}},
        {"solo_queue": {"tier": "GRANDMASTER", "lp": 1854}},
        {"solo_queue": {"tier": "GRANDMASTER", "lp": 1890}},
        {"solo_queue": {"tier": "CHALLENGER", "lp": 2469}},
        {"solo_queue": {"tier": "CHALLENGER", "lp": 2810}},
    ]

    result = calculate_team_soloq_summary(roster)

    assert result["total_players"] == 5
    assert result["ranked_players"] == 5
    assert result["average_lp"] == 2352.6
    assert result["challenger_count"] == 3
    assert result["grandmaster_count"] == 2


def test_team_soloq_summary_no_ranks():
    roster = [
        {"solo_queue": None},
        {"solo_queue": None},
    ]

    result = calculate_team_soloq_summary(roster)

    assert result["total_players"] == 2
    assert result["ranked_players"] == 0
    assert result["average_lp"] is None