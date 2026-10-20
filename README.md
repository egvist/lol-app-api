# lol-data

Profesyonel LoL oyuncularının verisini PostgreSQL'de toplayan araçlar:

1. **LOLPros import (tek sefer):** `data/pages.jsonl` içindeki LOLPros sayfalarından oyuncu, sosyal bağlantı, Riot hesabı ve başlangıç LP verisini aktarır.
2. **Riot API sync (tekrarlı):** Hesapları resmi Riot API ile zenginleştirir (PUUID, rank, mastery, maçlar, canlı oyun, leaderboard).

## Klasör yapısı

```
data/lolapp_import_html.py   LOLPros JSONL/HTML → PostgreSQL importer (git'e girmez)
lolapp_riot_sync.py          Riot API → PostgreSQL sync
test_riot_sync_offline.py    Ağsız smoke testler
api/                         FastAPI okuma API'si (öğrenme çalışması, bkz. api/README.md)
sql/schema.sql               25 tabloluk şema (boş DB'ye bir kez)
sql/switch_season_example.sql  Sezon geçişi örneği (S16 → S17)
data/                        pages.jsonl + importer, yerel kalır (git'e girmez)
docs/                        Ayrıntılı dokümanlar
```

## Kurulum (Windows / Git Bash)

```bash
py -m pip install -r requirements.txt
cp .env.example .env   # PGPASSWORD ve RIOT_API_KEY değerlerini doldur
```

Boş bir `lolapp` veritabanında şemayı kur:

```bash
psql -v ON_ERROR_STOP=1 -d lolapp -f sql/schema.sql
```

Ardından **tam bir** `ACTIVE` sezon tanımla (tarihleri gerçek sezona göre ayarla):

```sql
INSERT INTO ranked_seasons (season_year, label, starts_at, ends_at, status)
VALUES (2026, 'S16', '2026-01-01', '2027-01-01', 'ACTIVE');
```

## Kullanım

```bash
# 1) LOLPros verisini aktar (önce --dry-run --limit 5 ile dene)
py -u data/lolapp_import_html.py data/pages.jsonl --dry-run --limit 5
py -u data/lolapp_import_html.py data/pages.jsonl 2>&1 | tee import.log

# 2) Riot API ile güncelle (önce küçük limitle dene)
py -u lolapp_riot_sync.py --dry-run --limit 5
py -u lolapp_riot_sync.py --sections accounts,ranks --limit 5

# Testler
py -m unittest test_riot_sync_offline -v
```

## Dokümanlar

| Doküman | İçerik |
|---|---|
| [docs/collecting-html.md](docs/collecting-html.md) | LOLPros HTML'lerini url-html-collector ile `pages.jsonl` olarak toplama |
| [docs/html-import.md](docs/html-import.md) | Importer seçenekleri, doldurulan tablolar, LP/sezon kuralları |
| [docs/riot-sync.md](docs/riot-sync.md) | Sync bölümleri, platform çözümleme, maçlar, limitler, kontrol sorguları |
| [docs/database.md](docs/database.md) | 25 tablonun kolonları, ilişkileri ve veri akışı |
| [docs/lolpros-html-fields.md](docs/lolpros-html-fields.md) | LOLPros sayfalarından çıkarılabilecek alanların analizi |

`.env` ve Riot API anahtarını asla commit'leme.
