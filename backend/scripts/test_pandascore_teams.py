from pprint import pprint

from api.services.pandascore_client import PandaScoreClient


def main():
    with PandaScoreClient() as client:

        # Takım arama
        teams = client.get_teams(
            search="G2",
            per_page=5,
        )

        print("\n=== TEAM SEARCH ===")
        print("Total returned:", len(teams))

        for team in teams:
            print({
                "id": team.get("id"),
                "name": team.get("name"),
                "acronym": team.get("acronym"),
            })

        # Takım detayları
        team = client.get_team(88)

        print("\n=== TEAM DETAIL ===")
        print("Fields:", list(team.keys()))

        print("\n=== TEAM DATA ===")
        pprint({
            "id": team.get("id"),
            "name": team.get("name"),
            "acronym": team.get("acronym"),
            "location": team.get("location"),
            "image_url": team.get("image_url"),
            "players": team.get("players"),
        })


if __name__ == "__main__":
    main()