# =============================================================================
# db.py — Veritabanı bağlantı havuzu (Adım 3)
# =============================================================================
# Her HTTP isteğinde yeni bir PostgreSQL bağlantısı açmak yavaştır. Bunun
# yerine uygulama açılırken birkaç bağlantı açılır ve istekler bunları ödünç
# alıp geri verir. Buna "connection pool" denir.
#
# GÖREV:
#   1. psycopg_pool'dan ConnectionPool'u import et.
#   2. config.py'deki settings ile bir havuz oluştur. min_size / max_size
#      değerlerini settings'ten al.
#      DİKKAT: Havuzu modül import edilirken açma (open=False kullan), main.py
#      içindeki lifespan'de aç.
#   3. open_pool() ve close_pool() adında iki fonksiyon yaz. main.py bunları
#      lifespan içinde çağıracak.
#   4. get_conn() adında bir "dependency" fonksiyonu yaz:
#        - havuzdan bir bağlantı alsın,
#        - yield ile endpoint'e versin,
#        - istek bitince bağlantıyı havuza geri versin.
#
# ARAŞTIR:
#   - FastAPI docs: "Dependencies" ve "Dependencies with yield"
#   - psycopg_pool docs: pool.connection() bir context manager'dır. Neden
#     `with` bloğu ile kullanılır? Bağlantıyı geri vermeyi unutursan ne olur?
#   - psycopg "row_factory": Sorgu sonuçları varsayılan olarak tuple gelir.
#     dict_row kullanırsan dict gelir. Pydantic modellerine çevirmek için
#     hangisi daha kolay? (lolapp_riot_sync.py dict_row kullanıyor, oraya bak.)
#
# İPUCU:
#   - row_factory'yi havuz oluştururken "kwargs" ile bütün bağlantılara
#     verebilirsin.
#   - Bu API sadece okuma yapıyor. Bağlantıyı read-only yapmayı araştır
#     (psycopg'de conn.read_only veya
#     "SET default_transaction_read_only = on"). Bu bir güvenlik katmanıdır:
#     kodunda bir hata olsa bile API yanlışlıkla veri silemez.
#
# KONTROL:
#   main.py'deki /health endpoint'ine Depends(get_conn) ekle ve "SELECT 1"
#   çalıştır. PostgreSQL kapalıyken ne oluyor, açıkken ne oluyor? İkisini de dene.
# =============================================================================
