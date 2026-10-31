
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
