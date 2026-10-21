# LoLApp API — öğrenme çalışması

Bu klasördeki dosyalarda **kod yok**, sadece yorumlar var. Her dosyada şunları bulacaksın:

- **GÖREV:** O dosyaya ne yazman gerektiği
- **ARAŞTIR:** Yazmadan önce okuman / öğrenmen gereken konu
- **İPUCU:** Takılırsan bakacağın yön (cevabın kendisi değil)
- **KONTROL:** Doğru yaptığını nasıl anlarsın

Yorumları silmeden, altlarına kendi kodunu yaz. Bitirdiğin dosyada yorumları kısaltabilirsin.

## Kullanılacak teknolojiler

| Parça | Ne işe yarar |
|---|---|
| FastAPI | HTTP endpoint'lerini tanımlamak |
| Uvicorn | FastAPI uygulamasını çalıştıran sunucu |
| Pydantic | Gelen/giden verinin şeklini (şemasını) tanımlamak |
| psycopg 3 + psycopg_pool | PostgreSQL'e bağlanmak (projede zaten var) |
| pytest + FastAPI TestClient | Endpoint'leri test etmek |

## Klasör yapısı ve katmanlar

```
api/
  main.py            Uygulamanın giriş noktası, router'ları bağlar
  config.py          .env'den ayarları okur
  db.py              Veritabanı bağlantı havuzu
  schemas/           Pydantic modelleri: API'nin DIŞARIYA verdiği JSON'un şekli
  repositories/      SQL sorguları: veritabanından veriyi ÇEKER
  routers/           Endpoint'ler: HTTP isteğini alır, repository'yi çağırır, schema ile döner
  tests/             Testler
```

Bir istek şu yolu izler:

```
HTTP isteği → routers/players.py → repositories/players.py → PostgreSQL
                     ↓
              schemas/player.py (cevabın şekli) → JSON cevap
```

Neden üç katman? Router SQL bilmez, repository HTTP bilmez. Böylece her biri ayrı test edilir ve değiştirilir. Bu ayrımı "separation of concerns" diye araştır.

## Yol haritası (bu sırayla ilerle)

Kural: Bir adımın **KONTROL** kısmı çalışmadan sonraki adıma geçme. Her adımın sonunda uygulamayı çalıştırıp `/docs` sayfasından dene. Bitirdiğin maddenin kutusunu `[x]` yap.

### Aşama 1: Temel (veritabanı yok)

