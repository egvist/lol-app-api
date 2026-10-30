
import argparse

from psycopg import connect

from api.config import settings
from api.services.leaderboard_snapshot import (
    create_leaderboard_snapshot,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--platform", default="EUW1")
    parser.add_argument(
        "--queue",
        default="RANKED_SOLO_5x5",
        choices=["RANKED_SOLO_5x5", "RANKED_FLEX_SR"],
    )

    args = parser.parse_args()

    with connect(settings.dsn) as conn:
        result = create_leaderboard_snapshot(
            conn=conn,
            season=args.season,
            platform_id=args.platform,
            queue_type=args.queue,
        )

    print("Snapshot created successfully!")
    print(f"Snapshot ID: {result['snapshot_id']}")
    print(f"Season: {result['season']}")
    print(f"Platform: {result['platform_id']}")
    print(f"Queue: {result['queue_type']}")
    print(f"Captured at: {result['captured_at']}")
    print(f"Entries: {result['entries_count']}")


if __name__ == "__main__":
    main()
