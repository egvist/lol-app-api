


from api.schemas.account import SeasonRank, RankValue
from psycopg.rows import dict_row


def list_players(conn, search, role, country, limit, offset):
    conditions = []
    params = {}

    # 1. Dinamik filtreler
    if search is not None:
        conditions.append("nickname ILIKE %(search)s")
        params["search"] = f"%{search}%"

    if role is not None:
        conditions.append("main_role = %(role)s")
        params["role"] = role

    if country is not None:
        conditions.append("country_code = %(country)s")
        params["country"] = country

    # 2. WHERE koşullarını birleştir
    where_clause = ""

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    # 3. Filtre parametrelerini COUNT sorgusu için sakla
    filter_params = params.copy()

    # 4. Pagination parametreleri
    params["limit"] = limit
    params["offset"] = offset

    # 5. Oyuncuları getiren sorgu
    query = f"""
        SELECT id, nickname, slug, country_code, main_role
        FROM players
        {where_clause}
        ORDER BY nickname, id
        LIMIT %(limit)s OFFSET %(offset)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        players = cur.fetchall()

    # 6. Filtrelere uyan toplam oyuncu sayısı
    count_query = f"""
        SELECT COUNT(*)
        FROM players
        {where_clause}
    """

    with conn.cursor() as cur:
        cur.execute(count_query, filter_params)
        total = cur.fetchone()[0]

    # 7. Sonuçları döndür
    return players, total

def get_player_by_slug(conn, slug):
    query = """
        SELECT id, nickname, slug, country_code, main_role, profile_image_url
        FROM players
        WHERE slug = %(slug)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"slug": slug})
        player = cur.fetchone()


    return player


def get_player_socials(conn, player_id):
    query = """
        SELECT platform, url
        FROM player_socials
        WHERE player_id = %(player_id)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"player_id": player_id})
        socials = cur.fetchall()

    return socials

def get_player_accounts(conn, player_id):
    query = """
        SELECT id, game_name, tag_line, platform_id, summoner_level
        FROM riot_accounts
        WHERE player_id = %(player_id)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"player_id": player_id})
        accounts = cur.fetchall()

    return accounts


def get_player_ranks(conn, player_id, season):
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
    FROM riot_accounts ra
    INNER JOIN account_season_ranks asr 
        ON ra.id = asr.account_id
    INNER JOIN ranked_seasons rs 
        ON asr.season_id = rs.id
    WHERE ra.player_id = %(player_id)s 
        AND rs.season_year = %(season)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"player_id": player_id, "season": season})
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

            rank = SeasonRank(
                account_id=row["account_id"],
                season_label=row["season_label"],
                queue_type=row["queue_type"],
                current=current,
                peak=peak
            )

            ranks.append(rank)
        return ranks


def find_players_by_names(
    conn,
    normalized_names: list[str],
) -> list[dict]:
    if not normalized_names:
        return []

    query = """
        SELECT
            id,
            nickname,
            slug,
            country_code,
            main_role
        FROM players
        WHERE regexp_replace(
            lower(nickname),
            '[^[:alnum:]]',
            '',
            'g'
        ) = ANY(%(names)s)
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"names": normalized_names})
        return cur.fetchall()