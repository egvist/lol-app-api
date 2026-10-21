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
# CEVAP:
#   - Dependency: endpoint'in ihtiyaç duyduğu bir şeyi (burada bağlantı)
#     FastAPI'nin her istekte senin yerine hazırlamasıdır:
#     `conn = Depends(get_conn)`. yield'li bir dependency'de yield'den önceki
#     kısım istekten önce, sonraki kısım cevap gönderildikten sonra çalışır;
#     temizlik (bağlantıyı geri vermek) oraya yazılır.
#   - `with pool.connection() as conn:` bloğu bitince bağlantıyı havuza geri
#     verir, hata olsa bile. Blok hatasız biterse transaction commit, hata
#     olursa rollback edilir. Geri vermeyi unutursan bağlantı ödünçte kalır
#     ("connection leak"): max_size kadar istekten sonra havuz boşalır, yeni
#     istekler timeout'a kadar bekleyip hata alır.
#   - dict_row ile satır {"id": 1, "nickname": "Vladi", ...} olarak gelir ve
#     PlayerSummary(**row) ya da PlayerSummary.model_validate(row) ile doğrudan
#     modele dönüşür. Tuple'da row[0], row[1] diye sırayla eşlemen gerekir ve
#     SELECT'e kolon eklenince sıra kayar. dict_row daha kolay.
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

from psycopg_pool import ConnectionPool
from api.config import settings

min_size = settings.pool_min_size
max_size = settings.pool_max_size

connection_pool = ConnectionPool(settings.dsn, min_size=min_size, max_size=max_size, open=False)


def open_pool():
    connection_pool.open()
def close_pool():
    connection_pool.close()

def get_conn():
    with connection_pool.connection() as conn:
        yield conn
