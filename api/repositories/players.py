# =============================================================================
# repositories/players.py — Oyuncu sorguları (Adım 5)
# =============================================================================
# !!! EN ÖNEMLİ KURAL: SQL INJECTION
# Kullanıcıdan gelen hiçbir değeri SQL string'ine f-string / + / % ile EKLEME.
#   YANLIŞ fikir: f"... WHERE slug = '{slug}'"
#   DOĞRU fikir:  SQL içinde %s (veya %(isim)s) yer tutucu + değerleri ayrı
#                 parametre olarak cur.execute(sql, params)'a vermek.
# ARAŞTIR: "SQL injection" nedir? slug = "x' OR '1'='1" gönderilirse yanlış
#   yöntemde ne olur? psycopg docs: "Passing parameters to SQL queries".
#
# -----------------------------------------------------------------------------
# FONKSİYON 1: list_players(conn, search, role, country, limit, offset)
# -----------------------------------------------------------------------------
# GÖREV: Filtrelere uyan oyuncuları sayfalı olarak döndür.
#   - search: nickname içinde geçen metin (büyük/küçük harf duyarsız)
#   - role: main_role eşitliği
#   - country: country_code eşitliği
#   - Hepsi isteğe bağlı. None ise o filtre uygulanmaz.
#   - nickname'e göre sırala.
#   - İki şey döndür: o sayfanın satırları ve toplam sayı (Page modeli için).
#
# ARAŞTIR:
#   - ILIKE ve '%' joker karakteri. Kullanıcı aramasına % eklemeyi SQL'de mi
#     yoksa Python'da parametreye mi yaparsın? (İpucu: parametreye.)
#   - Değişken sayıda filtreyle WHERE oluşturmak: "WHERE 1=1 AND ..." hilesi
#     ya da koşul listesi + " AND ".join(...). İkisi de güvenli mi? Neden?
#     (İpucu: birleştirdiğin şey kullanıcı verisi değil, SENİN yazdığın sabit
#     SQL parçaları. Değerler yine %s ile gidiyor.)
#   - Toplam sayıyı ayrı bir COUNT(*) sorgusuyla mı alırsın, yoksa
#     COUNT(*) OVER () window function ile tek sorguda mı? İkisini de dene.
#   - LIMIT / OFFSET
#
# -----------------------------------------------------------------------------
# FONKSİYON 2: get_player_by_slug(conn, slug)
# -----------------------------------------------------------------------------
# GÖREV: Tek bir oyuncuyu döndür. Bulunamazsa None döndür.
#   (404 hatası vermek router'ın işi, repository'nin değil!)
#   ARAŞTIR: cur.fetchone() ile cur.fetchall() farkı.
#
# -----------------------------------------------------------------------------
# FONKSİYON 3: get_player_socials(conn, player_id)
# FONKSİYON 4: get_player_accounts(conn, player_id)
# -----------------------------------------------------------------------------
# GÖREV: Oyuncunun sosyal linklerini ve Riot hesaplarını döndür.
#   Router bu üçünü (oyuncu + socials + accounts) birleştirip PlayerDetail
#   yapacak.
#
# ARAŞTIR (ileri seviye, sonra dön):
#   Üç ayrı sorgu yerine tek sorguda yapmak mümkün: PostgreSQL json_agg() ve
#   json_build_object() ile alt listeleri JSON olarak toplamak. Hangisi daha
#   okunur, hangisi daha hızlı? "N+1 query problem" konusunu da oku. Liste
#   sayfasında her oyuncu için ayrı hesap sorgusu atarsan ne olur?
#
# -----------------------------------------------------------------------------
# FONKSİYON 5 (Bonus): get_player_live_game(conn, player_id)
# -----------------------------------------------------------------------------
# GÖREV: Oyuncunun herhangi bir hesabı şu an canlı oyundaysa o oyunu döndür.
#   Tablolar: live_games, live_game_participants, riot_accounts
#   Koşullar: ended_at IS NULL ve expires_at > now()
#   ARAŞTIR: Neden expires_at kontrolü gerekli? (docs/riot-sync.md bölüm 7)
#
# KONTROL: Her fonksiyonu önce pgAdmin'de çıplak SQL olarak yaz ve çalıştır.
#   Doğru sonucu verince Python'a taşı. Test oyuncusu: slug = 'vladi'.
# =============================================================================
