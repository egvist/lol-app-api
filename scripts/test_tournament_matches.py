from api.services.pandascore_client import PandaScoreClient
from api.services.player_career import find_last_result

def main():
    tournament_id = 21372  # EWC 2026 - Group A

    with PandaScoreClient() as client:
        matches = client.get_tournament_matches(
            tournament_id=tournament_id
        )
        result = find_last_result(
            matches=matches,
            team_id=126688,
        )

        print("LAST RESULT:", result)



if __name__ == "__main__":
    main()