- [x] **Adım 0:** `requirements.txt` (kök dizin): API paketlerini ekle (`fastapi`, `uvicorn[standard]`, `psycopg_pool`, `pytest`, `httpx`) ve `py -m pip install -r requirements.txt` çalıştır.
  ARAŞTIR: `==` ile `>=,<` sürüm yazımı arasındaki fark ne? Hangisini neden seçersin?\
  CEVAP: `==` tam bir sürümü sabitler: her kurulum aynıdır, ama güvenlik ve hata düzeltmeleri ancak elle yükseltince gelir ve başka paketlerle sürüm çakışması çıkabilir. `>=3.2,<4` bir aralık verir: küçük güncellemeler otomatik gelir, `<4` üst sınırı ise kodu bozabilecek bir sonraki büyük sürümü (semantic versioning'de MAJOR) dışarıda tutar; ama iki kurulum farklı sürüm alabilir. Uygulamada tekrarlanabilirlik önemliyse `==` (ya da aralık + `pip freeze` ile ayrı bir lock dosyası), başkalarının kuracağı bir kütüphanede `>=,<` seçilir. Bu proje kök `requirements.txt` dosyasında API paketleri için aralık kullanıyor.
- [x] **Adım 1:** `main.py` → sadece "ADIM 1" bölümü: `app` nesnesi ve `GET /health`.
  ✔ `py -m uvicorn api.main:app --reload` çalışıyor, `/health` → `{"status":"ok"}`

### Aşama 2: Veritabanına bağlanma

- [x] **Adım 2:** `config.py`: `.env` okuma, `settings` nesnesi.
  ✔ Python konsolunda `settings.pg_host` doğru değeri gösteriyor
- [x] **Adım 3:** `db.py`: havuz, `open_pool` / `close_pool`, `get_conn`.
- [x] **Adım 3b:** `main.py` → "ADIM 3" ve "ADIM 3b": lifespan'i bağla, `/health` veritabanını da kontrol etsin.
  ✔ PostgreSQL açıkken `"database": "ok"`, kapalıyken 503

### Aşama 3: İlk kaynak, players (en önemli aşama, acele etme)

Her kaynakta sıra **aynı**: önce schema, sonra repository, en son router.

- [ ] **Adım 4:** `schemas/common.py`: `Page`, `Role`, `QueueType`, `SeasonStatus`, (isteğe bağlı) `ErrorResponse`
- [ ] **Adım 4b:** `schemas/account.py` → sadece `AccountSummary` (`PlayerDetail` buna ihtiyaç duyuyor)
- [ ] **Adım 4c:** `schemas/player.py`: `SocialLink`, `PlayerSummary`, `PlayerDetail`
- [ ] **Adım 5:** `repositories/players.py` → fonksiyon 1–4 (5 bonus, sonra). Her sorguyu **önce pgAdmin'de** çalıştır.
- [ ] **Adım 6:** `routers/players.py` → endpoint 1, 2, 3 (4 bonus, sonra)
- [ ] **Adım 6b:** `main.py` → "ADIM 6+": players router'ını `include_router` ile bağla.
  ✔ `/players`, `/players/vladi`, `/players/yok` (404), `/players?role=ADC` (422)

### Aşama 4: Testler

- [ ] **Adım 7:** `tests/conftest.py`: `client` fixture'ı
- [ ] **Adım 7b:** `tests/test_players.py`: 8 test.
  ✔ `py -m pytest api/tests -v` hepsi yeşil

### Aşama 5: Diğer kaynaklar (aynı kalıbın tekrarı)

- [ ] **Adım 8 (accounts):** `schemas/account.py` (geri kalan modeller) → `repositories/accounts.py` → `routers/accounts.py` → `main.py`'de bağla → `tests/test_accounts.py`
- [ ] **Adım 8b (leaderboard):** `schemas/leaderboard.py` → `repositories/leaderboard.py` → `routers/leaderboard.py` → bağla → test
- [ ] **Adım 9 (matches):** `schemas/match.py` → `repositories/matches.py` → `routers/matches.py` → bağla → test
- [ ] **Adım 9b (champions):** `schemas/champion.py` → `repositories/champions.py` → `routers/champions.py` → bağla → test

> matches ve champions tabloları ancak `lolapp_riot_sync.py --sections matches` (veya `all`) çalıştırıldıysa dolu olur. Boşsa önce birkaç hesap için sync çalıştır.

### Aşama 6: Bonus (istediğin sırayla)

- [ ] `/players/{slug}/live` (players repository fonksiyon 5 + router endpoint 4)
- [ ] Hesabın leaderboard geçmişi (leaderboard repository bonus)
- [ ] Leaderboard için TTL cache, `/matches` için `Cache-Control`
- [ ] CORS ve global exception handler (`main.py` BONUS bölümü)
- [ ] Rate limit, Docker. Bunlar dosyalarda yok, kendin araştır.

### Neden bu sıra?

- **Önce veritabanısız `/health`:** Bir şey bozulduğunda sorunun FastAPI'de mi yoksa PostgreSQL'de mi olduğunu ayırt edebilmek için.
- **Schema → repository → router:** Önce neyi döndüreceğine karar verirsin (sözleşme), sonra veriyi nereden alacağına, en son HTTP'ye nasıl bağlayacağına.
- **Testler ikinci kaynaktan önce:** players'ta öğrendiğin kalıbı testlerle sabitlersen, sonraki kaynakları yazarken bir şeyi bozduğunda hemen fark edersin.

## Çalıştırma

Proje kök dizininde (`lol-data/`):

```bash
py -m uvicorn api.main:app --reload
```

Sonra tarayıcıda http://127.0.0.1:8000/docs adresini aç. FastAPI senin yazdığın endpoint'ler için buraya otomatik bir deneme sayfası koyar.

ARAŞTIR: `api.main:app` ifadesindeki `api.main` ve `app` neyi gösteriyor? `--reload` ne işe yarar, production'da neden kullanılmaz?

CEVAP: `api.main` import edilecek module'dür (`api/main.py`); `:` sonrasındaki `app` o module içindeki FastAPI nesnesinin adıdır. Uvicorn bunu `from api.main import app` gibi import eder. `--reload` kod dosyaları değişince sunucuyu otomatik yeniden başlatır; geliştirirken her değişiklikte sunucuyu elle kapatıp açmazsın. Production'da kullanılmaz: dosyaları sürekli izlemek kaynak harcar, `--workers` ile birlikte çalışmaz (tek process kalır) ve deploy sırasında dosyalar kopyalanırken sunucu yarım kodla yeniden başlayabilir.

## Kurallar (unutma)

- Bu API **sadece okuma** yapacak (GET). Veriyi `lolapp_import_html.py` ve `lolapp_riot_sync.py` yazıyor.
- `riot_id_history` tablosu **asla** API'den dışarı verilmeyecek. Riot politikası eski Riot ID'lerin yayınlanmasını yasaklıyor (bkz. `sql/schema.sql` en alttaki COMMENT).
- `.env` içindeki `RIOT_API_KEY` bu API'de kullanılmayacak. API sadece veritabanını okur.
- Leaderboard **resmî Riot sıralaması değil**. Sadece takip edilen pro hesapları kapsıyor ve cevapta bunu belirtmen gerekiyor.

## Faydalı kaynaklar

- FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/ (adım adım, Türkçe çevirisi de var)
- Pydantic: https://docs.pydantic.dev/latest/concepts/models/
- psycopg 3: https://www.psycopg.org/psycopg3/docs/basic/usage.html
- psycopg_pool: https://www.psycopg.org/psycopg3/docs/advanced/pool.html
- HTTP durum kodları: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
- Tabloların açıklaması: `docs/database.md`
