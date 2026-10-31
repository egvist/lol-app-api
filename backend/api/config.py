
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
