
import argparse
import subprocess
import sys

from psycopg import connect

from api.config import settings
from api.services.leaderboard_snapshot import (
    create_leaderboard_snapshot,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run Riot Rank Sync, then save a leaderboard snapshot."
    )

    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--platform", default="EUW1")
    parser.add_argument(
        "--queue",
        choices=["RANKED_SOLO_5x5", "RANKED_FLEX_SR"],
        default="RANKED_SOLO_5x5",
    )

    # Arguments before -- belong to this script.
    # Everything after -- is the Rank Sync command.
    arguments = sys.argv[1:]

    if "--" not in arguments:
        parser.error(
            "Provide your Rank Sync command after --"
        )

    separator = arguments.index("--")
    args = parser.parse_args(arguments[:separator])
    sync_command = arguments[separator + 1:]

    if not sync_command:
        parser.error("Rank Sync command is missing")

    print("STEP 1: Updating Riot API ranks...", flush=True)

    result = subprocess.run(
        sync_command,
        check=False,
    )

    if result.returncode != 0:
        print(
            "ERROR: Rank Sync failed. Snapshot was not created.",
            file=sys.stderr,
        )
        sys.exit(result.returncode)

    print("STEP 2: Saving leaderboard snapshot...", flush=True)

    with connect(settings.dsn) as conn:
        snapshot = create_leaderboard_snapshot(
            conn=conn,
            season=args.season,
            platform_id=args.platform,
            queue_type=args.queue,
        )

    print("\nWeekly leaderboard update completed!")
    print(f"Snapshot ID: {snapshot['snapshot_id']}")
    print(f"Season: {snapshot['season']}")
    print(f"Accounts: {snapshot['entries_count']}")
    print(f"Captured at: {snapshot['captured_at']}")


if __name__ == "__main__":
    main()
