# =============================================================================
# schemas/match.py — Maç modelleri (Adım 9)
# =============================================================================
# Kaynak tablolar: matches, match_teams, match_participants, champions
#
# GÖREV: Şu modelleri yaz:
#
#   1. MatchSummary  → bir hesabın maç geçmişi listesinde tek satır
#        match_id, queue_id, started_at, duration_seconds, win,
#        champion_id, champion_name, kills, deaths, assists, cs, team_position
#        (Bu model "bir maç"ı değil, "bir hesabın o maçtaki performansını"
#        anlatıyor. Bu yüzden match_participants + matches JOIN'inden gelir.)
#
#   2. ParticipantStats  → maç detayındaki 10 oyuncudan biri
#        participant_id, team_id, champion_id, champion_name, team_position,
#        kills, deaths, assists, cs, gold_earned, damage_to_champions,
#        vision_score, items (items_json), win
#        + account_id ve player_slug: bu katılımcı takip ettiğimiz bir pro
#          ise dolu, değilse boş. (Frontend pro oyuncuya link verebilsin diye.)
#
#   3. TeamStats
#        team_id, win, champion_kills, baron_kills, dragon_kills,
#        tower_kills, inhibitor_kills, bans (bans_json)
#
#   4. MatchDetail
#        matches tablosundaki bilgiler + teams: TeamStats listesi
#        + participants: ParticipantStats listesi
#
# ARAŞTIR:
#   - JSONB kolonları (items_json, bans_json) psycopg ile Python'a hangi tipte
#     gelir? Pydantic modelinde tipini ne yazmalısın? (list[int]? list[dict]?)
#     Önce veritabanında bir satıra bakıp gerçek şeklini gör.
#   - queue_id 420 = SoloQ, 440 = Flex (docs/riot-sync.md). Sayıyı mı
#     döndürmeli, yoksa "SOLO"/"FLEX" gibi okunur bir ad mı eklemeli?
#
# CEVAP:
#   - psycopg JSONB'yi otomatik çözer: string değil, Python list/dict gelir.
#     items_json: lolapp_riot_sync.py item0..item6'dan 7 elemanlı bir sayı
#     listesi yazıyor, boş slot 0 → list[int].
#     bans_json: Riot'un team.bans listesi aynen:
#     [{"championId": 266, "pickTurn": 1}, ...] → list[dict[str, int]] ya da
#     champion_id / pick_turn alanlı küçük bir Ban modeli.
#   - İkisini birden dön: queue_id (Riot'un resmî değeri, filtrelerde
#     kullanılır) + queue_name ("SOLO"/"FLEX"). Ad sabit bir sözlükten gelir;
#     bilinmeyen bir id için None.
#
# YASAK: matches.raw_data (ham Riot JSON) dışarı VERİLMEYECEK. Çok büyük ve
#   gereksiz. Neden response modelinde olmayan bir alanın dışarı sızamayacağını
#   araştır: "response_model filtreleme".
# =============================================================================
