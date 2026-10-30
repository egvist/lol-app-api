from api.services.pandascore_client import PandaScoreClient


def main():
    with PandaScoreClient() as client:

        series = client.get_running_lol_series(
            page=1,
            per_page=10,
        )

        print("RUNNING SERIES:", len(series))

        for item in series:
            league = item.get("league") or {}

            print({
                "id": item.get("id"),
                "name": item.get("name"),
                "league": league.get("name"),
                "begin_at": item.get("begin_at"),
                "end_at": item.get("end_at"),
            })

        if not series:
            print("No running series found.")
            return

        series_id = series[0]["id"]

        teams = client.get_series_teams(
            series_id=series_id,
            per_page=100,
        )

        print("\nSERIES ID:", series_id)
        print("TEAMS FOUND:", len(teams))

        for team in teams:
            print({
                "id": team.get("id"),
                "name": team.get("name"),
                "acronym": team.get("acronym"),
                "players_count": len(team.get("players") or []),
            })


if __name__ == "__main__":
    main()