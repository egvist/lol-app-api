# LOLPros JSONL → PostgreSQL importer (`lolapp_import_html.py`)

> Bu script `data/` klasöründe durur ve git'e girmez; sadece yerel makinede bulunur.

Bu sürüm **gönderilen gerçek export formatına** göre hazırlandı. Her kayıt aşağıdaki yapıda bir JSON nesnesidir:

```json
{"url":"https://lolpros.gg/player/vladi","title":"Vladi on LOLPros.GG","body":"<body>...</body>","requested_url":"https://lolpros.gg/player/vladi","captured_at":"2026-10-13T12:23:20.668849+00:00"}
```

5900+ kayıt bir dosyadaysa **satır başına bir JSON nesnesi (JSONL/NDJSON)** veya **JSON array (`[{...},{...}]`)** olabilir. Her iki format da desteklenir. 5900 ayrı `.json`/`.txt` dosyası bir klasördeyse klasör de verilebilir. Tek bir JSON nesnesi de desteklenir. Önceki `URL: ...` başlıklı HTML/TXT formatı da çalışır.

## 1. Ön koşul

Kurulum (`.env`, bağımlılıklar, şema) için kök dizindeki [README](../README.md) dosyasına bak. `ranked_seasons` tablosunda **tam bir adet** `ACTIVE` sezon bulunmalı.

## 2. Çalıştırma

