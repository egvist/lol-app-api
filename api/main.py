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
# -----------------------------------------------------------------------------
# BONUS (Adım 10)
# -----------------------------------------------------------------------------
# - CORS: İleride bir frontend (React vs.) bu API'yi farklı bir porttan
#   çağıracak. CORSMiddleware'i araştır, sadece izin verdiğin origin'leri ekle.
# - Global exception handler: Beklenmeyen bir hata olduğunda kullanıcıya
#   stack trace değil, düzgün bir JSON hata mesajı dön. Hatayı logla.
# =============================================================================
