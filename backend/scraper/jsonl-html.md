# Importer girdi formatı: LOLPros HTML kayıtları (JSONL)

[lolapp_import_html.py](lolapp_import_html.py), LOLPros oyuncu profil
sayfalarının kaydedilmiş HTML'lerini okuyup PostgreSQL'e aktarır. Bu doküman
importer'a verilecek dosyanın nasıl olması gerektiğini ve sayfalardan hangi
bilgilerin alındığını anlatır.

Böyle bir dosyanın [url-html-collector](https://github.com/egvist/url-html-collector)
ile nasıl üretileceği için: [docs/collecting-html.md](../docs/collecting-html.md).
Importer'ın seçenekleri ve LP/sezon kuralları için:
[docs/html-import.md](../docs/html-import.md).

> Kaydedilmiş HTML dosyaları büyük olur ve oyunculara ait bilgiler içerir.
> Repoya ekleme; `data/` gibi git'e girmeyen bir klasörde tut.

## Kayıt formatı

Önerilen format JSONL'dir: her satırda bir profil sayfasını taşıyan tek bir JSON
nesnesi bulunur. url-html-collector'ın `output/pages.jsonl` çıktısı bu formattadır
ve doğrudan kullanılabilir.

```json
{"requested_url": "https://lolpros.gg/player/<slug>", "url": "https://lolpros.gg/player/<slug>", "title": "<Oyuncu> on LOLPros.GG", "body": "<body>...</body>", "captured_at": "2026-10-13T12:23:20.668849+00:00"}
```

| Alan | Gerekli mi? | Importer'da kullanımı |
|---|---|---|
| `body` | Evet | Profil HTML'si. `html_body` veya `html` adıyla da kabul edilir |
| `url` | Önerilir | Oyuncunun `slug` değeri `/player/<slug>` kısmından alınır. Yoksa `requested_url`, o da yoksa `--source-url` kullanılır; hiçbiri yoksa slug görünen addan üretilir |
| `requested_url` | Hayır | `url` yoksa yedek olarak kullanılır |
| `captured_at` | Önerilir | ISO 8601 zaman. İlk LP gözleminin zamanı olur; yılı aktif sezon yılından farklıysa o kaydın LP'si yazılmaz. Yoksa import zamanı kullanılır |
| `title` | Hayır | Kullanılmaz |

Dosya satır satır okunduğu için binlerce sayfalık büyük dosyalar belleğe tamamen
yüklenmez.

### Desteklenen diğer girdiler

- **JSON array**: `[{...}, {...}]`. Stream ederek okunur.
- **Sarmalanmış JSON**: `{"items": [...]}`. `items`, `results`, `pages`,
  `records`, `data` veya `players` anahtarlarından biri olabilir.
- **Tek JSON nesnesi**: Tek bir sayfa. Birden fazla satıra yayılmış (pretty-printed)
  JSON yalnız 32 MiB'a kadar kabul edilir; daha büyükse JSONL kullan.
- **Klasör**: İçindeki `.jsonl`, `.ndjson`, `.json`, `.html`, `.htm` ve `.txt`
  dosyalarının hepsi alt klasörler dahil okunur.
- **Eski TXT formatı**: Her sayfanın önünde `URL: https://lolpros.gg/player/<slug>`
  satırı, ardından sayfanın HTML'si.

Uzantı önemli değil: `{` veya `[` ile başlayan bir `.txt` dosyası JSON olarak okunur.

## Sayfada beklenen içerik

Her kayıt bir LOLPros **oyuncu profil sayfası** olmalı ve sayfa tamamen yüklendikten
sonra kaydedilmiş olmalı. Importer `.profile-details h1.name` elementini bulamazsa
o kaydı `ERROR` ile atlar. Hata sayfaları, Cloudflare doğrulama ekranları veya yarım
yüklenmiş sayfalar bu şekilde elenir. Collector'da
`--ready-selector ".profile-details h1.name"` kullanmak bu kayıtları baştan azaltır.

Importer'ın okuduğu bilgiler:

| Bilgi | HTML kaynağı | Hedef tablo |
|---|---|---|
| Görünen ad | `.profile-details h1.name` | `players.nickname` |
| Ülke | `.profile-details .keypoint i.fi-xx` (ilk bayrak) | `players.country_code` |
| Pozisyon | keypoint içindeki `img[alt]` | `players.main_role` |
| Sosyal linkler | `.profile-details .social-media a[href]` | `player_socials` |
| Riot hesapları | `.accounts-list button.account[aria-label]` (`Ad#TAG`) | `riot_accounts` |
| Seçili hesap | `.accounts-list button.account.--selected` | Rank kartlarının bağlandığı hesap |
| Current / Peak rank | `#current-elo`, `#peak-elo` içinde `.rank`, `.league-points`, `.games .wins`, `.games .losses` | `account_season_ranks`, `rank_snapshots` |

Takım, kadro, rank geçmişi, isim geçmişi ve canlı oyun bilgileri sayfada bulunsa da
importer bunları **almaz**.

> **Bilinen sınır:** Tek hesaplı oyuncuların profillerinde `.accounts-list`
> hesap listesi bulunmaz. Importer hesapları yalnız bu listeden okuduğu için bu
> oyuncular `players` tablosuna yazılır ama Riot hesapları ve başlangıç rank'ları
> eklenmez.

## Sayfada bulunan diğer veriler

Her profil sayfasının `body` kısmında bir `window.__LOLPROSGG__` script'i bulunur.
Bu script, görünen HTML'den daha fazlasını taşır: her hesabın `gamename`, `tagline`,
`server` ve `encrypted_puuid` alanları, `rank`/`peak`/`seasons[]` kayıtları, rank
geçmişi (`state.profile.league.rankings[]`), isim geçmişi (`summoner_names[]`),
ligler ve takımlar.

Bu script **JSON değil**, parametrelerle sıkıştırılmış bir JavaScript IIFE'sidir
(`server:q` gibi değerler değişken referansıdır). Okumak istersen `eval` ile
çalıştırma; bir JavaScript parser'ı kullan. Oyuncu verisi `state.profile.profile`
ve `state.profile.league` altındadır.

Tüm alanların ayrıntılı analizi için:
[docs/lolpros-html-fields.md](../docs/lolpros-html-fields.md).

## Dikkat edilecekler

- **Zamanlar**: Rank kartlarındaki `time` yalnızca gün/ay gösterir (`31/08`);
  importer bunu tarih olarak kullanmaz. Gerçek zaman için `captured_at` alanını
  doldur.
- **Peak**: LOLPros'ta kaydedilmiş en yüksek rank'tır, oyuncunun tüm kariyerindeki
  en yüksek rank'ı olmayabilir.
- **Bozuk satır**: JSONL'de bir satır geçerli JSON değilse importer o dosyayı
  okumayı bırakır. Collector zorla kapatıldıysa son satır yarım kalabilir; o satırı
  silip tekrar çalıştır.
- **Tekrar çalıştırma**: Aynı dosyayı tekrar vermek güvenlidir. Oyuncular `slug`
  ile güncellenir, mevcut Current LP değeri ezilmez.
- **Anlık görüntü**: Bu dosya yalnızca ilk veri yüklemesi içindir. Güncel rank
  verisi `lolapp_riot_sync.py` ile Riot API'den gelir.
