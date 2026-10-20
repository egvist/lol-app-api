# =============================================================================
# repositories/matches.py — Maç detay sorguları (Adım 9)
# =============================================================================
#
# FONKSİYON 1: get_match(conn, match_id)
#   GÖREV: matches tablosundan tek satır. raw_data kolonunu SEÇME.
#   ARAŞTIR: Neden "SELECT *" yerine kolonları tek tek yazmak daha iyi?
#     (raw_data büyük bir JSONB; seçmesen bile * onu getirir.)
#
# FONKSİYON 2: get_match_teams(conn, match_id)
#   GÖREV: match_teams'ten iki takımın satırını team_id sırasıyla getir.
#
# FONKSİYON 3: get_match_participants(conn, match_id)
#   GÖREV: 10 katılımcı + şampiyon adı + (varsa) pro oyuncunun slug'ı.
#   Bağlantı zinciri:
#     match_participants.account_id → riot_accounts.id → riot_accounts.player_id → players.id
#   account_id çoğu katılımcı için NULL olacak (pro olmayan oyuncular).
#   ARAŞTIR: Bu yüzden riot_accounts ve players'a hangi JOIN türüyle
#     bağlanmalısın? INNER JOIN kullanırsan kaç satır döner? Dene ve gör.
#
# DÜŞÜN: Router bu üç fonksiyonu sırayla çağıracak. get_match None dönerse
#   diğer ikisini çağırmaya gerek var mı?
# =============================================================================
