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
#
# -----------------------------------------------------------------------------
# FONKSİYON 6: get_account_masteries(conn, account_id, limit)
# -----------------------------------------------------------------------------
# GÖREV: champion_masteries JOIN champions, mastery_points'e göre azalan.
#
# YASAK: Bu dosyada riot_id_history tablosuna dokunan sorgu OLMAYACAK.
# =============================================================================
