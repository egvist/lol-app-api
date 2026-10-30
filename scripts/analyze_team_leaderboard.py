import httpx

from api.services.team_leaderboard_analysis import (
    analyze_team_coverage,
)


def main():
    response = httpx.get(
        "http://127.0.0.1:8000/teams/leaderboard",
        params={
            "limit": 20,
            "offset": 0,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    # Şu anki 19 takımlık discovery için limit=20 yeterli.
    # Daha büyük leaderboard'larda tüm sayfaları çekmeliyiz.
    if data["total"] > len(data["items"]):
        raise RuntimeError(
            "Leaderboard has more teams than fetched. "
            "Pagination is required for a complete analysis."
        )

    result = analyze_team_coverage(data["items"])

    print("\nTEAM LEADERBOARD COVERAGE")
    print("-" * 60)

    print("Total teams:", result["total_teams"])
    print("Eligible teams:", result["eligible_teams"])
    print("Complete teams:", result["complete_teams"])
    print("Partial teams:", result["partial_teams"])
    print("Insufficient teams:", result["insufficient_teams"])

    print(
        "Overall coverage:",
        f"{result['overall_coverage_percent']}%",
    )

    print("\nTEAM DETAILS")
    print("-" * 60)

    for team in result["teams"]:
        print(
            f"{team['team_name']:<25} "
            f"{team['ranked_players']}/{team['total_players']} "
            f"{team['coverage_percent']:>6}% "
            f"{team['status']}"
        )
    print("\nMISSING PLAYER BREAKDOWN")
    print("-" * 60)

    for team in data["items"]:
        missing_players = [
            p["nickname"]
            for p in team["roster"]
            if p["local_player_id"] is None
        ]

        missing_ranks = [
            p["nickname"]
            for p in team["roster"]
            if p["local_player_id"] is not None
            and p["solo_queue"] is None
        ]

        if missing_players or missing_ranks:
            print(f"\n{team['team_name']}")
            print("  Not in DB:", missing_players)
            print("  No SoloQ rank:", missing_ranks)

if __name__ == "__main__":
    main()