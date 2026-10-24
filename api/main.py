# =============================================================================
# main.py — Uygulamanın giriş noktası
# =============================================================================
# Bu dosya küçük kalmalı. Görevi: FastAPI uygulamasını oluşturmak, router'ları
# bağlamak ve uygulama açılırken/kapanırken yapılacak işleri tanımlamak.
# İş mantığı ve SQL buraya YAZILMAZ.
#
# -----------------------------------------------------------------------------
# ADIM 1 — İlk endpoint (önce sadece bunu yap, veritabanı olmadan)
# -----------------------------------------------------------------------------
# GÖREV:
#   1. fastapi'den FastAPI sınıfını import et.
#   2. `app` adında bir FastAPI nesnesi oluştur. title, version ve description
#      ver (bunlar /docs sayfasında görünür).
#   3. GET /health endpoint'i yaz. {"status": "ok"} döndürsün.
#
# ARAŞTIR:
#   - Decorator nedir? `@app.get("/health")` satırı fonksiyona ne yapıyor?
#   - `def` ile `async def` endpoint arasındaki fark ne? psycopg'yi senkron
#     kullanacaksan hangisini seçmelisin? (FastAPI docs: "Concurrency and async / await")
#
# CEVAP:
#   - Decorator, bir fonksiyonu alıp yerine başka bir şey döndüren
#     fonksiyondur; `@x` yazmak `f = x(f)` demektir. `@app.get("/health")`
#     fonksiyonu değiştirmez, onu GET /health yoluna kaydeder: o adrese istek
#     gelince FastAPI bu fonksiyonu çağırır ve dönen değeri JSON'a çevirir.
#   - `async def` endpoint'ler tek bir event loop üzerinde çalışır; içinde
#     sadece `await` ile beklenen async kütüphaneler kullanılmalı. Bloklayan
#     (senkron) bir çağrı yaparsan o sırada bütün sunucu bekler.
#     `def` endpoint'leri FastAPI ayrı bir thread havuzunda çalıştırır;
#     bloklayan kod diğer istekleri durdurmaz.
#   - Senkron psycopg (ConnectionPool) kullanacağın için `def` seç.
#
# KONTROL:
#   `py -m uvicorn api.main:app --reload` çalıştır.
#   http://127.0.0.1:8000/health → {"status":"ok"}
#   http://127.0.0.1:8000/docs   → endpoint listede görünüyor mu?
#
# -----------------------------------------------------------------------------
# ADIM 3 — Lifespan: bağlantı havuzunu aç/kapat (db.py yazıldıktan sonra)
# -----------------------------------------------------------------------------
# GÖREV:
#   1. Bir "lifespan" fonksiyonu yaz. Uygulama açılırken db.py'deki havuzu
#      açsın, kapanırken kapatsın.
#   2. Bu fonksiyonu FastAPI(...) oluştururken `lifespan=` parametresine ver.
#
# ARAŞTIR:
#   - FastAPI docs: "Lifespan Events"
#   - contextlib.asynccontextmanager ve `yield` burada nasıl çalışıyor?
#   - Eski yöntem olan @app.on_event("startup") neden artık önerilmiyor?
#
# CEVAP:
#   - Lifespan, uygulama başlarken bir kez ve kapanırken bir kez çalışan kod.
#   - @asynccontextmanager, içinde bir `yield` olan async fonksiyonu
#     `async with` ile kullanılabilen bir context manager'a çevirir. FastAPI
#     açılışta yield'e kadar olan kısmı çalıştırır (havuzu aç), uygulama
#     yield'de bekleyip istekleri karşılar, kapanışta yield'den sonrası
#     çalışır (havuzu kapat).
#   - on_event("startup") / on_event("shutdown") deprecated: açma ve kapama
#     iki ayrı fonksiyonda kalır, aralarında bir şey paylaşmak için global
#     değişken gerekir. Lifespan ikisini tek yerde tutar. İkisi birlikte de
#     kullanılamaz: lifespan verirsen on_event handler'ları çalışmaz.
#
# İPUCU: yield'den önceki kısım açılışta, sonraki kısım kapanışta çalışır.
#
# -----------------------------------------------------------------------------
# ADIM 3b — /health'i geliştir
# -----------------------------------------------------------------------------
# GÖREV: /health içinde veritabanına basit bir sorgu at (ör. "SELECT 1").
#   - Başarılıysa {"status": "ok", "database": "ok"}
#   - Hata olursa 503 durum koduyla {"status": "degraded", "database": "error"}
#
# ARAŞTIR: 500 ile 503 arasındaki fark ne? Neden burada 503 daha doğru?
# CEVAP: 500 Internal Server Error "sunucuda beklenmeyen bir hata oldu,
#   muhtemelen kodda bir bug var" demektir. 503 Service Unavailable "servis şu
#   an isteği karşılayamıyor, durum geçici, sonra tekrar dene" demektir.
#   Veritabanı kapalıyken kodda hata yok, bağımlı olunan servis yok. Load
#   balancer ve monitoring araçları 503'ü "bu instance hazır değil" olarak
#   anlar; trafiği oraya göndermez ya da bekler.
#
# -----------------------------------------------------------------------------
# ADIM 6+ — Router'ları bağla
# -----------------------------------------------------------------------------
# GÖREV: routers/ klasöründeki her dosyanın `router` nesnesini import et ve
#   app.include_router(...) ile uygulamaya ekle. Her router'ın prefix'i
#   (/players, /accounts, ...) ve tags'i olsun.
#
# ARAŞTIR: FastAPI docs: "Bigger Applications - Multiple Files"
#   prefix ve tags'i router dosyasında mı yoksa include_router'da mı vermek
#   daha temiz? İkisini de dene, birini seç.
#
# CEVAP: Router dosyasında vermek (APIRouter(prefix="/players", tags=[...]))
#   daha yaygın ve bu projeye uygun. Yollar ve prefix aynı dosyada durur;
#   dosyayı açan her şeyin /players altında olduğunu hemen görür. main.py de
#   sadece app.include_router(players.router) olarak kısa kalır.
#   include_router'da vermek, aynı router'ı farklı prefix'lerle (ör. /v1 ve
#   /v2) bağlaman gerektiğinde işe yarar. İkisini birden verirsen prefix'ler
#   birleşir: include_router(prefix="/v1") + router prefix "/players"
#   → /v1/players.


