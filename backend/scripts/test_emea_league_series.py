from api.services.pandascore_client import PandaScoreClient
from api.services.emea_leagues import EMEA_LEAGUES


TEST_LEAGUE_IDS = [
    4197,  # LEC
    4292,  # LFL
    1003,  # TCL
    4743,  # LFL Division 2
    4962,  # Arabian League
]


def main():
    with PandaScoreClient() as client:
        for league_id in TEST_LEAGUE_IDS:
            print(
                f"\n{EMEA_LEAGUES[league_id]} "
                f"(ID: {league_id})"
            )
            print("-" * 60)

            series = client.get_league_series(
                league_id=league_id,
                page=1,
                per_page=100,
            )

            print("Fetched series:", len(series))

            current_series = [
                item
                for item in series
                if (
                    (item.get("begin_at") or "").startswith("2026")
                    or (item.get("end_at") or "").startswith("2026")
                )
            ]

            print("2026 series:", len(current_series))

            for item in current_series:
                print({
                    "id": item["id"],
                    "name": item.get("name"),
                    "begin_at": item.get("begin_at"),
                    "end_at": item.get("end_at"),
                })


if __name__ == "__main__":
    main()