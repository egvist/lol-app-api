import json
from pathlib import Path

from api.services.pandascore_client import PandaScoreClient


OUTPUT = Path("data/pandascore_lol_leagues.json")


def main():
    leagues = []
    page = 1

    with PandaScoreClient() as client:
        while True:
            batch = client.get_lol_leagues(
                page=page,
                per_page=100,
            )

            if not batch:
                break

            leagues.extend(batch)

            print(
                f"Page {page}: "
                f"{len(batch)} leagues "
                f"(total: {len(leagues)})"
            )

            if len(batch) < 100:
                break

            page += 1

    # Sort for easier inspection
    leagues.sort(
        key=lambda league: (
            (league.get("name") or "").casefold(),
            league.get("id") or 0,
        )
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            leagues,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\nTOTAL LEAGUES:", len(leagues))
    print("SAVED TO:", OUTPUT)

    print("\nLEAGUE CATALOG")
    print("-" * 70)

    for league in leagues:
        print(
            f"{league['id']:>7} | "
            f"{league.get('name', '')}"
        )


if __name__ == "__main__":
    main()