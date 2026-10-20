# =============================================================================
# repositories/champions.py — Şampiyon sorguları (Adım 9)
# =============================================================================
#
# FONKSİYON 1: list_champions(conn)
#   GÖREV: Bütün şampiyonlar, ada göre sıralı. (~170 satır; sayfalama gerekir mi?)
#
# FONKSİYON 2: get_champion(conn, champion_id)
#
# FONKSİYON 3: get_top_pros_for_champion(conn, champion_id, queue_id, min_games, limit)
#   GÖREV: Bu şampiyonu en çok oynayan pro oyuncular.
#     match_participants'ı champion_id ile filtrele, account_id NULL olmayanları
#     al, riot_accounts → players ile bağla, OYUNCU bazında grupla.
#     Hesapla: oyun sayısı, galibiyet, winrate, ortalama KDA.
#
#   ARAŞTIR:
#     - GROUP BY, COUNT(*), SUM(CASE WHEN win THEN 1 ELSE 0 END)
#       veya COUNT(*) FILTER (WHERE win)
#     - HAVING: "en az min_games maç" filtresi neden WHERE ile yapılamaz?
#     - Sıfıra bölme: NULLIF(deaths, 0)
#     - Oyuncu bazında mı, hesap bazında mı gruplamalısın? Bir proun 3 hesabı
#       varsa sonuç nasıl değişir?
#     - Şemada idx_participants_champion_role index'i var. Bu sorgu onu kullanıyor mu?
#
#   docs/riot-sync.md bölüm 6'daki örnek sorgu iyi bir başlangıç noktası.
# =============================================================================
