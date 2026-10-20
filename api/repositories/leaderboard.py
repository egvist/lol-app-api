# =============================================================================
# repositories/leaderboard.py — Sıralama ve sezon sorguları (Adım 8)
# =============================================================================
#
# FONKSİYON 1: get_current_leaderboard(conn, platform_id, queue_type, limit, offset)
#   GÖREV: v_current_pro_leaderboard view'ından ilgili platform + kuyruk için
#     satırları rank_position sırasıyla getir. Oyuncu slug'ı için players ile JOIN.
#   ARAŞTIR: View sadece ACTIVE sezonu gösteriyor. Neden? View tanımındaki
#     WHERE koşullarını oku (sql/schema.sql).
#
# FONKSİYON 2: list_platforms(conn)
#   GÖREV: riot_accounts'ta bulunan, NULL olmayan farklı platform_id'leri döndür.
#     Frontend'deki "sunucu seç" listesi için.
#   ARAŞTIR: SELECT DISTINCT
#
# FONKSİYON 3: list_seasons(conn)
# FONKSİYON 4: get_active_season(conn)
#   GÖREV: ranked_seasons tablosu. ACTIVE sezon tam bir tane olmalı.
#     0 ya da 2+ satır gelirse ne yapmalısın? (lolapp_riot_sync.py içinde
#     ACTIVE sezonu nasıl okuduğuna bak.)
#
# BONUS: get_leaderboard_history(conn, account_id)
#   leaderboard_entries + leaderboard_snapshots ile bir hesabın zaman içindeki
#   sıralama pozisyonu. (Bu tablolar ancak sync --leaderboard-snapshot
#   çalıştırıldıysa dolu olur.)
# =============================================================================
