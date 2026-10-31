
from psycopg.rows import dict_row
from api.schemas.account import RankValue, SeasonRank

def get_account_by_id(conn, account_id: int):
    query = """

        SELECT id, player_id, game_name, tag_line, platform_id, summoner_level
        FROM riot_accounts
        WHERE id = %(account_id)s


    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"account_id": account_id})
        account = cur.fetchone()

    return account


def get_account_ranks(conn, account_id, season):
    query = """

        SELECT 
            asr.account_id,
            rs.label AS season_label,
            asr.queue_type,
            asr.current_tier,
            asr.current_division,
            asr.current_lp,
            asr.current_wins,
            asr.current_losses,
            asr.peak_tier,
            asr.peak_division,
            asr.peak_lp
        FROM account_season_ranks asr
        JOIN ranked_seasons rs
            ON asr.season_id = rs.id
        WHERE asr.account_id = %(account_id)s AND rs.season_year = %(season)s
        ORDER BY asr.queue_type

    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"account_id": account_id, "season": season})
        rows = cur.fetchall()

    ranks = []

    for row in rows:
        current = RankValue(
            tier=row["current_tier"],
            division=row["current_division"],
            lp=row["current_lp"],
            wins=row["current_wins"],
            losses=row["current_losses"]
        )

        peak = RankValue(
            tier=row["peak_tier"],
            division=row["peak_division"],
            lp=row["peak_lp"]
        )

        ranks.append(
            SeasonRank(
                account_id=row["account_id"],
                season_label=row["season_label"],
                queue_type=row["queue_type"],
                current=current,
                peak=peak
            )
        )

    return ranks


def get_account_rank_history(
    conn,
    account_id: int,
    season: int,
    queue_type: str,
    limit: int = 100
):
    query = """
        SELECT
            snap.tier,
            snap.division,
            snap.lp,
            snap.wins,
            snap.losses,
            snap.observed_at
        FROM rank_snapshots snap
        JOIN account_season_ranks asr
            ON snap.account_season_rank_id = asr.id
        JOIN ranked_seasons rs
            ON asr.season_id = rs.id
        WHERE asr.account_id = %(account_id)s
          AND rs.season_year = %(season)s
          AND asr.queue_type = %(queue_type)s
        ORDER BY snap.observed_at DESC
        LIMIT %(limit)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {
            "account_id": account_id,
            "season": season,
            "queue_type": queue_type,
            "limit": limit
        })

        history = cur.fetchall()

    return history


def get_season_by_year(conn, season: int):
    query = """
        SELECT id, label, season_year
        FROM ranked_seasons
        WHERE season_year = %(season)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"season": season})
        return cur.fetchone()