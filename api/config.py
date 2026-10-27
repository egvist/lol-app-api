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
# CEVAP:
#   - 12-factor: aynı kod her ortamda (kendi bilgisayarın, test, sunucu)
#     çalışır, sadece ortam değişkenleri farklıdır. Şifre koda yazılmadığı
#     için git'e girmez; bir ayarı değiştirmek için kodu değiştirmen gerekmez.
#   - "host=localhost port=5432 dbname=lolapp user=postgres password=..."
#     keyword/value formatıdır: alanlar boşlukla ayrılır, değerde boşluk varsa
#     tek tırnak içine alınır.
#     "postgresql://postgres:sifre@localhost:5432/lolapp" URI formatıdır: tek
#     parça taşınır ve çoğu araç (Docker, bulut servisleri) bunu verir; ama
#     şifrede @ : / gibi karakterler varsa percent-encoding gerekir.
#     psycopg ikisini de kabul eder. psycopg.conninfo.make_conninfo(host=...,
#     password=...) keyword formatını kaçış işleriyle birlikte senin yerine
#     üretir.
#   - pydantic-settings: BaseSettings'ten türeyen sınıf alanlarını ortam
#     değişkenlerinden (ve .env'den) otomatik okur, tipe çevirir (port → int)
#     ve zorunlu bir alan eksikse uygulama açılırken hata verir.
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

import os
from dotenv import load_dotenv
from psycopg.conninfo import make_conninfo
from dataclasses import dataclass

load_dotenv()  # .env dosyasını ortam degiskenlerine yukle (os.environ)

class Settings:
    def __init__(self):
        # os.getenv ise ortam degiskenlerinden o degerleri okur, yoksa varsayılanı kullanır.
        self.pg_host = os.getenv("PGHOST", "localhost")
        self.pg_port = int(os.getenv("PGPORT", 5432))
        self.pg_database = os.getenv("PGDATABASE", "lolapp")
        self.pg_user = os.getenv("PGUSER", "postgres")
        self.pg_password = os.getenv("PGPASSWORD", "")
        self.pool_min_size = int(os.getenv("POOL_MIN_SIZE", 1))
        self.pool_max_size = int(os.getenv("POOL_MAX_SIZE", 10))
        self.default_page_size = int(os.getenv("DEFAULT_PAGE_SIZE", 20))
        self.max_page_size = int(os.getenv("MAX_PAGE_SIZE", 100))
        self.pandascore_token = os.getenv("PANDASCORE_TOKEN", "")
 
    # property settingsi daha sonra .() olmadan almamizi saglar ve cachelemez her seferinde yeniden hesaplar.
    @property
    def dsn(self):
        return make_conninfo(
            host=self.pg_host,
            port=self.pg_port,
            dbname=self.pg_database,
            user=self.pg_user,
            password=self.pg_password
        )

settings = Settings()
