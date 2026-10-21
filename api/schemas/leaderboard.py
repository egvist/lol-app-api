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
#
# CEVAP:
#   - VIEW, kaydedilmiş bir SELECT sorgusudur; kendi verisi yoktur. Her
#     sorguda tanımı çalışır ve tablolardaki güncel veri gelir. API tarafında
#     fark yok: FROM v_current_pro_leaderboard tablo gibi yazılır. Bu view
#     JOIN ve window function içerdiği için ona yazılamaz (API zaten sadece
#     okuyor) ve kendi index'i yoktur, alttaki tabloların index'leri kullanılır.
#   - ROW_NUMBER() OVER (PARTITION BY season_id, platform_id, queue_type
#     ORDER BY tier, division, lp DESC, a.id): satırları her (sezon, sunucu,
#     kuyruk) grubu için ayrı ayrı sıralar ve 1'den başlayarak numaralar.
#     Eşitlikte küçük a.id önce gelir; aynı numara iki kez verilmez.
#   - Evet. Sıralama hesap bazında: bir proun aynı sunucuda iki hesabı da
#     rank'liyse ikisi de listede ayrı sıralarda, aynı nickname ile görünür.
#     Farklı sunuculardaki hesaplar farklı listelere düşer.
# =============================================================================
