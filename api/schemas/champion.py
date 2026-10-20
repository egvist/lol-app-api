# =============================================================================
# schemas/champion.py — Şampiyon modelleri (Adım 9)
# =============================================================================
# Kaynak: champions tablosu (id, ddragon_key, name, image_filename)
#
# GÖREV:
#   1. Champion
#        id, name, ddragon_key, image_url
#
#   2. ChampionProStats  → "bu şampiyonu en çok hangi prolar oynuyor"
#        player_slug, nickname, games, wins, winrate, avg_kda
#
# ARAŞTIR:
#   - Tabloda image_filename var ama image_url yok. Data Dragon görsel URL'inin
#     formatını bul (ddragon.leagueoflegends.com/cdn/<version>/img/champion/...).
#     URL'i SQL'de mi, Python'da mı, yoksa frontend'de mi oluşturmak daha
#     doğru? Sürüm numarasını nereden alacaksın?
#     (lolapp_riot_sync.py içinde ddragon'u nasıl kullandığına bak.)
#   - KDA = (kills + assists) / deaths. deaths = 0 ise ne yapmalı?
# =============================================================================
