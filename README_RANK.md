# On-demand rank refresh – entegrasyon

Bu paket mevcut `lolapp_rank_sync.py` scriptindeki `sync_ranks` fonksiyonunu tekrar kullanır.
**Mevcut oyuncu/repository/schemas dosyalarını değiştirmeden** servis dosyasını kopyala.

## 1. Dosyalar

`api/services/rank_refresh.py` → kendi projenin aynı yoluna kopyala.
Proje kökünde en son EUW1-only `lolapp_rank_sync.py` durmalı.
`api/services/__init__.py` boş dosyası ekle (paket yapısı için).

## 2. Router

`api/routers/players.py`:

```python
from fastapi import BackgroundTasks
from api.services.rank_refresh import refresh_player_ranks
```

Mevcut `/players/{slug}/ranks` endpoint fonksiyonunun parametrelerine
`background_tasks: BackgroundTasks` ekle (default değeri olmayan parametre olmalı):

```python
@router.get("/{slug}/ranks", response_model=list[SeasonRank])
def get_player_ranks(
    background_tasks: BackgroundTasks,
    slug: str = Path(min_length=1),
    season: int = Query(...),
    conn: Connection = Depends(get_conn),
):
    player = player_repo.get_player_by_slug(conn, slug)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    # Yalnızca ACTIVE sezon isteklerinde otomatik yenile.
    with conn.cursor() as cur:
        cur.execute("SELECT season_year FROM ranked_seasons WHERE status='ACTIVE'")
        active = cur.fetchone()
    if active is not None:
        active_year = active["season_year"] if isinstance(active, dict) else active[0]
        if active_year == season:
            background_tasks.add_task(refresh_player_ranks, player["id"])

    # Stale-while-revalidate: ilk istekte eski veri (veya []) gelir.
    return player_repo.get_player_ranks(conn, player["id"], season)
```

Önemli: Eğer bu fonksiyon mevcut dosyanda farklı tanımlanmışsa fonksiyonu
körlemesine yapıştırma; importları ve `background_tasks.add_task(...)`
çağrısını uygun yere ekle. Yalnızca rank isteyen endpoint tetikliyor.
`/players` ve `/players/{slug}` read-only kalıyor.

## 3. Ortam / test

`.env` içinde `RIOT_API_KEY`, `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` olmalı.

```bash
py -m uvicorn api.main:app --reload
```

1. `GET /players/vladi/ranks?season=2026` → mevcut DB sonucunu hemen döndürür.
2. Terminalde `Updated player=... account=...` loglarını kontrol et.
3. Aynı endpoint'i tekrar aç → güncellenmiş sonuç döner.
4. Son 48 saatte güncellenmiş hesabın tekrar Riot API'ye gitmediğini doğrula.

DB kontrolü:

```sql
SELECT a.id, a.game_name, st.last_rank_sync_at, st.next_retry_at,
       sr.current_lp, sr.peak_lp, sr.queue_type
FROM riot_accounts a
LEFT JOIN account_sync_state st ON st.account_id=a.id
LEFT JOIN account_season_ranks sr ON sr.account_id=a.id
WHERE a.player_id=(SELECT id FROM players WHERE slug='vladi')
ORDER BY a.id, sr.queue_type;
```

## Sınırlar / iyileştirmeler

- `BackgroundTasks` kalıcı job queue değildir. Süreç kapanırsa job kesilebilir; 5 dakika claim lease bittikten sonra tekrar denenebilir.
- 5 dakikalık lease süresi 5 dakikadan uzun işler için yetersiz kalabilir; aynı hesabı tekrar claim etme riski oluşur. Özellikle ağır yükte Celery/RQ + Redis gibi bir worker veya lease heartbeat gerekir.
- `next_retry_at` claim ve failed retries için paylaşılıyor. Eski toplu sync ile **aynı anda çalıştırma**; gerekiyorsa ayrı `rank_refresh_claim_until` kolonu oluştur.
- Tek process içinde Riot çağrıları sıralı; **birden fazla uvicorn worker** Riot rate-limit için ayrıca paylaşımlı limiter gerektirir.
- `last_rank_sync_at` sadece **başarılı** rank yazımında güncellenir.
- Peak LP mevcut `account_season_ranks` DB trigger'ına bağlı. Trigger yoksa ek kontrol gerekir. Trigger'ın tier sıralamasını nasıl ele aldığını da kontrol et.
- API key geçersiz veya limit doluysa eski veriler gösterilmeye devam eder.
- Leaderboard tetiklemesi **bu sürümde ekli değil**: tek istekle binlerce Riot çağrısı başlatmak güvenli değil. Daha sonra düşük hacimli batch queue gerekir.
