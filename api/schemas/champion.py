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
#
# CEVAP:
#   - Format: https://ddragon.leagueoflegends.com/cdn/<version>/img/champion/<image_filename>
#     ör. .../cdn/14.20.1/img/champion/Ahri.png. Sürüm listesi
#     https://ddragon.leagueoflegends.com/api/versions.json adresinde, ilk
#     eleman en yenisi (lolapp_riot_sync.py de sürümü böyle alıyor).
#   - URL'i Python'da (schema ya da router) oluşturmak en doğrusu: format ve
#     sürüm tek yerde değişir, frontend hazır URL alır. SQL'de yapmak veriyi
#     sunuma bağlar. Sürümü her istekte ddragon'dan çekme; config'te tut ya da
#     uygulama açılırken bir kez çekip sakla.
#     Not: Data Dragon indirilemediyse sync geçici bir şampiyon kaydı açar ve
#     image_filename NULL kalır; o durumda image_url de None olmalı.
#   - deaths = 0 ise sıfıra bölünemez. Çoğu site bunu "Perfect" gösterir.
#     API'de None dön, frontend "Perfect" yazsın. Ortalama KDA için maç maç
#     ortalama almak yerine toplamları böl:
#     SUM(kills + assists) / NULLIF(SUM(deaths), 0).
# =============================================================================
