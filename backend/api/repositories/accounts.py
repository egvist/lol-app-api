# =============================================================================
# repositories/accounts.py — Hesap, rank ve mastery sorguları (Adım 8)
# =============================================================================
# Tablo ilişkileri için docs/database.md içindeki diyagramlara bak.
#
# -----------------------------------------------------------------------------
# FONKSİYON 1: get_account(conn, account_id)
# FONKSİYON 2: find_account_by_riot_id(conn, game_name, tag_line)
# -----------------------------------------------------------------------------
# GÖREV: Tek hesap döndür, yoksa None. İkincisi "Faker#KR1" gibi Riot ID ile arar.
#   Hesabın sahibi olan oyuncunun slug ve nickname'ini de getir (JOIN players).
#
# ARAŞTIR:
#   - Riot ID'ler büyük/küçük harf duyarsız eşleşmeli. Şemada şu index var:
#       idx_accounts_riot_id ON riot_accounts(lower(game_name), lower(tag_line))
#     Bu index'in kullanılması için WHERE koşulunu nasıl yazmalısın?
#     EXPLAIN ile sorgu planına bak ve "Index Scan" görüyor musun kontrol et.
#   CEVAP: WHERE koşulu index tanımındaki ifadeyle birebir aynı olmalı:
#       WHERE lower(game_name) = lower(%s) AND lower(tag_line) = lower(%s)
#     ILIKE ya da düz game_name = %s yazarsan bu index kullanılamaz.
#     Not: tablo küçükken (birkaç bin satır) PostgreSQL index olsa bile Seq
#     Scan seçebilir, çünkü tabloyu baştan okumak daha ucuzdur. Index'in
#     kullanılabildiğini görmek için denemede önce SET enable_seqscan = off;
#     çalıştır. Planda "Index Scan" ya da "Bitmap Index Scan" görürsün.
#
# -----------------------------------------------------------------------------
# FONKSİYON 3: get_account_ranks(conn, account_id, season_year=None)
# -----------------------------------------------------------------------------
# GÖREV: Hesabın sezon bazlı current/peak rank'lerini döndür.
#   Tablolar: account_season_ranks JOIN ranked_seasons
#   season_year verilmezse bütün sezonlar, en yenisi önce.
#
# -----------------------------------------------------------------------------
# FONKSİYON 4: get_rank_history(conn, account_id, queue_type, season_year=None)
# -----------------------------------------------------------------------------
# GÖREV: LP grafiği için rank_snapshots satırlarını zamana göre sırala.
#   rank_snapshots doğrudan account_id tutmuyor. Hangi tablo üzerinden
#   bağlanıyor? (account_season_rank_id → account_season_ranks)
#   Sezon verilmezse ACTIVE sezonu kullan.
#
# -----------------------------------------------------------------------------
# FONKSİYON 5: get_account_matches(conn, account_id, queue_id, limit, offset)
# -----------------------------------------------------------------------------
# GÖREV: Hesabın maç geçmişi (MatchSummary için).
#   match_participants (account_id ile filtrele) JOIN matches LEFT JOIN champions
#   En yeni maç önce (matches.started_at DESC).
#   ARAŞTIR: Burada neden champions için INNER değil LEFT JOIN? champion_id
#   NULL olabilir mi, ya da champions tablosunda o şampiyon henüz yoksa?
#   CEVAP: match_participants.champion_id NULL olabilir (şemada NOT NULL yok;
#     Riot championId vermezse sync NULL yazar). INNER JOIN bu satırları, yani
#     hesabın o maçlarını listeden tamamen düşürür. LEFT JOIN'de maç yine
#     görünür, sadece champion_name NULL olur. Sync bilinmeyen şampiyonlar
#     için "Unknown champion" kaydı açtığından ikinci durum pratikte nadirdir,
#     ama LEFT JOIN hiçbir maçın kaybolmamasını garanti eder.
#
# -----------------------------------------------------------------------------
# FONKSİYON 6: get_account_masteries(conn, account_id, limit)
# -----------------------------------------------------------------------------
# GÖREV: champion_masteries JOIN champions, mastery_points'e göre azalan.
#
# YASAK: Bu dosyada riot_id_history tablosuna dokunan sorgu OLMAYACAK.
# =============================================================================

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