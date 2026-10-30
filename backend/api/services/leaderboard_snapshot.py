
from psycopg import Connection


def create_leaderboard_snapshot(
    conn: Connection,
    season: int,
    platform_id: str = "EUW1",
    queue_type: str = "RANKED_SOLO_5x5",
) -> dict:
    with conn.transaction():
        with conn.cursor() as cur:

            # 1. Aktif sezonu bul
            cur.execute(
                """
                SELECT id
                FROM ranked_seasons
                WHERE season_year = %s
                  AND status = 'ACTIVE'
                """,
                (season,),
            )

            season_row = cur.fetchone()

            if season_row is None:
                raise ValueError(
                    f"No active ranked season for {season}"
                )

            season_id = season_row[0]

            # 2. Snapshot kaydını oluştur
            cur.execute(
                """
                INSERT INTO leaderboard_snapshots
                    (season_id, platform_id, queue_type, scope)
                VALUES (%s, %s, %s, 'TRACKED_PROS')
                RETURNING id, captured_at
                """,
                (season_id, platform_id, queue_type),
            )

            snapshot_id, captured_at = cur.fetchone()

            # 3. Güncel leaderboard satırlarını kopyala
            cur.execute(
                """
                INSERT INTO leaderboard_entries
                    (
                        snapshot_id,
                        rank_position,
                        account_id,
                        tier,
                        division,
                        lp,
                        wins,
                        losses
                    )
                SELECT
                    %s,
                    lb.rank_position,
                    lb.account_id,
                    lb.tier,
                    lb.division,
                    lb.lp,
                    lb.wins,
                    lb.losses
                FROM v_current_pro_leaderboard lb
                WHERE lb.season_id = %s
                  AND lb.platform_id = %s
                  AND lb.queue_type = %s
                """,
                (
                    snapshot_id,
                    season_id,
                    platform_id,
                    queue_type,
                ),
            )

            entries_count = cur.rowcount

            if entries_count == 0:
                raise ValueError(
                    "Cannot create an empty leaderboard snapshot"
                )

    return {
        "snapshot_id": snapshot_id,
        "season": season,
        "platform_id": platform_id,
        "queue_type": queue_type,
        "captured_at": captured_at,
        "entries_count": entries_count,
    }
