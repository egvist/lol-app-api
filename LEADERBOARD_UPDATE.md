# LoL Stats API — Haftalık Riot Rank Sync ve Leaderboard Snapshot

Bu projede **otomatik Task Scheduler / cron kullanılmıyor**. Rank verilerini ve leaderboard geçmişini yaklaşık **haftada bir** manuel güncelliyoruz.

## Tek komutla haftalık güncelleme

Proje kök klasöründe, `.venv` aktifken:

```bash
python -m scripts.weekly_leaderboard_update --season 2026 -- python lolapp_rank_sync.py
```

> **Önemli:** `python lolapp_rank_sync.py` burada örnek sync komutudur. Dosyanın gerçek yolunu ve normalde kullandığın parametreleri `--` işaretinden sonra aynen yaz. Script başka klasördeyse yolu değiştir. `--` öncesindeki parametreler haftalık güncelleme aracına, sonrasındakiler Riot sync komutuna aittir.

Bu komut sırasıyla:

1. **Riot API Rank Sync** başlatır; seçilen hesapların güncel rank/LP verilerini PostgreSQL'e yazar.
2. Sync işlemi **sıfırdan farklı çıkış koduyla biterse** snapshot oluşturmayı durdurur.
3. Sync başarılı çıkış koduyla tamamlanırsa `create_leaderboard_snapshot()` çalışır. `v_current_pro_leaderboard` görünümündeki o anki sıralama `leaderboard_snapshots` ve `leaderboard_entries` tablolarına kaydedilir.

**Dikkat:** Sync scriptinin `0` ile çıkması, bütün hesapların güncellendiğini tek başına garanti etmez. API rate limit, hatalı API key, atlanan hesaplar, `--limit` gibi filtreler ve sync loglarını kontrol et. Yalnızca bir kısmı yenilenen hesaplarla alınmış snapshot, eski LP verilerini içerebilir.

## Haftalık değişim ne demek?

Mevcut `/leaderboard?season=2026` endpoint'indeki:

- `rank_position`: güncel veritabanı sıralaması.
- `previous_rank`: **bir önceki snapshot'taki** hesap sırası; karşılaştırma yoksa `null`.
- `rank_change`: **son snapshot sırası ile bir önceki snapshot sırası** arasındaki fark (`previous_snapshot_rank - latest_snapshot_rank`). Pozitif değer yükseliş, negatif değer düşüş demektir.

Karşılaştırma **son iki kayıtlı snapshot** arasındadır; zorunlu olarak tam 7 günlük değildir. Haftalık komut erken veya geç çalıştırılırsa ölçülen süre de değişir. Ayrıca `rank_position` canlı veritabanı görünümünden, `rank_change` ise snapshot'lardan gelir: snapshot sonrası yeni sync yapılırsa bu iki alan farklı zamanları temsil edebilir.

İlk snapshot: **24 Ekim 2026, 23:19:49 (+02), ID 1, 68 hesap**. İlk karşılaştırma için ikinci bir snapshot gerekir.

## Snapshot kontrolü

pgAdmin'de:

```sql
SELECT
    s.id,
    s.captured_at,
    s.platform_id,
    s.queue_type,
    COUNT(e.account_id) AS entries
FROM leaderboard_snapshots s
LEFT JOIN leaderboard_entries e ON e.snapshot_id = s.id
GROUP BY s.id, s.captured_at, s.platform_id, s.queue_type
ORDER BY s.captured_at DESC
LIMIT 5;
```

API'de:

```text
http://127.0.0.1:8000/leaderboard?season=2026
```

## Yalnızca snapshot almak istersen

Riot API rank sync'i zaten ayrı çalıştırdıysan:

```bash
python -m scripts.create_leaderboard_snapshot --season 2026
```

Bu komut **Riot API'ye istek atmaz**; yalnızca PostgreSQL'deki mevcut sıralamayı kaydeder. Üst üste gereksiz snapshot almamaya dikkat et.

## Sezon değişiminde

`2026` sabitini aktif sezon yılıyla (ör. `2027`) değiştir. Snapshot servisi yalnızca `ACTIVE` sezonu kabul eder. Yeni sezonda ilk snapshot alınırken önceki sezonun snapshot'ları karşılaştırmaya dahil edilmez.

## Kısa kontrol listesi

- [ ] PostgreSQL çalışıyor ve Riot API key geçerli.
- [ ] Haftalık birleşik komut gerçek rank sync yolu ve parametreleriyle çalıştırıldı.
- [ ] Sync logları kontrol edildi; kapsamdaki hesaplar güncellendi.
- [ ] Yeni snapshot'ın tarihi ve `entries` sayısı doğrulandı.
- [ ] `/leaderboard` yanıtında `previous_rank` ve `rank_change` alanları kontrol edildi.
