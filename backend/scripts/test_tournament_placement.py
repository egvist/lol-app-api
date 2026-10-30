from pprint import pprint

from api.services.pandascore_client import PandaScoreClient


def main():
    tournament_id = 21813  # LEC Playoffs 2026

    with PandaScoreClient() as client:
        standings = client.get_tournament_standings(
            tournament_id=tournament_id,
        )

        print("DATA TYPE:", type(standings))
        print("TOTAL ENTRIES:", len(standings))

        pprint(standings[:3])


if __name__ == "__main__":
    main()