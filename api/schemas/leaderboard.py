# =============================================================================
# schemas/leaderboard.py — Sıralama ve sezon modelleri (Adım 8)
# =============================================================================
# Kaynak: v_current_pro_leaderboard VIEW'ı (sql/schema.sql en altta) ve
#         ranked_seasons tablosu
#
# GÖREV:
#   1. LeaderboardEntry
#        rank_position, player_id, nickname, account_id, game_name, tag_line,
#        tier, division, lp, wins, losses
#        + player_slug (frontend'in oyuncu sayfasına link verebilmesi için)
#        DİKKAT: View'da slug YOK. Ya view'ı players ile JOIN'leyeceksin ya da
#        bu alanı çıkaracaksın. Hangisi?
#
#   2. Leaderboard  → cevabın tamamı
#        season_label, platform_id, queue_type, entries: LeaderboardEntry listesi
#        + note: "Sadece takip edilen pro hesaplar; resmî Riot sıralaması değildir."
#        (Bu not bir proje kuralı, bkz. docs/riot-sync.md bölüm 4.)
#
#   3. Season
#        id, season_year, label, starts_at, ends_at, status
#
# ARAŞTIR:
#   - VIEW nedir, tablodan farkı ne? Bir VIEW'dan SELECT yapmak ile tablodan
#     yapmak arasında API tarafında fark var mı?
#   - ROW_NUMBER() OVER (PARTITION BY ...) — view rank_position'ı nasıl
#     hesaplıyor? Bir oyuncunun iki hesabı aynı listede olabilir mi?
# =============================================================================
