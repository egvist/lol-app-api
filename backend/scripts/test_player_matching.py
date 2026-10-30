import psycopg
from psycopg.rows import dict_row

from api.config import settings
from api.services.pandascore_client import PandaScoreClient
from api.services.player_matching import match_player


def get_local_player(slug: str):
    with psycopg.connect(settings.dsn, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    nickname,
                    country_code,
                    main_role
                FROM players
                WHERE slug = %s
                """,
                (slug,),
            )

            return cur.fetchone()


def main():
    slug = "broken-blade"

    player = get_local_player(slug)

    if player is None:
        print("Player not found in PostgreSQL")
        return

    print("LOCAL PLAYER:", player)

    client = PandaScoreClient()

    try:
        candidates = client.get_player_candidates(player["nickname"])

        matched = match_player(player, candidates)

        if matched is None:
            print("No reliable match found")
            return

        print("\nMATCH FOUND")
        print("PandaScore ID:", matched["id"])
        print("Nickname:", matched["name"])
        print("First name:", matched.get("first_name"))
        print("Last name:", matched.get("last_name"))
        print("Team:", (matched.get("current_team") or {}).get("name"))

    finally:
        client.close()


if __name__ == "__main__":
    main()