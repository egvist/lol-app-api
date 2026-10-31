# Riot API sync (`lolapp_riot_sync.py`)

Bu script mevcut **25 tabloluk PostgreSQL v2 şemasına** yazar. `pages.jsonl` dosyasını **okumaz**. İlk defa [`lolapp_import_html.py`](html-import.md) ile aktarılmış `riot_accounts` kayıtlarını alır ve resmi Riot API ile zenginleştirir. `teams`, `team_memberships` ve profesyonel turnuva verilerini değiştirmez; bunlar ayrı yetkili espor kaynağından gelecek.

## 1. Ön koşul

Kurulum (`.env`, bağımlılıklar, şema) için kök dizindeki [README](../README.md) dosyasına bak. Komutlar `backend/` klasöründe çalıştırılır. `.env` içinde `RIOT_API_KEY` dolu olmalı ([developer.riotgames.com](https://developer.riotgames.com/)). DB'de **tam bir ACTIVE** ranked season olmalı; program sezonu kendisi oluşturmaz:

```sql
SELECT id, label, season_year, status FROM ranked_seasons;
```

## 2. Önce test et

DB'yi değiştirmez ve API'ye istek göndermez:

```bash
py -u lolapp_riot_sync.py --dry-run --limit 5
```

Yalnızca hesap PUUID, platform, Current/Peak rank verilerini güncelle:

```bash
py -u lolapp_riot_sync.py --sections accounts,ranks --limit 5
```

Tam özellikleri ilk **1 hesap** için test et:

```bash
py -u lolapp_riot_sync.py --sections all --limit 1 --match-count 5
```

Belirli DB hesabını işlemek için:

```bash
py -u lolapp_riot_sync.py --account-id 123 --sections all --match-count 20
```

Tüm hesaplar için sadece rank takibi:

```bash
py -u lolapp_riot_sync.py --sections accounts,ranks --limit 0 2>&1 | tee riot_sync.log
```

Büyük listeyi partiler halinde işlemek için son işlenen hesap ID’sinden devam edebilirsin:

```bash
py -u lolapp_riot_sync.py --sections accounts,ranks --limit 100 --after-id 100
```

Bu örnek yalnızca `riot_accounts.id > 100` olan ilk 100 satırı seçer. ID değerlerini kendi veritabanına göre belirle; ardışık olmaları gerekmez.

**Dikkat:** 5900+ profesyonel oyuncunun çok daha fazla Riot hesabı olabilir. Bir hesap için 2–4 API isteği, maç detayları için ise daha fazlası gerekir; hepsini tek seferde başlatmak yerine önce `--limit 5` ile doğrula. Geliştirme anahtarları süre ve rate limit bakımından sınırlıdır. `429` yanıtları `Retry-After` ile yeniden denenir; sürekli limit veya 401/403 alındığında işlem kesilir.

## 3. Sunucu (platform) çözümleme

Riot ID `gameName#tagLine` hesap PUUID'sini verir, **hangi sunucuda oynadığını kesin söylemez**. Mevcut `riot_accounts.platform_id` varsa öncelik verilir. Yoksa varsayılan `EUW1` denenir; yalnızca Summoner-V4 gerçekten yanıt verirse `platform_id` yazılır. EUW dışında oyuncular için platform adaylarını açıkça ver:

```bash
py -u lolapp_riot_sync.py --platforms EUW1,EUN1,TR1,KR,NA1 --limit 5
```

Bu seçenek her aday sunucu için ek API isteği üretebilir. `--account-region` (varsayılan `europe`), Account-V1 kimlik sorgularının bölgesel rotasıdır; platform değildir. PUUID bulunup sunucu bulunamazsa hesabın `puuid` bilgisi kaydedilir, rank/maç/mastery/canlı bölümleri atlanır; sonraki çalıştırmada yeni adaylarla denenebilir.

## 4. Bölümler

| `--sections` | Riot kaynağı | Veritabanına yazdığı tablolar |
|---|---|---|
| `accounts` | Account-V1 + Summoner-V4 | `riot_accounts`, `riot_id_history` (yalnız dahili), `account_sync_state`; yeni PUUID için eski `match_participants` ve `live_game_participants` bağlantıları |
| `ranks` | League-V4 (PUUID) | `account_season_ranks`, `rank_snapshots`, `account_sync_state` |
| `mastery` | Champion-Mastery-V4 | `champion_masteries`, `champions`, `account_sync_state` |
| `matches` | Match-V5 | `matches`, `match_teams`, `match_participants`, `champions`, `account_sync_state` |
| `live` | Spectator-V5 | `live_games`, `live_game_participants`, `champions`, `account_sync_state` |
| `all` | Yukarıdakilerin hepsi | Yukarıdaki tablolar |

`--leaderboard-snapshot` ekleyerek senkronizasyondan sonra `v_current_pro_leaderboard` view'ından anlık sıralamayı `leaderboard_snapshots` + `leaderboard_entries` tablolarına kaydedebilirsin:

```bash
py -u lolapp_riot_sync.py --sections accounts,ranks --limit 5 --leaderboard-snapshot
```

Sıralama **yalnızca LoLApp'te kayıtlı profesyonel hesapları** kapsar; resmi global Riot sıralaması değildir.

## 5. Current / Peak LP sistemi ve sezonlar

HTML'den başlangıçta alınan Current ve Peak LP'ler `account_season_ranks` tablosunda durur. Riot API'den gelen current rank değiştiğinde SQL trigger'ı otomatik karşılaştırır. Örnek:

| İşlem | `current_lp` | `peak_lp` |
|---|---:|---:|
| HTML import | 3028 | 3258 |
| Riot: 3100 | 3100 | 3258 |
| Riot: 3400 | 3400 | 3400 |
| Riot: 3200 | 3200 | 3400 |

Riot API eski maksimum LP vermez; peak değeri **HTML başlangıç + sonradan gözlemlediğimiz maksimum** olarak tutulur. `rank_snapshots`, değer/değişiklik olduğunda yeni satır ekler. `ranked_seasons` içinde S16 `FINISHED`, S17 `ACTIVE` olduğunda **S16'nın son current/peak değerleri olduğu gibi kalır**; S17 için ayrı yeni satırlar açılır. Sezon kapanırken son snapshot'ın gerçekten kapanışa yakın olması için API güncellemesini sezon bitmeden çalıştır.

Sezon geçişi manuel yapılmalı; `--season-year` parametresi yok. Script her rank yazımı öncesinde DB'deki `ACTIVE` sezonu alır. **Sezonu değiştirmeden önce tüm sync işlerinizin bitmesini sağlayın.**

## 6. Maçları toplama

Varsayılan `--sections` yalnızca `accounts,ranks`. Maç için `--sections matches` veya `--sections all` ekle. `--match-count 10`, **her queue için** son 10 maç ID'sini getirir (SoloQ **420** ve Flex **440**); `--match-start` ile daha eski maça sayfalanabilir. Bir maçın detayları sadece **bir kez** `matches` tablosuna yazılır. `match_teams` iki takımın hedeflerini, `match_participants` maçtaki tüm katılımcıları tutar. `puuid` değerleri `riot_accounts` ile eşleşirse diğer profesyonel oyuncuların profil bağlantılarını oluşturabilirsin. Şimdilik **özel/custom maçları toplamıyoruz**.

Maç istatistiklerini sorgulamak için:

```sql
SELECT p.nickname, a.game_name, mp.champion_id,
       COUNT(*) AS games, SUM(mp.kills) AS kills, SUM(mp.deaths) AS deaths
FROM match_participants mp
JOIN riot_accounts a ON a.id=mp.account_id
JOIN players p ON p.id=a.player_id
GROUP BY p.nickname, a.game_name, mp.champion_id
ORDER BY games DESC LIMIT 20;
```

**Önemli:** `Match-V5` platformdan bağımsız, bölgesel (europe/americas/asia/sea) rota kullanır. Her maçın API'deki `matchId` benzersiz olduğu için aynı maç tekrar indirilmez. `--match-count` geçmişin tamamını otomatik arşivlemez; daha eski maçlar için sonraki çalıştırmalarda `--match-start` kullan.

## 7. Champion Mastery ve canlı maç

Mastery API'si şampiyon bazında güncel mastery level / points verir. Champion metadata resmi Data Dragon üzerinden alınıp `champions` tablosuna eklenir. Data Dragon indirilemezse geçici şampiyon kaydı açılır ve daha sonra güncellenebilir.

Spectator API ile **oyunda olan hesabın o anki maçı** kontrol edilir. Canlı maç verisi geçici önbellek olarak saklanır ve 5 dakika sonra süresi dolar; API 404 döndürürse o hesaba bağlı önceki canlı oyunlar kapanmış olarak işaretlenir. `live` için periyodik ayrı bir job kullan; milyonlarca canlı kayıt biriktirmek için tasarlanmamıştır.

## 8. Tekrar çalışma, güvenlik ve limitler

- HTML importer (`lolapp_import_html.py`) bir kez başlangıç için; Riot senkronizasyonunu sonraki günlerde tekrar çalıştırabilirsin.
- Account PUUID ve maç ID'leri üzerinden tekrar kayıt önlenir. Aynı PUUID'nin iki `riot_accounts` satırına karşılık geldiği algılanırsa **otomatik birleştirmek yerine hata verir**; manuel kontrol gerekir.
- Hesapların eski Riot ID'lerini web sitesinde gösterme. `riot_id_history` **dahili** veridir.
- API anahtarını sadece backend'de sakla; GitHub'a, HTML'e veya frontend'e koyma.
- Bazı Riot ID'leri eski veya hatalı olabilir, özellikle ilk PUUID çözümlemesinde 404 alınabilir.
- `--retry-failed` kullanmazsan DB'de 5 dakikalık yeniden deneme bekleme süresi uygulanır.
- **Canlı Riot istekleri ve senin PostgreSQL'in üzerinde uçtan uca test yapılmadı.** İlk test için `--limit 1` tavsiye edilir.

## 9. SQL kontrol komutları

```sql
-- Güncel/current ve en yüksek/peak LP (aktif ve bitmiş sezonlar)
SELECT p.nickname,a.game_name,a.tag_line,s.label,r.queue_type,
       r.current_tier,r.current_lp,r.peak_tier,r.peak_lp,r.finalized_at
FROM account_season_ranks r
JOIN riot_accounts a ON a.id=r.account_id
JOIN players p ON p.id=a.player_id
JOIN ranked_seasons s ON s.id=r.season_id
ORDER BY p.nickname,s.season_year DESC;

-- PUUID eksik / sunucu eksik hesaplar
SELECT COUNT(*) FILTER (WHERE puuid IS NULL) AS missing_puuid,
       COUNT(*) FILTER (WHERE platform_id IS NULL) AS missing_platform,
       COUNT(*) AS total FROM riot_accounts;

-- Maç sayısı, katılımcı sayısı
SELECT (SELECT count(*) FROM matches) AS matches,
       (SELECT count(*) FROM match_participants) AS participants;

-- API hataları
SELECT account_id, sync_status, last_error, next_retry_at
FROM account_sync_state WHERE sync_status='FAILED';
```

## 10. Riot API dokümantasyonu

- [Riot Developer Portal](https://developer.riotgames.com/apis)
- [LoL Developer Guide](https://developer.riotgames.com/docs/lol)
- [Riot ID → PUUID](https://support-developer.riotgames.com/hc/en-us/articles/22698698001939-League-of-Legends)

**Bu script espor turnuvalarını / kadro geçmişlerini doldurmaz.** Bunların güvenilir ve kullanım izni olan ayrı bir kaynaktan beslenmesi gerekiyor.
