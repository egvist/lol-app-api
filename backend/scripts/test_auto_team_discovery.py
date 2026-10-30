from api.services.pandascore_client import PandaScoreClient
from api.services.team_discovery import discover_running_teams


def main():
    with PandaScoreClient() as client:
        teams = discover_running_teams(
            client,
            max_series=10,
        )

    print(f"DISCOVERED TEAMS: {len(teams)}")

    for team in teams:
        print(
            f"{team['id']:>7} | "
            f"{team['name']} | "
            f"Players: {team['players_count']}"
        )


if __name__ == "__main__":
    main()