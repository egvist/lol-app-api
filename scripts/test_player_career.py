from pprint import pprint
from api.services.pandascore_client import PandaScoreClient
from api.services.player_matching import match_player
from api.services.player_career import build_career_history

local_player = {
    "id": 530,
    "nickname": "Broken Blade",
    "country_code": "DE",
    "main_role": "TOP",
}

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