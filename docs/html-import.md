# LOLPros JSONL → PostgreSQL Importer (`lolapp_import_html.py`)

> **Script:** `backend/scraper/lolapp_import_html.py`  
> **Working directory:** `backend/` for all commands below.  
> **Input:** `backend/data/pages.jsonl` is local data and should not be committed to Git.

This importer is designed for the actual JSON export structure produced by the LOLPros HTML collector. Each captured page is represented by a JSON object:

```json
{
  "url": "https://lolpros.gg/player/vladi",
  "title": "Vladi on LOLPros.GG",
  "body": "<body>...</body>",
  "requested_url": "https://lolpros.gg/player/vladi",
  "captured_at": "2026-10-13T12:23:20.668849+00:00"
}
```

The importer supports several input layouts:

- **JSONL/NDJSON:** one JSON object per line, suitable for exports containing 5,900+ player records.
- **JSON arrays:** one file containing `[{...}, {...}]`.
- **A single JSON object.**
- **A directory** containing separate `.json` or `.txt` files.
- **Legacy HTML/TXT** documents prefixed with a `URL: ...` header.

The file extension is not significant: a `.txt` file containing valid JSONL can be imported.

## 1. Prerequisites

See the [root README](../README.md) for project setup, Python dependencies, PostgreSQL configuration, `.env`, and database schema initialization.

The `ranked_seasons` table must contain **exactly one season with `status = 'ACTIVE'`**. The importer reads this season from PostgreSQL rather than accepting a season year on the command line.

## 2. Running the importer

Run these commands from `backend/`.

### Test five player records without writing to PostgreSQL

```bash
py -u scraper/lolapp_import_html.py data/pages.jsonl --dry-run --limit 5
```

`--dry-run` parses the records without opening a PostgreSQL connection.

### Import the first five player records

Use a small batch to verify the database connection and insert behavior:

```bash
py -u scraper/lolapp_import_html.py data/pages.jsonl --limit 5
```

### Import all records

```bash
py -u scraper/lolapp_import_html.py data/pages.jsonl 2>&1 | tee import.log
```

### Resume at record 2,501

```bash
py -u scraper/lolapp_import_html.py data/pages.jsonl --start-at 2501 2>&1 | tee import_resume.log
```

`--start-at` is particularly useful for a large input file. Re-running the complete import is also intended to be safe: existing players are matched by `slug`, social links and Riot accounts are not duplicated, and older HTML data does not overwrite current LP values that have already been updated.

Each player profile is saved in its own transaction. If the process is interrupted, previously committed profiles remain in the database.

### Import a directory of saved profiles

```bash
py -u scraper/lolapp_import_html.py saved_players/ 2>&1 | tee import.log
```

### Inspect the parsed output for two records

```bash
py scraper/lolapp_import_html.py data/pages.jsonl --dry-run --limit 2 --print-json
```

The importer prints `OK ...` for successfully parsed dry-run records, `SAVED ...` for successfully persisted records, and `ERROR ...` with the relevant file or URL when a record fails.

## 3. PostgreSQL tables affected

| Table | Data extracted from LOLPros HTML |
|---|---|
| `players` | `nickname`, `slug`, `country_code`, `main_role` |
| `player_socials` | `platform` and `url` for social links with an actual `href` (for example, X, Twitch, Instagram, and Leaguepedia) |
| `riot_accounts` | `game_name`, `tag_line`, and `player_id` for each listed Riot account; PUUID is resolved later through the Riot API |
| `account_season_ranks` | One Solo Queue row per Riot account in the active season. Only the selected account receives HTML-derived current/peak tier and LP and current wins/losses. |
| `rank_snapshots` | The selected account's initial current-rank observation, recorded once. |
| `ranked_seasons` | **Read-only.** Used to determine the active season; the importer does not create or change seasons. |

**Team data is not imported.** The script does not modify `teams` or `team_memberships`.

