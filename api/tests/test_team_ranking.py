from api.services.team_ranking import (
    calculate_player_score,
    calculate_team_ranking,
)


def test_challenger_beats_master():
    challenger = calculate_player_score({
        "tier": "CHALLENGER",
        "division": None,
        "lp": 100,
    })

    master = calculate_player_score({
        "tier": "MASTER",
        "division": None,
        "lp": 2000,
    })

    assert challenger > master


def test_higher_lp_same_tier():
    low = calculate_player_score({
        "tier": "GRANDMASTER",
        "division": None,
        "lp": 500,
    })

    high = calculate_player_score({
        "tier": "GRANDMASTER",
        "division": None,
        "lp": 1200,
    })

    assert high > low


def test_team_ranking():
    roster = [
        {"solo_queue": {"tier": "CHALLENGER", "lp": 2740}},
        {"solo_queue": {"tier": "GRANDMASTER", "lp": 1854}},
        {"solo_queue": {"tier": "GRANDMASTER", "lp": 1890}},
        {"solo_queue": {"tier": "CHALLENGER", "lp": 2469}},
        {"solo_queue": {"tier": "CHALLENGER", "lp": 2810}},
    ]

    result = calculate_team_ranking(roster)

    assert result["eligible"] is True
    assert result["ranked_players"] == 5
    assert result["ranking_score"] == 88352.6


def test_insufficient_ranked_players():
    roster = [
        {"solo_queue": {"tier": "MASTER", "lp": 500}},
        {"solo_queue": None},
        {"solo_queue": None},
    ]

    result = calculate_team_ranking(roster)

    assert result["eligible"] is False
    assert result["ranking_score"] is None


def test_unranked_player():
    assert calculate_player_score(None) is None