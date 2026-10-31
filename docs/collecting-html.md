# LOLPros HTML'lerini toplama (`url-html-collector`)

Importer'ın okuduğu `pages.jsonl` dosyası, LOLPros oyuncu sayfalarının
[egvist/url-html-collector](https://github.com/egvist/url-html-collector) ile
kaydedilmesiyle üretildi. Bu doküman uçtan uca akışı anlatır:

```
urls.txt  ──►  url-html-collector  ──►  output/pages.jsonl  ──►  data/pages.jsonl  ──►  scraper/lolapp_import_html.py  ──►  PostgreSQL
```

`url-html-collector`, sayfaları görünür bir CloakBrowser penceresinde açıp
render edilmiş HTML'yi her sayfa için bir JSON satırı olarak kaydeder.
Collector ayrı bir repo; bu projeye dahil değil.

## 1. Collector kurulumu

Python 3.10+ ve grafik masaüstü gerekir (tarayıcı görünür açılır).

```bash
git clone https://github.com/egvist/url-html-collector
cd url-html-collector
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
cp urls.example.txt urls.txt
```

İlk çalıştırmada CloakBrowser kendi Chromium'unu indirir.

## 2. URL listesi

`urls.txt` içine her satıra bir LOLPros oyuncu URL'si yaz. Boş satırlar ve
`#` ile başlayan satırlar atlanır, tekrar eden URL'ler bir kez toplanır.

```
https://lolpros.gg/player/vladi
https://lolpros.gg/player/caps
```

Importer oyuncunun `slug` değerini URL'deki `/player/<slug>` kısmından alır.
Bu yüzden listede profil URL'leri olmalı.

## 3. HTML'leri toplama

Önce birkaç sayfayla dene:

```bash
.venv/Scripts/python collector.py --urls urls.txt --auto --resume --limit 5 \
    --ready-selector ".profile-details h1.name" --timeout 180
```

Sonra listenin tamamını topla:

```bash
.venv/Scripts/python collector.py --urls urls.txt --auto --resume \
    --ready-selector ".profile-details h1.name" --timeout 180
```

- `--ready-selector ".profile-details h1.name"`: importer'ın profili tanımak için
  aradığı element budur. Element sayfada belirmeden kayıt yapılmaz; böylece yarım
  yüklenmiş veya hata sayfaları daha az kaydedilir.
- `--auto`: soru sormadan kaydeder. Başarısız URL'ler `output/errors.jsonl`
  dosyasına yazılır ve iş devam eder.
- `--resume`: `output/pages.jsonl` içinde zaten olan URL'leri atlar. Yarıda kalan
  toplamaya aynı komutla devam edilir.
- Collector Cloudflare/CAPTCHA çözmez; doğrulama çıkarsa tarayıcıda elle geç.
- Ctrl+C mevcut kayıt bitince güvenle durdurur. Zorla kapatılırsa dosyanın son
  satırı yarım kalabilir; importer bu satırda durur, o satırı silip tekrar dene.

Her başarılı sayfa `output/pages.jsonl` dosyasına tek satır olarak eklenir:

```json
{"requested_url":"https://lolpros.gg/player/vladi","url":"https://lolpros.gg/player/vladi","title":"Vladi on LOLPros.GG","body":"<body>...</body>","captured_at":"2026-10-13T12:23:20.668849+00:00"}
```

Importer bu alanları şöyle kullanır:

| Alan | Kullanım |
|---|---|
| `body` | Profil HTML'si (oyuncu, sosyal linkler, Riot hesapları, rank kartları) |
| `url` / `requested_url` | `slug` için; `url` yoksa `requested_url` kullanılır |
| `captured_at` | İlk LP gözlem zamanı; yılı aktif sezondan farklıysa LP yazılmaz |
| `title` | Kullanılmaz |

## 4. Dosyayı importer'a verme

`output/pages.jsonl` dosyasını bu repodaki `backend/data/` klasörüne kopyala. `data/`
git'e girmez; HTML'ler büyük olabilir ve yerelde kalmalıdır.

```bash
cp ../url-html-collector/output/pages.jsonl backend/data/pages.jsonl
```

Önce veritabanına dokunmadan kontrol et, sonra yaz:

```bash
cd backend
py -u scraper/lolapp_import_html.py data/pages.jsonl --dry-run --limit 5
py -u scraper/lolapp_import_html.py data/pages.jsonl 2>&1 | tee import.log
```

Her profil için `OK ...` (dry-run) veya `SAVED ...` satırı, hatalı kayıtlar için
`ERROR ...` satırı basılır. Importer'ın tüm seçenekleri, doldurduğu tablolar ve
LP/sezon kuralları için [html-import.md](html-import.md) dosyasına bak.

## 5. Yeniden toplama

Importer'ı aynı veya güncellenmiş dosyayla tekrar çalıştırmak güvenlidir:
oyuncular `slug` ile güncellenir, mevcut Current LP ezilmez. Ancak bu akış
**ilk veri yüklemesi** içindir. Sonraki rank güncellemeleri
`lolapp_riot_sync.py` ile Riot API'den gelir; yeni sezon için HTML yeniden
toplanıp LP aktarılmaz.