# -----------------------------------------------------------------------------
# BONUS (Adım 10)
# -----------------------------------------------------------------------------
# - CORS: İleride bir frontend (React vs.) bu API'yi farklı bir porttan
#   çağıracak. CORSMiddleware'i araştır, sadece izin verdiğin origin'leri ekle.
# - Global exception handler: Beklenmeyen bir hata olduğunda kullanıcıya
#   stack trace değil, düzgün bir JSON hata mesajı dön. Hatayı logla.
# =============================================================================

from contextlib import asynccontextmanager
from api.routers import players
from fastapi import FastAPI, HTTPException
from psycopg import OperationalError
from psycopg_pool import PoolTimeout
from api.routers import accounts
from api.db import connection_pool, open_pool, close_pool
from api.routers import players, accounts, leaderboard
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.limiter import limiter
from api.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    open_pool()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(
    title="LoL Stats API",
    version="0.1.0",
    description="LoL Stats API, player statistics and account information",
    lifespan=lifespan
)


# Shared limiter instance
app.state.limiter = limiter


# Consistent JSON response for rate limit errors
async def rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded,
):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
            }
        },
    )


app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_handler,
)

# Apply default limits to API routes
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    global_exception_handler,
)
app.include_router(players.router)
app.include_router(accounts.router)
app.include_router(leaderboard.router)

@app.get("/health")
def health_check():
    try:
        with connection_pool.connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "ok"}

    except (OperationalError, PoolTimeout):
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "database": "error"}
        )
