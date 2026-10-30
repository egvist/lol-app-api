import json
from pathlib import Path
from api.services.pandascore_limiter import (
    PandaScoreRateLimitError,
)
from api.services.pandascore_client import (
    PandaScoreClient,
    PandaScoreError,
)
from api.services.team_discovery import discover_emea_teams
from api.services.emea_leagues import EMEA_LEAGUES


TEAMS_FILE = Path("data/emea_teams_2026.json")
PROGRESS_FILE = Path("data/emea_discovery_progress.json")

SEASON = 2026

# İlk başarılı testimizde tamamladığımız ligler
INITIAL_COMPLETED_LEAGUES = [
    4197,  # LEC
    4292,  # LFL
    1003,  # TCL
    4743,  # LFL Division 2
    4962,  # Arabian League
]


def load_json(path, default):
    if not path.exists():
        return default

    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    # Geçici dosyaya yazıp tamamlanınca değiştiriyoruz.
    temporary = path.with_name(path.name + ".tmp")

    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    temporary.replace(path)


def merge_teams(existing, incoming):
    merged = {
        team["id"]: team
        for team in existing
    }

    for team in incoming:
        team_id = team["id"]

        if team_id not in merged:
            merged[team_id] = team
            continue

        current = merged[team_id]

        for field in ("league_ids", "series_ids"):
            current[field] = sorted(
                set(current.get(field, []))
                | set(team.get(field, []))
            )

    return sorted(
        merged.values(),
        key=lambda team: (
            (team.get("name") or "").casefold(),
            team["id"],
        ),
    )


def main():
    teams = load_json(TEAMS_FILE, [])

    if not PROGRESS_FILE.exists() and teams:
        completed = INITIAL_COMPLETED_LEAGUES.copy()
    else:
        completed = load_json(PROGRESS_FILE, [])

    completed_set = set(completed)

    remaining = [
        league_id
        for league_id in EMEA_LEAGUES
        if league_id not in completed_set
    ]

    print("Existing teams:", len(teams))
    print("Completed leagues:", len(completed_set))
    print("Remaining leagues:", len(remaining))

    with PandaScoreClient() as client:
        for league_id in remaining:
            league_name = EMEA_LEAGUES[league_id]

            print(f"\nScanning: {league_name} ({league_id})")

            try:
                discovered = discover_emea_teams(
                    client=client,
                    league_ids=[league_id],
                    season=SEASON,
                )

            except (PandaScoreError, PandaScoreRateLimitError) as exc:
                print(f"\nDiscovery stopped: {exc}")
                print("Completed leagues are saved.")
                print("Resume after the API limit resets.")
                break

            teams = merge_teams(teams, discovered)

            # Önce verileri, sonra ilerlemeyi kaydet.
            save_json(TEAMS_FILE, teams)

            completed_set.add(league_id)

            save_json(
                PROGRESS_FILE,
                sorted(completed_set),
            )

            print(
                f"Found: {len(discovered)} | "
                f"Total unique teams: {len(teams)}"
            )

    print("\nDISCOVERY PROGRESS")
    print("-" * 50)
    print("Completed leagues:", len(completed_set))
    print("Remaining leagues:", len(EMEA_LEAGUES) - len(completed_set))
    print("Unique teams:", len(teams))


if __name__ == "__main__":
    main()