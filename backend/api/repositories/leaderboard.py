
from psycopg.rows import dict_row



def list_leaderboard(
    conn,
    season: int,
    queue_type: str,
    limit: int,
    offset: int,
):
    query = """
        WITH recent_snapshots AS (
            SELECT id
            FROM leaderboard_snapshots
            WHERE season_id = (
                SELECT id
                FROM ranked_seasons
                WHERE season_year = %(season)s
            )
              AND platform_id = 'EUW1'
              AND queue_type = %(queue_type)s
              AND scope = 'TRACKED_PROS'
            ORDER BY captured_at DESC, id DESC
            LIMIT 2
        ),
        snapshots AS (
            SELECT
                MAX(id) FILTER (WHERE rn = 1) AS latest_id,
                MAX(id) FILTER (WHERE rn = 2) AS previous_id
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        ORDER BY captured_at DESC, id DESC
                    ) AS rn
                FROM leaderboard_snapshots
                WHERE id IN (
                    SELECT id FROM recent_snapshots
                )
            ) ranked
        )
        SELECT
            lb.rank_position,
            lb.player_id,
            lb.nickname,
            p.slug,
            lb.account_id,
            lb.game_name,
            lb.tag_line,
            lb.platform_id,
            lb.queue_type,
            lb.tier,
            lb.division,
            lb.lp,
            lb.wins,
            lb.losses,

            previous_entry.rank_position AS previous_rank,

            CASE
                WHEN latest_entry.rank_position IS NOT NULL
                 AND previous_entry.rank_position IS NOT NULL
                THEN
                    previous_entry.rank_position
                    - latest_entry.rank_position
                ELSE NULL
            END AS rank_change

        FROM v_current_pro_leaderboard lb

        JOIN ranked_seasons rs
            ON lb.season_id = rs.id

        JOIN players p
            ON lb.player_id = p.id

        CROSS JOIN snapshots s

        LEFT JOIN leaderboard_entries latest_entry
            ON latest_entry.snapshot_id = s.latest_id
           AND latest_entry.account_id = lb.account_id

        LEFT JOIN leaderboard_entries previous_entry
            ON previous_entry.snapshot_id = s.previous_id
           AND previous_entry.account_id = lb.account_id

        WHERE rs.season_year = %(season)s
          AND lb.platform_id = 'EUW1'
          AND lb.queue_type = %(queue_type)s

        ORDER BY lb.rank_position
        LIMIT %(limit)s
        OFFSET %(offset)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            query,
            {
                "season": season,
                "queue_type": queue_type,
                "limit": limit,
                "offset": offset,
            },
        )
        return cur.fetchall()



def get_leaderboard_total(
    conn,
    season: int,
    queue_type: str,
):
    query = """
        SELECT COUNT(*) AS total
        FROM v_current_pro_leaderboard lb
        JOIN ranked_seasons rs
            ON lb.season_id = rs.id
        WHERE rs.season_year = %(season)s
          AND lb.platform_id = 'EUW1'
          AND lb.queue_type = %(queue_type)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            query,
            {
                "season": season,
                "queue_type": queue_type,
            },
        )
        result = cur.fetchone()

    return result["total"]


def season_exists(conn, season: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM ranked_seasons
                WHERE season_year = %s
            )
            """,
            (season,),
        )
        return cur.fetchone()[0]


def get_active_season_year(conn) -> int | None:
    query = """
        SELECT season_year
        FROM ranked_seasons
        WHERE status = 'ACTIVE'
    """

    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()

    if len(rows) != 1:
        return None

    return rows[0][0]