**Önce 5 oyuncuyu test et (DB'ye dokunmaz):**

```bash
py -u data/lolapp_import_html.py data/pages.jsonl --dry-run --limit 5
```

Gerçek dosyan `.txt` ise `data/pages.jsonl` yerine kendi TXT dosya adını yaz. İçerik JSONL ise uzantının `.txt` olması sorun değil.

**İlk 5 oyuncuyu PostgreSQL'e yaz (bağlantıyı test etmek için):**

```bash
py -u data/lolapp_import_html.py data/pages.jsonl --limit 5
```

**Bütün kayıtları PostgreSQL'e yaz:**

```bash
py -u data/lolapp_import_html.py data/pages.jsonl 2>&1 | tee import.log
```

**Yarıda kesilirse örneğin 2501. kayıttan devam et:**

```bash
py -u data/lolapp_import_html.py data/pages.jsonl --start-at 2501 2>&1 | tee import_resume.log
```

> `--start-at` tek bir büyük dosyada pratik kullanım içindir. Tekrar baştan çalıştırmak da güvenlidir: mevcut oyuncu `slug`'ı, sosyal bağlantılar ve Riot hesapları tekrar oluşturulmaz. Eski HTML, mevcut Current LP değerlerini ezmez. Bir profil ayrı transaction ile kaydedilir: işlem yarıda kesilse önceki başarılı kayıtlar saklanır.

**Bir klasörde farklı dosyalar:**

```bash
py -u data/lolapp_import_html.py saved_players/ 2>&1 | tee import.log
```

**İlk iki oyuncunun parse edilmiş JSON çıktısını incele:**

```bash
py data/lolapp_import_html.py data/pages.jsonl --dry-run --limit 2 --print-json
```

Program her profil için `OK ...` veya `SAVED ...` yazdırır; hata varsa `ERROR ...` ve dosya/URL bilgisi basar. `--dry-run` PostgreSQL bağlantısı açmaz.

## 3. Hangi tablolar dolduruluyor?

| Tablo | HTML'den çıkarılan değerler |
|---|---|
| `players` | `nickname`, `slug`, `country_code`, `main_role` |
| `player_socials` | `platform`, `url` (X, Twitch, Instagram, Leaguepedia vb. **href** içeren linkler) |
| `riot_accounts` | Her hesap için `game_name`, `tag_line` ve `player_id`; PUUID daha sonra Riot API'dan gelecek |
| `account_season_ranks` | Aktif sezon için **her Riot hesabına ayrı SoloQ satırı**; yalnız seçili hesabın HTML Current ve Peak Tier/LP, current wins/losses verileri doldurulur |
| `rank_snapshots` | HTML'deki seçili hesabın ilk Current rank gözlemi (sadece bir kez) |
| `ranked_seasons` | **Sadece okunur**: Aktif sezon sorgulanır, sezon yılı komutla verilmez |

**Takım bilgileri kesinlikle alınmaz.** `teams` / `team_memberships` tabloları bu script tarafından değiştirilmez. Eski sezon LP kartları alınmaz; maç, canlı maç, mastery, profesyonel turnuva ve PUUID için Riot API / başka kaynak kullanılacak.

### Sezonun ve LP'nin korunması

- HTML'deki tek seçili Riot hesabının Current/Peak LP bilgileri ilk aktarımda alınır; diğer Riot hesaplarının sezon satırları `NULL` Current/Peak ile açılır.
- HTML'nin `captured_at` alanı mevcutsa ilk LP snapshot zamanı olarak kullanılır. **Bu, LOLPros'un Peak'e gerçekten ulaşıldığı zaman anlamına gelmez.**
- Kaydın `captured_at` yılı aktif sezon yılından farklıysa o HTML'nin LP'si **yeni sezona yazılmaz**; oyuncu ve hesapları yine kaydedilir.
- İleride Riot API Current LP'yi güncelleyecek ve var olan SQL trigger'ı daha yüksek rank geldiyse Peak değerini yükseltecek.
- S16 tamamlandığında S16 satırları korunur; S17 için yeni ayrı satırlar Riot API updater'ıyla doldurulur. Bu importer gelecek sezonların geçmiş LP'sini belirlemek için kullanılmaz.

### Örnek: Vladi (gönderilen gerçek JSON)

- `players`: Vladi / `vladi` / `GR` / `MIDDLE`.
- `riot_accounts`: 8 Riot ID (yalnızca mevcut sayfada listelenenler).
- `player_socials`: X, Twitch ve Leaguepedia olmak üzere 3 bağlantı.
- Seçili Riot hesabı: `J1HUIV#000`.
- Seçili hesap HTML Current: Challenger **3864 LP**, 1175W/1015L.
- HTML Peak: Challenger **5464 LP**.
- Diğer 7 hesap için aktif sezon satırı oluşturulur, rank alanları `NULL` kalır.

## 4. pgAdmin kontrol sorguları

```sql
SELECT COUNT(*) AS player_count FROM players;
SELECT COUNT(*) AS account_count FROM riot_accounts;
SELECT COUNT(*) AS rank_row_count FROM account_season_ranks;

SELECT p.nickname, a.game_name, a.tag_line,
       s.label, r.current_tier, r.current_lp, r.peak_tier, r.peak_lp
FROM players p
JOIN riot_accounts a ON a.player_id = p.id
LEFT JOIN account_season_ranks r ON r.account_id = a.id
LEFT JOIN ranked_seasons s ON s.id = r.season_id
WHERE p.slug = 'vladi'
ORDER BY a.id;
```

## 5. Sınırlar ve uyarılar

- 5900+ kayıt formatını destekleyen streaming parser var, ancak bu ortamda **yalnızca gönderdiğin tekil Vladi JSON'unu** ve bundan üretilmiş küçük bir JSONL/array testini işleyerek doğruladım. Gerçek büyük export'un her kaydının sağlam olduğunu henüz doğrulayamadım.
- Bu ortamda kullanıcının kendi PostgreSQL sunucusuna bağlanıp gerçek `INSERT` testi yapılamadı. İlk 5 kaydı yazarak kontrol et.
- Gerçek JSONL'de her satır ayrı geçerli JSON nesnesi olmalı. Bir satır bozuksa dosyayı okuma durur ve hata yazılır; önce JSONL export'unu düzelt.
- Kodu aynı anda birden fazla importer olarak aynı DB'ye karşı çalıştırma; önce tek süreçle içe aktar.
- `country_code` şemamız tek ülke saklar; birden fazla uyruk gösteren sayfalarda **ilk bayrak** seçilir.
- HTML'de `href` bulunmayan Discord kullanıcı adı vb. bağlantılar sosyal tabloda saklanmaz.
- `.env` ve Riot API anahtarlarını GitHub'a yükleme.
