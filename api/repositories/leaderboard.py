# =============================================================================
# repositories/leaderboard.py — Sıralama ve sezon sorguları (Adım 8)
# =============================================================================
#
# FONKSİYON 1: get_current_leaderboard(conn, platform_id, queue_type, limit, offset)
#   GÖREV: v_current_pro_leaderboard view'ından ilgili platform + kuyruk için
#     satırları rank_position sırasıyla getir. Oyuncu slug'ı için players ile JOIN.
#   ARAŞTIR: View sadece ACTIVE sezonu gösteriyor. Neden? View tanımındaki
#     WHERE koşullarını oku (sql/schema.sql).
#   CEVAP: View'ın WHERE'i: s.status = 'ACTIVE', r.finalized_at IS NULL,
#     current_tier ve current_lp NOT NULL, platform_id NOT NULL. Bu bir
#     "current" leaderboard: sadece şu anki sezonun bitmemiş, rank'i bilinen
#     ve sunucusu çözülmüş hesaplarını sıralar. Biten sezonların satırları
#     dondurulmuş eski durumlardır; karışırsa geçen sezonun LP'si bu sezonla
#     yarışır. Sunucusu belli olmayan hesap hangi listeye gireceğini bilemez,
#     rank'i olmayan hesap da sıralanamaz.
#
# FONKSİYON 2: list_platforms(conn)
#   GÖREV: riot_accounts'ta bulunan, NULL olmayan farklı platform_id'leri döndür.
#     Frontend'deki "sunucu seç" listesi için.
#   ARAŞTIR: SELECT DISTINCT
#   CEVAP: SELECT DISTINCT tekrar eden satırları tek satıra indirir:
#     SELECT DISTINCT platform_id FROM riot_accounts
#     WHERE platform_id IS NOT NULL ORDER BY platform_id;
#     Aynı sonucu GROUP BY platform_id de verir.
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
