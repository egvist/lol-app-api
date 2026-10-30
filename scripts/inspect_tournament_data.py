import json

from api.services.pandascore_client import PandaScoreClient


def main():
    tournament_id = 21813  # LEC Summer 2026 Playoffs

    with PandaScoreClient() as client:
        standings = client.get_tournament_standings(
            tournament_id=tournament_id,
            page=1,
            per_page=3,
        )

        matches = client.get_tournament_matches(
            tournament_id=tournament_id,
            page=1,
            per_page=2,
        )

    print("\nSTANDINGS")
    print("-" * 60)

    print(json.dumps(
        standings,
        indent=2,
        ensure_ascii=False,
    ))

    print("\nMATCHES")
    print("-" * 60)

    print(json.dumps(
        matches,
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()