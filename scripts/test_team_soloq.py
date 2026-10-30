from api.db import connection_pool
from api.services.team_leaderboard import get_team_soloq_roster


def main():
    with connection_pool.connection() as conn:
        roster = get_team_soloq_roster(
            conn=conn,
            team_id=88,
            season=2026,
        )

    for player in roster:
        print(
            player["nickname"],
            "=>",
            player["solo_queue"],
        )


if __name__ == "__main__":
    connection_pool.open()
    try:
        main()
    finally:
        connection_pool.close()