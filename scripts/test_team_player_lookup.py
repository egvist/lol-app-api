from api.db import connection_pool
from api.repositories import players as player_repo
from api.services.player_matching import normalize_name
from api.services.team_player_matching import match_roster_player
from api.services.team_service import get_team_detail


def main():
    team = get_team_detail(88)

    roster = team["roster"]

    normalized_names = [
        normalize_name(player["nickname"])
        for player in roster
    ]

    with connection_pool.connection() as conn:
        local_players = player_repo.find_players_by_names(
            conn,
            normalized_names,
        )

    print("TEAM:", team["name"])
    print("LOCAL CANDIDATES:", len(local_players))

    for pro_player in roster:
        matched = match_roster_player(
            pro_player,
            local_players,
        )

        print(
            pro_player["nickname"],
            "=>",
            matched["nickname"] if matched else "NOT MATCHED",
        )


if __name__ == "__main__":
    connection_pool.open()
    try:
        main()
    finally:
        connection_pool.close()