It also does not import historical season rank cards, Solo Queue match history, live games, champion mastery, professional tournament matches, or PUUIDs. Those require the Riot API or other suitable sources.

### Season and LP preservation rules

1. The importer initializes current/peak LP using the **single selected Riot account** displayed in the captured HTML. Other listed accounts receive active-season rank rows whose current/peak values may remain `NULL`.
2. When available, `captured_at` is used as the timestamp of the initial LP observation. **It does not indicate when the player actually reached their peak LP.**
3. If the year of `captured_at` differs from the active ranked season year, HTML-derived LP values are **not written into that season**. Player and account details can still be imported.
4. Subsequent current-rank updates come from Riot League-V4. The database's peak-rank trigger updates peak values when a higher observed rank is recorded.
5. When Season 16 (S16) finishes, its existing rank rows are retained. Season 17 (S17) uses separate rows populated by the Riot API synchronization process; old HTML is not used to reconstruct future-season ranks.

### Example: Vladi

The provided sample HTML was described as containing:

| Field | Parsed example |
|---|---|
| Player | Vladi |
| Slug | `vladi` |
| Country | `GR` |
| Role | `MIDDLE` |
| Riot accounts | 8 listed accounts |
| Social links | 3 — X, Twitch, Leaguepedia |
| Selected Riot ID | `J1HUIV#000` |
| Current Solo Queue rank | Challenger, **3,864 LP** |
| Current wins / losses | 1,175 W / 1,015 L |
| Peak rank shown in HTML | Challenger, **5,464 LP** |

The other seven Riot accounts receive season-rank rows without HTML-derived current/peak rank values. These values illustrate the supplied sample capture and should not be interpreted as live rankings.

## 4. Verification queries in pgAdmin

The following queries can help confirm the imported row counts and relationships:

```sql
SELECT COUNT(*) AS player_count FROM players;
SELECT COUNT(*) AS account_count FROM riot_accounts;
SELECT COUNT(*) AS rank_row_count FROM account_season_ranks;

SELECT
    p.nickname,
    a.game_name,
    a.tag_line,
    s.label,
    r.current_tier,
    r.current_lp,
    r.peak_tier,
    r.peak_lp
FROM players AS p
JOIN riot_accounts AS a ON a.player_id = p.id
LEFT JOIN account_season_ranks AS r ON r.account_id = a.id
LEFT JOIN ranked_seasons AS s ON s.id = r.season_id
WHERE p.slug = 'vladi'
ORDER BY a.id;
```

## 5. Limitations and operational notes

- **Large-export validation:** The parser supports the 5,900+ record export format, but the original validation described for this importer covered only a supplied Vladi JSON sample and small derived JSONL/array examples. Do not assume every record in a full export is valid without checking it.
- **Database verification:** The original documentation did not report an actual INSERT test against the user's PostgreSQL instance. Begin with `--limit 5` and inspect the database before importing the full dataset.
- **Malformed JSONL:** Each JSONL line must contain one complete, valid JSON object. A malformed line can stop processing; repair the export and rerun the importer.
- **Concurrent imports:** Avoid running multiple importer processes against the same database simultaneously. Perform the initial import with a single process.
- **Country selection:** `country_code` stores one country. If a player profile displays multiple nationalities, the importer uses the first flag.
- **Social links:** Text-only handles (for example, a Discord username without an `href`) are not stored in `player_socials`.
- **Secrets:** Keep `.env`, PostgreSQL credentials, and Riot API keys out of GitHub.

## 6. Related documentation

- [Project README](../README.md) — setup and configuration.
- [LOLPros HTML collection](collecting-html.md) — creating `pages.jsonl` with the external collector.
- [PostgreSQL database documentation](database.md) — schema, relationships, and update flows.

> **Scope:** This script performs the initial LOLPros player/account import. Continuing Riot account and rank synchronization is handled separately by `lolapp_riot_sync.py`.
