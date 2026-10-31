# Collecting LOLPros Player HTML (`url-html-collector`)

This guide documents how the initial `pages.jsonl` dataset was created from LOLPros player profile pages, and how that dataset is imported into the LoLApp PostgreSQL database.

The HTML collector is maintained separately at [egvist/url-html-collector](https://github.com/egvist/url-html-collector). It is **not** part of this repository.

## Data pipeline

```text
urls.txt
   |
   v
url-html-collector
   |
   v
output/pages.jsonl
   |
   | copy to LoLApp
   v
backend/data/pages.jsonl
   |
   v
backend/scraper/lolapp_import_html.py
   |
   v
PostgreSQL
```

The collector opens each URL in a visible CloakBrowser window, waits for the player profile to render, and saves the rendered HTML as one JSON object per line in a JSONL file.

> **Scope:** This pipeline is intended for **initial player-data ingestion**. Ongoing rank and account updates use the Riot API synchronization process rather than repeatedly importing HTML snapshots.

## 1. Install the collector

Requirements:

- Python 3.10 or newer
- A graphical desktop environment (the browser window is visible)
- Access to the separate collector repository

From Git Bash on Windows:

```bash
git clone https://github.com/egvist/url-html-collector.git
cd url-html-collector
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp urls.example.txt urls.txt
```

CloakBrowser downloads its own Chromium build on the first run.

## 2. Prepare the URL list

Put one LOLPros player profile URL per line in `urls.txt`:

```text
https://lolpros.gg/player/vladi
https://lolpros.gg/player/caps
```

The collector ignores blank lines and lines beginning with `#`, and collects duplicate URLs only once.

Use **player profile URLs**, because the importer derives the player's unique `slug` from the `/player/<slug>` portion of the URL.

## 3. Collect rendered HTML

Start with a small sample:

```bash
.venv/Scripts/python collector.py \
  --urls urls.txt \
  --auto --resume --limit 5 \
  --ready-selector ".profile-details h1.name" \
  --timeout 180
```

Then collect the full URL list:

```bash
.venv/Scripts/python collector.py \
  --urls urls.txt \
  --auto --resume \
  --ready-selector ".profile-details h1.name" \
  --timeout 180
```

### Important options and behavior

| Option / behavior | Description |
|---|---|
| `--ready-selector ".profile-details h1.name"` | Waits for the player-name element expected by the importer; helps avoid recording partially rendered profiles. |
| `--auto` | Saves without interactive confirmation; failed URLs are written to `output/errors.jsonl`, and collection continues. |
| `--resume` | Skips URLs already present in `output/pages.jsonl`, allowing interrupted collection to resume. |
| `--limit 5` | Limits a test run to a small number of URLs. |
| `--timeout 180` | Sets the page readiness timeout used by the collector. |

The collector does **not** automatically solve Cloudflare or CAPTCHA challenges. If a verification page appears, complete it manually in the browser.

Pressing `Ctrl+C` allows the current record to finish before stopping. A forced shutdown can leave a truncated final JSONL line. If the importer later fails to parse that line, remove the incomplete line and retry collection.

### Output format

Each successfully captured page is appended to `output/pages.jsonl` as a single JSON object:

```json
{
  "requested_url": "https://lolpros.gg/player/vladi",
  "url": "https://lolpros.gg/player/vladi",
  "title": "Vladi on LOLPros.GG",
  "body": "<body>...</body>",
  "captured_at": "2026-10-13T12:23:20.668849+00:00"
}
```

The example above is formatted across multiple lines for readability; **the actual JSONL file must contain one complete JSON object per line**.

### How the importer uses the fields

| Field | Importer usage |
|---|---|
| `body` | Rendered profile HTML: player identity, social links, Riot accounts, and rank cards. |
| `url` / `requested_url` | Used to derive the player's `slug`; `requested_url` is the fallback. |
| `captured_at` | Timestamp of the initial LP observation. If its year differs from the active ranked season, the importer does not write that LP observation. |
| `title` | Not used by the importer. |

## 4. Import the dataset into PostgreSQL

Copy the generated file into this repository's `backend/data/` directory.

Assuming the collector and `lol-data` folders are siblings, and **from the `lol-data` repository root**:

```bash
cp ../url-html-collector/output/pages.jsonl backend/data/pages.jsonl
```

`backend/data/` contains large, local datasets and should not be committed to Git unless a specific sanitized dataset is intentionally tracked. Check `.gitignore` before staging changes.

Run a small dry run before writing to PostgreSQL:

```bash
cd backend
python -u scraper/lolapp_import_html.py data/pages.jsonl --dry-run --limit 5
```

Then perform the import:

```bash
python -u scraper/lolapp_import_html.py data/pages.jsonl 2>&1 | tee import.log
```

On a Windows installation where `py` is preferred, `py -u` may be used in place of `python -u`. When the virtual environment is activated, `python` is the simplest choice.

The importer logs `OK ...` for successfully checked records during a dry run, `SAVED ...` for imported records, and `ERROR ...` for failed records.

For the complete importer options, database tables, and LP/season handling rules, see [HTML import documentation](html-import.md).

## 5. Recollecting or reimporting profiles

Re-running the importer using the same or an updated dataset is supported:

- Existing players are matched and updated by `slug`.
- Existing current LP values are not overwritten by the initial HTML import.
- The import remains an **initial ingestion** process, not the source of ongoing ranked updates.

For later updates, use the Riot API synchronization script:

```text
backend/lolapp_riot_sync.py
```

In the current workflow, the relevant sections are `accounts` and `ranks`. Account identity and current/peak rank data are refreshed from Riot APIs, with ranked-season information maintained in PostgreSQL. Do not recollect old HTML pages to initialize LP for a new season.

## 6. Data ownership and boundaries

This collection pipeline primarily supplies the initial player, social-link, Riot-account, and rank-related records. It does **not** populate the professional-team or esports competition datasets.

Those features are handled separately by the PandaScore integration and local discovery/catalog services. The distinction matters: LOLPros HTML, Riot Solo Queue ranks, and professional esports match data come from different sources and should not be treated as interchangeable.

## 7. Troubleshooting checklist

| Symptom | Check |
|---|---|
| A profile was not collected | Check `output/errors.jsonl`, browser verification pages, and whether the readiness selector still exists. |
| Collector resumes without fetching an URL | The URL may already be present in `output/pages.jsonl`; `--resume` skips completed captures. |
| JSON decoding fails at the end of `pages.jsonl` | Inspect the final line for truncation caused by an interrupted write. |
| A player has no initial LP | Check the HTML rank card, `captured_at`, and active season year. Missing LP is not necessarily an import failure. |
| Importer cannot find `data/pages.jsonl` | Run it from `backend/` as shown above, or adjust the path to match your working directory. |
| Unexpected files appear in `git status` | Ensure large JSONL datasets, logs, and `.env` files are ignored before committing. |

---

**Related documentation:** [HTML importer](html-import.md) · [Collector repository](https://github.com/egvist/url-html-collector)
