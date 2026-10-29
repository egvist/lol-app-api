from api.services.player_career import find_last_result


def test_find_last_result():
    matches = [
        {
            "id": 100,
            "status": "finished",
            "end_at": "2026-07-15T12:00:00Z",
            "opponents": [
                {
                    "type": "Team",
                    "opponent": {"id": 88, "name": "G2 Esports"}
                },
                {
                    "type": "Team",
                    "opponent": {"id": 200, "name": "FURIA"}
                },
            ],
            "results": [
                {"team_id": 88, "score": 1},
                {"team_id": 200, "score": 0},
            ],
            "winner_id": 88,
        },
        {
            "id": 101,
            "status": "finished",
            "end_at": "2026-07-16T15:00:00Z",
            "opponents": [
                {
                    "type": "Team",
                    "opponent": {"id": 88, "name": "G2 Esports"}
                },
                {
                    "type": "Team",
                    "opponent": {"id": 300, "name": "Dplus KIA"}
                },
            ],
            "results": [
                {"team_id": 88, "score": 0},
                {"team_id": 300, "score": 2},
            ],
            "winner_id": 300,
        },
    ]

    result = find_last_result(matches, team_id=88)

    assert result is not None
    assert result["match_id"] == 101
    assert result["opponent"]["name"] == "Dplus KIA"
    assert result["team_score"] == 0
    assert result["opponent_score"] == 2
    assert result["winner_id"] == 300


def test_find_last_result_empty_matches():
    result = find_last_result([], team_id=88)

    assert result is None


def test_find_last_result_unrelated_team():
    matches = [
        {
            "id": 100,
            "status": "finished",
            "end_at": "2026-07-15T12:00:00Z",
            "opponents": [
                {"type": "Team", "opponent": {"id": 200, "name": "FURIA"}},
                {"type": "Team", "opponent": {"id": 300, "name": "Dplus KIA"}},
            ],
        }
    ]

    result = find_last_result(matches, team_id=88)

    assert result is None


def test_find_last_result_unfinished_match():
    matches = [
        {
            "id": 101,
            "status": "not_started",
            "end_at": None,
            "opponents": [
                {"type": "Team", "opponent": {"id": 88, "name": "G2 Esports"}},
                {"type": "Team", "opponent": {"id": 300, "name": "Dplus KIA"}},
            ],
        }
    ]

    result = find_last_result(matches, team_id=88)

    assert result is None