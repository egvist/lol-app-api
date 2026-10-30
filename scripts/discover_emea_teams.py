import argparse
import json
from pathlib import Path

from api.services.pandascore_client import PandaScoreClient
from api.services.team_discovery import discover_emea_teams
from api.services.emea_leagues import EMEA_LEAGUES


OUTPUT = Path("data/emea_teams_2026.json")

TEST_LEAGUES = [
    4197,  # LEC
    4292,  # LFL
    1003,  # TCL
    4743,  # LFL Division 2
    4962,  # Arabian League
]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--all",
        action="store_true",
        help="Discover teams from all configured EMEA leagues",
    )

    args = parser.parse_args()

    league_ids = (
        list(EMEA_LEAGUES)
        if args.all
        else TEST_LEAGUES
    )

    with PandaScoreClient() as client:
        teams = discover_emea_teams(
            client=client,
            league_ids=league_ids,
            season=2026,
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            teams,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\nEMEA TEAM DISCOVERY")
    print("-" * 60)
    print("Leagues scanned:", len(league_ids))
    print("Unique teams:", len(teams))
    print("Saved to:", OUTPUT)

    for team in teams:
        print(
            f"{team['id']:>7} | "
            f"{(team['name'] or ''):<30} | "
            f"Leagues: {len(team['league_ids'])} | "
            f"Series: {len(team['series_ids'])}"
        )


if __name__ == "__main__":
    main()