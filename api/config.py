# =============================================================================
# config.py — Ayarlar (Adım 2)
# =============================================================================
# Veritabanı şifresi gibi bilgiler koda YAZILMAZ. Kök dizindeki .env dosyasında
# duruyorlar: PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD.
# Bu dosyanın görevi bunları tek bir yerden okuyup uygulamaya vermek.
#
# GÖREV:
#   1. python-dotenv ile .env dosyasını yükle (projede zaten kullanılıyor,
#      lolapp_riot_sync.py içinde load_dotenv() çağrısına bak).
#   2. Bir Settings sınıfı ya da dataclass tanımla. İçinde şunlar olsun:
#        - pg_host, pg_port, pg_database, pg_user, pg_password
#        - pool_min_size, pool_max_size (bağlantı havuzu boyutu, ör. 1 ve 10)
#        - default_page_size, max_page_size (ör. 20 ve 100; pagination için)
#   3. Bu değerlerden PostgreSQL bağlantı string'i (conninfo / DSN) üreten
#      bir property ya da fonksiyon yaz.
#   4. Modül seviyesinde tek bir `settings` nesnesi oluştur. Diğer dosyalar
#      `from api.config import settings` diye kullansın.
#
# ARAŞTIR:
#   - "12-factor app config" — ayarlar neden ortam değişkenlerinde tutulur?
#   - PostgreSQL conninfo formatı: "host=... port=... dbname=..." ile
#     "postgresql://user:pass@host:port/db" arasındaki fark.
#   - (İsteğe bağlı) pydantic-settings paketi: BaseSettings ile aynı işi daha
#     az kodla ve tip kontrolüyle yapar. Önce elle yap, sonra bununla karşılaştır.
#
# İPUCU:
#   - os.environ["X"] ile os.getenv("X", "varsayılan") farkını bil. Şifre
#     yoksa uygulama hemen hata vermeli mi, yoksa varsayılanla mı devam etmeli?
#   - .env'den gelen her şey string'dir. Port ve havuz boyutunu int'e çevir.
#
# KONTROL:
#   Python konsolunda: from api.config import settings; print(settings.pg_host)
#   Şifreyi print ETME. Loglara da asla yazma.
# =============================================================================
