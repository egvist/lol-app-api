from api.services.team_leaderboard_analysis import (
    analyze_team_coverage,
)


def make_team(team_id, total, ranked, eligible):
    return {
        "team_id": team_id,
        "team_name": f"Team {team_id}",
        "summary": {
            "total_players": total,
            "ranked_players": ranked,
        },
        "ranking": {
            "eligible": eligible,
        },
    }


def test_coverage_analysis():
    teams = [
        make_team(1, 5, 5, True),
        make_team(2, 6, 3, True),
        make_team(3, 5, 0, False),
    ]

    result = analyze_team_coverage(teams)

    assert result["total_teams"] == 3
    assert result["eligible_teams"] == 2

    assert result["complete_teams"] == 1
    assert result["partial_teams"] == 1
    assert result["insufficient_teams"] == 1

    assert result["total_players"] == 16
    assert result["ranked_players"] == 8
    assert result["overall_coverage_percent"] == 50.0


def test_empty_leaderboard():
    result = analyze_team_coverage([])

    assert result["total_teams"] == 0
    assert result["eligible_teams"] == 0
    assert result["overall_coverage_percent"] == 0
    assert result["teams"] == []


def test_team_without_roster():
    result = analyze_team_coverage([
        make_team(1, 0, 0, False),
    ])

    assert result["insufficient_teams"] == 1
    assert result["teams"][0]["coverage_percent"] == 0