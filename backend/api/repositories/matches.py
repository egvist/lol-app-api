# =============================================================================
# repositories/matches.py — Maç detay sorguları (Adım 9)
# =============================================================================
#
# FONKSİYON 1: get_match(conn, match_id)
#   GÖREV: matches tablosundan tek satır. raw_data kolonunu SEÇME.
#   ARAŞTIR: Neden "SELECT *" yerine kolonları tek tek yazmak daha iyi?
#     (raw_data büyük bir JSONB; seçmesen bile * onu getirir.)
#   CEVAP: * bütün kolonları getirir; raw_data maç başına büyük bir ham Riot
#     JSON'u. Kullanmadığın veri diskten okunur, ağdan taşınır ve Python'da
#     dict'e çevrilir; her istek yavaşlar. Ayrıca tabloya ileride kolon
#     eklenirse * onu da sessizce getirir. Kolonları tek tek yazmak sorgunun
#     ne döndürdüğünü açık ve sabit tutar, dışarı verilmemesi gereken bir
#     alanı yanlışlıkla seçme ihtimalini de azaltır.
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
#   CEVAP: LEFT JOIN riot_accounts ve LEFT JOIN players. INNER JOIN,
#     account_id'si NULL olan (pro olmayan) katılımcıları düşürür: 10 yerine
#     sadece takip edilen pro sayısı kadar satır döner (genelde 1-2). LEFT
#     JOIN'de 10 satır gelir; pro olmayanların account_id ve player_slug
#     alanları NULL olur.
#
# DÜŞÜN: Router bu üç fonksiyonu sırayla çağıracak. get_match None dönerse
#   diğer ikisini çağırmaya gerek var mı?
# =============================================================================
