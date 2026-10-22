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
# CEVAP: SQL injection, kullanıcı verisinin SQL kodunun parçası olarak
#   çalışmasıdır. f-string ile sorgu WHERE slug = 'x' OR '1'='1' olur;
#   '1'='1' her satırda doğru olduğu için bütün oyuncular döner. Daha kötü
#   değerlerle (ör. "x'; DROP TABLE players; --") veri silinebilir.
#   Parametreli sorguda (%s) değer SQL metninden ayrı gönderilir ve her zaman
#   sadece veri olarak işlenir: veritabanı slug'ı "x' OR '1'='1" metniyle
#   karşılaştırır, eşleşen oyuncu olmadığı için sonuç boş gelir.
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
# CEVAP:
#   - ILIKE, büyük/küçük harf duyarsız LIKE'tır; % "herhangi bir metin"
#     demektir. %'leri Python'da parametreye ekle: params["search"] =
#     f"%{search}%", SQL'de nickname ILIKE %(search)s. Dikkat: parametreli bir
#     sorgunun metnine düz % yazarsan psycopg onu yer tutucu sanır, %% yazmak
#     gerekir; bu da parametreye eklemeyi daha kolay yapar. Kullanıcının
#     yazdığı % ve _ de joker olarak çalışır; istenmiyorsa \ ile kaçır.
#   - İkisi de güvenli, çünkü birleştirdiğin "main_role = %(role)s" gibi
#     parçaları sen yazdın; kullanıcı değeri yine ayrı parametre olarak
#     gidiyor. Koşul listesi + " AND ".join(...) daha temiz; liste boşsa
#     WHERE'i hiç yazma. Kural: SQL metnine sadece sabit string girer.
#   - Ayrı COUNT(*): iki sorgu, aynı WHERE iki kez çalışır ama okunur.
#     COUNT(*) OVER (): tek sorgu, her satırda total kolonu gelir; ama sayfa
#     boşsa (offset toplamdan büyükse) hiç satır gelmez ve total'i
#     öğrenemezsin. Bu proje boyutunda ikisi de yeterince hızlı.
#   - LIMIT n en fazla n satır döndürür, OFFSET m ilk m satırı atlar. ORDER BY
#     olmadan sayfalar tutarsız olur; aynı nickname'ler için
#     ORDER BY nickname, id ile sırayı kesinleştir.
#
# -----------------------------------------------------------------------------
# FONKSİYON 2: get_player_by_slug(conn, slug)
# -----------------------------------------------------------------------------
# GÖREV: Tek bir oyuncuyu döndür. Bulunamazsa None döndür.
#   (404 hatası vermek router'ın işi, repository'nin değil!)
#   ARAŞTIR: cur.fetchone() ile cur.fetchall() farkı.
#   CEVAP: fetchone() sonraki tek satırı döner, satır yoksa None. fetchall()
#     kalan bütün satırları liste olarak döner, yoksa []. slug UNIQUE olduğu
#     için burada fetchone() doğru; None dönmesi "bulunamadı" demektir ve
#     router bunu 404'e çevirir.
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
# CEVAP:
#   - Üç ayrı sorgu daha okunur ve test etmesi daha kolay. Detay sayfasında
#     3 index'li sorgu milisaniyeler sürer. json_agg ile tek sorgu ağ gidiş
#     dönüşünü 3'ten 1'e indirir ama SQL uzar ve okunması zorlaşır; tek
#     oyuncu sayfasında fark hissedilmez.
#   - N+1: listeyi getiren 1 sorgu + listedeki N satırın her biri için 1
#     sorgu. 20 oyunculuk sayfa 21 sorgu, limit=100 ise 101 sorgu demek; her
#     birinin gidiş-dönüş maliyeti toplanır. Çözüm: JOIN/json_agg ile tek
#     sorgu ya da WHERE player_id = ANY(%s) ile bütün hesapları tek seferde
#     alıp Python'da gruplamak.
#
# -----------------------------------------------------------------------------
# FONKSİYON 5 (Bonus): get_player_live_game(conn, player_id)
# -----------------------------------------------------------------------------
# GÖREV: Oyuncunun herhangi bir hesabı şu an canlı oyundaysa o oyunu döndür.
#   Tablolar: live_games, live_game_participants, riot_accounts
#   Koşullar: ended_at IS NULL ve expires_at > now()
#   ARAŞTIR: Neden expires_at kontrolü gerekli? (docs/riot-sync.md bölüm 7)
#   CEVAP: Canlı oyun kaydı geçici bir önbellektir: sync oyunu her gördüğünde
#     expires_at = now() + 5 dakika yapar. ended_at ise ancak sync o hesabı
#     tekrar kontrol edip Spectator API'den 404 alırsa yazılır. Live job
#     durursa ya da o hesaba sıra gelmezse ended_at NULL kalır ve sadece ona
#     bakarsan bitmiş oyun sonsuza kadar canlı görünür. expires_at > now(),
#     son 5 dakikada doğrulanmamış kaydı eski sayar.
#
# KONTROL: Her fonksiyonu önce pgAdmin'de çıplak SQL olarak yaz ve çalıştır.
#   Doğru sonucu verince Python'a taşı. Test oyuncusu: slug = 'vladi'.
# =============================================================================



from psycopg.rows import dict_row


def list_players(conn, search, role, country, limit, offset):
    conditions = []
    params = {}

    # 1. Dinamik filtreler
    if search is not None:
        conditions.append("nickname ILIKE %(search)s")
        params["search"] = f"%{search}%"

    if role is not None:
        conditions.append("main_role = %(role)s")
        params["role"] = role

    if country is not None:
        conditions.append("country_code = %(country)s")
        params["country"] = country

    # 2. WHERE koşullarını birleştir
    where_clause = ""

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    # 3. Filtre parametrelerini COUNT sorgusu için sakla
    filter_params = params.copy()

    # 4. Pagination parametreleri
    params["limit"] = limit
    params["offset"] = offset

    # 5. Oyuncuları getiren sorgu
    query = f"""
        SELECT id, nickname, slug, country_code, main_role
        FROM players
        {where_clause}
        ORDER BY nickname, id
        LIMIT %(limit)s OFFSET %(offset)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        players = cur.fetchall()

    # 6. Filtrelere uyan toplam oyuncu sayısı
    count_query = f"""
        SELECT COUNT(*)
        FROM players
        {where_clause}
    """

    with conn.cursor() as cur:
        cur.execute(count_query, filter_params)
        total = cur.fetchone()[0]

    # 7. Sonuçları döndür
    return players, total

def get_player_by_slug(conn, slug):
    query = """
        SELECT id, nickname, slug, country_code, main_role
        FROM players
        WHERE slug = %(slug)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"slug": slug})
        player = cur.fetchone()


    return player


def get_player_socials(conn, player_id):
    query = """
        SELECT platform, url
        FROM player_socials
        WHERE player_id = %(player_id)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"player_id": player_id})
        socials = cur.fetchall()

    return socials

def get_player_accounts(conn, player_id):
    query = """
        SELECT id, game_name, tag_line, platform_id, summoner_level
        FROM riot_accounts
        WHERE player_id = %(player_id)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, {"player_id": player_id})
        accounts = cur.fetchall()

    return accounts