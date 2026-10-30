from pprint import pprint
from api.services.pandascore_client import PandaScoreClient
from api.services.player_matching import match_player
from api.services.player_career import build_career_history, extract_placement

local_player = {
    "id": 530,
    "nickname": "Broken Blade",
    "country_code": "DE",
    "main_role": "TOP",
}

def test_extract_placement():
    standings = [
        {"rank": 1, "team": {"id": 88}},
        {"rank": 2, "team": {"id": 100}},
        {"rank": 3, "team": {"id": 200}},
        {"rank": 11, "team": {"id": 300}},
    ]

    assert extract_placement(standings, 88) == "1st"
    assert extract_placement(standings, 100) == "2nd"
    assert extract_placement(standings, 200) == "3rd"
    assert extract_placement(standings, 300) == "11th"
    assert extract_placement(standings, 999) is None
    assert extract_placement([], 88) is None

def main():
    with PandaScoreClient() as client:
        candidates = client.get_player_candidates(local_player["nickname"])

        player = match_player(local_player, candidates)

        if player is None:
            print("No reliable player match")
            return

        print("PANDASCORE PLAYER")
        print("ID:", player["id"])
        print("Nickname:", player["name"])

        tournaments = client.get_all_player_tournaments(
            player_id=player["id"]
        )

        print("Total tournaments:", len(tournaments))

        history = build_career_history(
            tournaments=tournaments,
            player_id=player["id"],
        )

        print("Career entries:", len(history))

        for entry in history:
            print(
                entry["begin_at"],
                "|",
                entry["team"]["name"],
                "|",
                entry["league_name"],
                "-",
                entry["tournament_name"],
            )


if __name__ == "__main__":
    main()