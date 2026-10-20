"""Import LOLPros JSON/JSONL exports (or saved HTML/TXT), without team parsing.

The initial HTML Current / Peak rank seeds the DB. Subsequent official Riot API rank
updates can replace Current; existing PostgreSQL trigger raises Peak only on increase.
An HTML page includes rank cards only for its selected account. Other accounts
get season-rank rows with NULL current and peak values. Re-importing does not replace an existing Current value.
The active ranked season is selected FROM DATABASE (ranked_seasons.status = ACTIVE); there is NO --season-year flag.
Never use this one-time HTML bootstrap to manage rank data in subsequent seasons.

Usage:
    python lolapp_import_html.py "sajator.txt" --dry-run
    python lolapp_import_html.py "sajator.txt"
    python lolapp_import_html.py my_saved_pages/ --dry-run
    python lolapp_import_html.py "players.jsonl" --limit 3 --dry-run

Input: JSONL with one {"url", "body", "captured_at"} record per line; JSON arrays;
       standalone JSON pages; or older URL-header HTML/TXT exports.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

BASE_URL = "https://lolpros.gg"
ROLE_MAP = {
    "top": "TOP", "jungle": "JUNGLE", "mid": "MIDDLE", "middle": "MIDDLE",
    "bot": "BOTTOM", "bottom": "BOTTOM", "adc": "BOTTOM", "support": "UTILITY",
    "utility": "UTILITY",
}
SOCIAL_HOSTS = {
    "twitter.com": "x", "x.com": "x", "twitch.tv": "twitch",
    "instagram.com": "instagram", "youtube.com": "youtube",
    "lol.fandom.com": "leaguepedia", "liquipedia.net": "liquipedia",
    "gol.gg": "gamesoflegends",
}


@dataclass
class RankCard:
    tier: str
    division: str | None
    lp: int
    wins: int | None
    losses: int | None
    site_date: str | None  # Page's displayed day/month, not a timestamp or guaranteed date


@dataclass
class Profile:
    nickname: str
    slug: str
    source_url: str | None
    country_code: str | None
    main_role: str | None
    socials: list[dict[str, str]] = field(default_factory=list)
    accounts: list[dict[str, str]] = field(default_factory=list)
    selected_riot_id: str | None = None
    current_rank: RankCard | None = None
    peak_rank: RankCard | None = None


def slugify(value: str) -> str:
    norm = unicodedata.normalize("NFKD", value)
    ascii_text = norm.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def unwrap_html(raw: str, url_override: str | None = None) -> tuple[str, str | None]:
    url = url_override
    cleaned = raw.strip()
    if cleaned.startswith("{") or cleaned.startswith('"'):
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, str):
            cleaned = data
        elif isinstance(data, dict):
            url = url or data.get("url") or data.get("source_url")
            for key in ("body", "html_body", "html", "content"):
                if isinstance(data.get(key), str):
                    cleaned = data[key]
                    break
            else:
                raise ValueError("No body / html_body / html / content field in JSON")
    if not url:
        match = re.search(r"^URL:\s*(https?://[^\s]+)", cleaned, flags=re.MULTILINE)
        if match:
            url = match.group(1)
    start = cleaned.find("<body")
    if start >= 0:
        cleaned = cleaned[start:]
    elif "<html" not in cleaned and "<h1" not in cleaned:
        raise ValueError("No HTML body found in file")
    return cleaned, url


VALID_TIERS = {
    "IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND",
    "MASTER", "GRANDMASTER", "CHALLENGER",
}


def _parse_rank_card(soup: BeautifulSoup, card_id: str) -> RankCard | None:
    card = soup.select_one(f"#{card_id} .card.rank-display")
    if card is None:
        return None
    tier_node = card.select_one("p.rank")
    lp_node = card.select_one("p.league-points")
    if tier_node is None or lp_node is None:
        return None
    rank_text = tier_node.get_text(" ", strip=True).upper()
    # LOLPros sometimes writes "Grand Master" (two words) instead of "Grandmaster".
    rank_text = re.sub(r"\s+", " ", rank_text).replace("GRAND MASTER", "GRANDMASTER")
    rank_match = re.fullmatch(r"([A-Z]+)(?:\s+(IV|III|II|I))?", rank_text)
    if not rank_match or rank_match.group(1) not in VALID_TIERS:
        return None
    raw_lp = lp_node.get_text(" ", strip=True)
    lp_match = re.search(r"[\d][\d\s.,]*", raw_lp)
    if not lp_match:
        return None
    lp = int(re.sub(r"\D", "", lp_match.group(0)))
    wins_node = card.select_one(".games .wins")
    losses_node = card.select_one(".games .losses")
    time_node = card.select_one("time")
    return RankCard(
        tier=rank_match.group(1),
        division=rank_match.group(2),
        lp=lp,
        wins=int(wins_node.get_text(strip=True)) if wins_node and wins_node.get_text(strip=True).isdigit() else None,
        losses=int(losses_node.get_text(strip=True)) if losses_node and losses_node.get_text(strip=True).isdigit() else None,
        site_date=(time_node.get("title") or time_node.get_text(" ", strip=True)) if time_node else None,
    )


def _selected_riot_id(soup: BeautifulSoup) -> str | None:
    selected = soup.select_one(".accounts-list button.account.--selected")
    if selected is None:
        return None
    return selected.get("aria-label", "").strip() or None


def parse_profile(raw: str, url_override: str | None = None) -> Profile:
    html, url = unwrap_html(raw, url_override)
    soup = BeautifulSoup(html, "lxml")
    title = soup.select_one(".profile-details h1.name")
    if title is None:
        raise ValueError("No LOLPros player profile (.profile-details h1.name) found in this HTML")
    nickname = title.get_text(" ", strip=True)
    path = urlparse(url).path if url else ""
    found = re.search(r"/player/([^/?#]+)", path)
    slug = found.group(1).lower() if found else slugify(nickname)
    if not slug:
        raise ValueError("Could not determine player slug")

    country = None
    role = None
    for item in soup.select(".profile-details .keypoint"):
        if not country:
            flag = item.select_one("i.fi")
            if flag:
                for cls in flag.get("class", []):
                    if re.fullmatch(r"fi-[a-z]{2}", cls):
                        country = cls[3:].upper()
                        break
        if not role:
            pos_img = item.select_one("img[alt]")
            if pos_img:
                role = ROLE_MAP.get(pos_img.get("alt", "").lower())

    socials = []
    visited = set()
    for a in soup.select(".profile-details .social-media a[href]"):
        href = a.get("href", "")
        absolute = urljoin("https://lolpros.gg", href)
        hostname = (urlparse(absolute).hostname or "").lower().removeprefix("www.")
        platform = next((p for host, p in SOCIAL_HOSTS.items() if hostname == host), None)
        if platform and (platform, absolute) not in visited:
            socials.append({"platform": platform, "url": absolute})
            visited.add((platform, absolute))

    accounts = []
    seen_accounts = set()
    for button in soup.select(".accounts-list button.account"):
        full_id = button.get("aria-label", "").strip()
        if "#" not in full_id:
            continue
        game_name, tag_line = full_id.rsplit("#", 1)
        if not game_name or not tag_line:
            continue
        key = (game_name.casefold(), tag_line.casefold())
        if key not in seen_accounts:
            accounts.append({"game_name": game_name, "tag_line": tag_line})
            seen_accounts.add(key)

    return Profile(
        nickname=nickname, slug=slug, source_url=url,
        country_code=country, main_role=role,
        socials=socials, accounts=accounts,
        selected_riot_id=_selected_riot_id(soup),
        current_rank=_parse_rank_card(soup, "current-elo"),
        peak_rank=_parse_rank_card(soup, "peak-elo"),
    )


def get_active_season(cur) -> tuple[int, str, int]:
    """Read the ONLY ACTIVE ranked season from PostgreSQL.

    The row lock also prevents a concurrent season switch during this import.
    Season creation/transition is deliberately a separate admin operation.
    """
    cur.execute("""SELECT id, label, season_year FROM ranked_seasons
                   WHERE status = 'ACTIVE' FOR SHARE""")
    rows = cur.fetchall()
    if len(rows) != 1:
        raise RuntimeError(
            f"Expected exactly 1 ACTIVE season in ranked_seasons. Found: {len(rows)}. "
            "Define the active season first (e.g. via pgAdmin)."
        )
    return rows[0][0], rows[0][1], rows[0][2]


def seed_html_rank(cur, account_id: int, current: RankCard | None,
                   peak: RankCard | None, season_id: int,
                   observed_at: datetime | None = None) -> bool:
    """Seed selected account rank. Existing current is NEVER overwritten by old HTML.

    Merge an HTML peak only when it outranks the DB's peak. The existing SQL
    trigger automatically promotes a higher Current to Peak for later API syncs.
    """
    if current is None and peak is None:
        return False

    queue = "RANKED_SOLO_5x5"
    # A previously imported HTML page must NEVER seed old LP into a new season.
    # Once any earlier season exists for an account, subsequent seasons are
    # populated exclusively by the Riot API rank updater.
    cur.execute("""SELECT 1 FROM account_season_ranks
                   WHERE account_id = %s AND season_id <> %s
                   LIMIT 1""", (account_id, season_id))
    if cur.fetchone() is not None:
        return False
    cur.execute(
        """SELECT id, current_observed_at, peak_tier, peak_division, peak_lp, finalized_at
           FROM account_season_ranks
           WHERE account_id=%s AND season_id=%s AND queue_type=%s
           FOR UPDATE""",
        (account_id, season_id, queue),
    )
    existing = cur.fetchone()
    imported_at = observed_at or datetime.now(timezone.utc)
    seed_current = current is not None and (existing is None or existing[1] is None)
    if existing is not None and existing[5] is not None:
        return False  # Never rewrite a finished season.

    if existing is None:
        cur.execute(
            """INSERT INTO account_season_ranks
               (account_id,season_id,queue_type,
                current_tier,current_division,current_lp,current_wins,current_losses,current_observed_at,
                peak_tier,peak_division,peak_lp,peak_observed_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               RETURNING id""",
            (account_id, season_id, queue,
             current.tier if current else None, current.division if current else None,
             current.lp if current else None, current.wins if current else None,
             current.losses if current else None, imported_at if current else None,
             peak.tier if peak else None, peak.division if peak else None,
             peak.lp if peak else None, imported_at if peak else None),
        )
        rank_id = cur.fetchone()[0]
    else:
        rank_id = existing[0]
        if seed_current:
            cur.execute(
                """UPDATE account_season_ranks SET
                       current_tier=%s, current_division=%s, current_lp=%s,
                       current_wins=%s, current_losses=%s, current_observed_at=%s
                   WHERE id=%s""",
                (current.tier, current.division, current.lp,
                 current.wins, current.losses, imported_at, rank_id),
            )
        # The SQL trigger handles Current > Peak. A separate comparison handles
        # a historical HTML Peak > Current, even when Current came from Riot.
        if peak:
            cur.execute(
                """UPDATE account_season_ranks SET
                       peak_tier=%s, peak_division=%s, peak_lp=%s, peak_observed_at=%s
                   WHERE id=%s AND
                     (peak_tier IS NULL OR lol_rank_is_higher(
                       %s, %s, %s, peak_tier, peak_division, peak_lp))""",
                (peak.tier, peak.division, peak.lp, imported_at, rank_id,
                 peak.tier, peak.division, peak.lp),
            )

    if seed_current:
        cur.execute(
            """INSERT INTO rank_snapshots
               (account_season_rank_id,tier,division,lp,wins,losses,observed_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT DO NOTHING""",
            (rank_id, current.tier, current.division, current.lp,
             current.wins, current.losses, imported_at),
        )
    return True


def import_profile(cur, profile: Profile, season_id: int,
                   observed_at: datetime | None = None,
                   seed_rank: bool = True) -> dict[str, int]:
    """Upsert one player plus initial HTML fields using the exact existing schema."""
    cur.execute(
        """INSERT INTO players (nickname, slug, country_code, main_role)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (slug) DO UPDATE SET
               nickname = EXCLUDED.nickname,
               country_code = COALESCE(EXCLUDED.country_code, players.country_code),
               main_role = COALESCE(EXCLUDED.main_role, players.main_role),
               updated_at = NOW()
           RETURNING id""",
        (profile.nickname, profile.slug, profile.country_code, profile.main_role),
    )
    player_id = cur.fetchone()[0]

    for social in profile.socials:
        cur.execute(
            """INSERT INTO player_socials (player_id, platform, url)
               VALUES (%s, %s, %s) ON CONFLICT (player_id, platform, url) DO NOTHING""",
            (player_id, social["platform"], social["url"]),
        )

    selected_account_id = None
    account_ids: list[int] = []
    for account in profile.accounts:
        cur.execute(
            """SELECT id, puuid FROM riot_accounts
               WHERE player_id = %s
               AND LOWER(game_name) = LOWER(%s)
               AND LOWER(tag_line) = LOWER(%s)
               LIMIT 1""",
            (player_id, account["game_name"], account["tag_line"]),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                """INSERT INTO riot_accounts (player_id, game_name, tag_line)
                   VALUES (%s, %s, %s) RETURNING id""",
                (player_id, account["game_name"], account["tag_line"]),
            )
            account_id = cur.fetchone()[0]
        else:
            account_id = row[0]
        account_ids.append(account_id)
        # Existing Riot account is untouched; official API data takes precedence.
        full_id = f'{account["game_name"]}#{account["tag_line"]}'
        if profile.selected_riot_id and full_id.casefold() == profile.selected_riot_id.casefold():
            selected_account_id = account_id

    # Every listed account gets a separate SoloQ rank row for the DB's ACTIVE season.
    # Only the HTML-selected account has values at import time; other accounts
    # deliberately start with NULL current/peak. Re-runs never overwrite API data.
    if account_ids:
        for account_id in set(account_ids):
            cur.execute(
                """INSERT INTO account_season_ranks (account_id, season_id, queue_type)
                   VALUES (%s, %s, 'RANKED_SOLO_5x5')
                   ON CONFLICT (account_id, season_id, queue_type) DO NOTHING""",
                (account_id, season_id),
            )

    rank_seeded = False
    if selected_account_id is not None and seed_rank:
        rank_seeded = seed_html_rank(
            cur, selected_account_id, profile.current_rank, profile.peak_rank, season_id,
            observed_at=observed_at
        )

    return {"players": 1, "socials": len(profile.socials),
            "accounts": len(profile.accounts),
            "html_rank_processed": int(rank_seeded),
            "season_rank_rows_ready": len(set(account_ids))}


def collect_files(inputs: list[str]) -> list[Path]:
    paths = []
    for arg in inputs:
        p = Path(arg)
        if p.is_dir():
            paths.extend(sorted(f for f in p.rglob("*")
                                if f.is_file() and f.suffix.lower() in {".html", ".htm", ".txt", ".json", ".jsonl", ".ndjson"}))
        elif p.is_file():
            paths.append(p)
        else:
            raise FileNotFoundError(f"File not found: {arg}")
    return list(dict.fromkeys(paths))



# A saved export has ONE JSON object per player, often on a single long line:
# {"url":"https://lolpros.gg/player/vladi", "body":"<body>...", "captured_at":"..."}
# JSON Lines (JSONL/NDJSON) streams ~5900 pages without loading the whole export.
JSON_ARRAY_KEYS = ("items", "results", "pages", "records", "data", "players")
PROFILE_HEADER_RE = re.compile(
    r"^URL:\s*(https?://(?:www\.)?lolpros\.gg/player/[^\s]+)\s*$",
    re.IGNORECASE,
)


def expand_json_object(obj):
    """Flatten recognized wrappers; do not mix unrelated metadata dictionaries."""
    if isinstance(obj, list):
        for item in obj:
            yield from expand_json_object(item)
    elif isinstance(obj, dict):
        if isinstance(obj.get("body") or obj.get("html_body") or obj.get("html"), str):
            yield obj
        else:
            for key in JSON_ARRAY_KEYS:
                if isinstance(obj.get(key), list):
                    yield from expand_json_object(obj[key])
                    return
            raise ValueError("No body/html field found in JSON record")
    else:
        raise ValueError(f"JSON profile record is not an object: {type(obj).__name__}")


def iter_json_profiles(path: Path):
    """Read JSONL line by line, or a JSON array using streaming ijson.

    Also handles a standalone single-line JSON object or small pretty-printed object.
    """
    with path.open("r", encoding="utf-8-sig") as stream:
        ch = ""
        while not ch or ch.isspace():
            ch = stream.read(1)
            if not ch:
                return
        stream.seek(0)
        if ch == "[":
            # Stream a giant JSON array using only the Python standard library.
            # Only the current entry (~100-500 KB), not the full 5900-entry file,
            # is kept in memory.
            decoder = json.JSONDecoder()
            buf = stream.read(256 * 1024)
            cursor = 0
            while cursor < len(buf) and buf[cursor].isspace():
                cursor += 1
            if cursor >= len(buf) or buf[cursor] != "[":
                raise ValueError("Expected a JSON array")
            cursor += 1
            first = True
            while True:
                while True:
                    while cursor < len(buf) and buf[cursor].isspace():
                        cursor += 1
                    if cursor < len(buf):
                        break
                    piece = stream.read(256 * 1024)
                    if not piece:
                        raise ValueError("File ended before JSON array was closed")
                    buf = buf[cursor:] + piece
                    cursor = 0
                if buf[cursor] == "]":
                    # Empty array or end after an item.
                    cursor += 1
                    if buf[cursor:].strip() or stream.read(1).strip():
                        raise ValueError("Unexpected content after JSON array")
                    return
                if not first:
                    if buf[cursor] != ",":
                        raise ValueError("Missing comma in JSON array")
                    cursor += 1
                first = False
                while True:
                    while cursor < len(buf) and buf[cursor].isspace():
                        cursor += 1
                    if cursor >= len(buf):
                        piece = stream.read(256 * 1024)
                        if not piece:
                            raise ValueError("JSON array ended while expecting data")
                        buf = buf[cursor:] + piece
                        cursor = 0
                        continue
                    try:
                        item, end = decoder.raw_decode(buf, cursor)
                    except json.JSONDecodeError as exc:
                        piece = stream.read(256 * 1024)
                        if not piece:
                            raise ValueError(f"Invalid JSON array: {exc}") from exc
                        # Bounded by the size of a single JSON profile entry.
                        buf = buf[cursor:] + piece
                        cursor = 0
                    else:
                        yield from expand_json_object(item)
                        buf = buf[end:]
                        cursor = 0
                        break
        if ch != '{':
            raise ValueError("JSON file must start with '{' or '['")

        first_line = stream.readline()
        try:
            first_item = json.loads(first_line)
        except json.JSONDecodeError:
            # Pretty-printed standalone JSON is fine for small files. A giant
            # pretty-printed export should be converted to JSONL or JSON array.
            if path.stat().st_size > 32 * 1024 * 1024:
                raise ValueError(
                    "Very large multi-line JSON object. Use JSONL/NDJSON or "
                    "JSON array format instead."
                )
            stream.seek(0)
            yield from expand_json_object(json.load(stream))
            return
        yield from expand_json_object(first_item)
        for line_num, line in enumerate(stream, start=2):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL line {line_num}: {e}") from e
            yield from expand_json_object(item)


def iter_header_html_profiles(path: Path, url_override: str | None = None):
    """Backward compatibility for earlier multi-URL TXT exports."""
    chunks = []
    url = None
    with path.open("r", encoding="utf-8-sig", errors="replace") as stream:
        for line in stream:
            match = PROFILE_HEADER_RE.match(line.strip())
            if match:
                if url is not None and chunks:
                    yield ("".join(chunks), url, None)
                chunks = []
                url = match.group(1)
            chunks.append(line)
    if chunks and "".join(chunks).strip():
        yield ("".join(chunks), url or url_override, None)


def parse_capture_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        when = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return when.astimezone(timezone.utc)
    except ValueError:
        return None


def iter_file_profiles(path: Path, url_override: str | None = None):
    """Yield (HTML, profile URL, captured timestamp) per profile."""
    with path.open("r", encoding="utf-8-sig", errors="replace") as f:
        prefix = f.read(4096).lstrip()
    if path.suffix.lower() in (".json", ".jsonl", ".ndjson") or prefix.startswith(("{", "[")):
        for item in iter_json_profiles(path):
            body = next((item[key] for key in ("body", "html_body", "html")
                         if isinstance(item.get(key), str)), None)
            if body is None:
                raise ValueError("Missing body HTML")
            url = item.get("url") or item.get("requested_url") or url_override
            yield body, url, parse_capture_time(item.get("captured_at"))
    else:
        yield from iter_header_html_profiles(path, url_override)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LOLPros JSONL / JSON array / JSON / HTML -> LoLApp PostgreSQL"
    )
    parser.add_argument("inputs", nargs="+", help="JSONL/NDJSON/JSON/TXT file or directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to PostgreSQL")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N profiles")
    parser.add_argument("--start-at", type=int, default=1, help="Skip earlier records; resume from this 1-based index")
    parser.add_argument("--print-json", action="store_true", help="Show parsed JSON (dry-run only)")
    parser.add_argument("--source-url", help="Fallback URL for standalone HTML input")
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be >= 0")
    if args.start_at < 1:
        parser.error("--start-at must be >= 1")
    if args.print_json and not args.dry_run:
        parser.error("--print-json can only be used with --dry-run")

    paths = collect_files(args.inputs)
    if not paths:
        parser.error("No files to process")
    if args.source_url and len(paths) != 1:
        parser.error("--source-url requires exactly one file")

    conn = None
    if not args.dry_run:
        try:
            import psycopg
            from dotenv import load_dotenv
        except ImportError as e:
            parser.error(f"Missing DB dependency: {e}. Run pip install -r requirements.txt")
        load_dotenv()
        conn = psycopg.connect(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            dbname=os.getenv("PGDATABASE", "lolapp"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD"),
        )
        # Fail fast before parsing ~5900 pages if active season is unset.
        with conn.cursor() as cur:
            season_id, label, season_year = get_active_season(cur)
        conn.commit()
        print(f"ACTIVE SEASON: {label} ({season_year}) id={season_id}", flush=True)

    completed = errors = 0
    totals = {"players": 0, "socials": 0, "accounts": 0,
              "html_rank_processed": 0, "season_rank_rows_ready": 0}
    try:
        for path in paths:
            print(f"FILE: {path.name} ({path.stat().st_size/1024/1024:.1f} MiB)", flush=True)
            try:
                for ix, (raw, url, captured_at) in enumerate(iter_file_profiles(path, args.source_url), start=1):
                    if ix < args.start_at:
                        continue
                    if args.limit and completed + errors >= args.limit:
                        break
                    try:
                        profile = parse_profile(raw, url)
                        if args.dry_run:
                            print(f"[{completed+errors+1}] OK {profile.nickname} ({profile.slug}) "
                                  f"accounts={len(profile.accounts)} socials={len(profile.socials)} "
                                  f"current={profile.current_rank.lp if profile.current_rank else 'NULL'} "
                                  f"peak={profile.peak_rank.lp if profile.peak_rank else 'NULL'}", flush=True)
                            if args.print_json:
                                print(json.dumps(asdict(profile), ensure_ascii=False, indent=2), flush=True)
                        else:
                            with conn.transaction():
                                with conn.cursor() as cur:
                                    season_id, label, season_year = get_active_season(cur)
                                    # Do not import last year's HTML LP into a new active year.
                                    allow_rank = not captured_at or captured_at.year == season_year
                                    result = import_profile(cur, profile, season_id, observed_at=captured_at,
                                                            seed_rank=allow_rank)
                            for k, v in result.items():
                                totals[k] += v
                            extra = " [old HTML: rank skipped]" if not allow_rank else ""
                            print(f"[{completed+errors+1}] SAVED {profile.nickname} ({profile.slug}) "
                                  f"[{label}] accounts={result['accounts']} "
                                  f"rank_seeded={result['html_rank_processed']}{extra}", flush=True)
                        completed += 1
                    except Exception as exc:
                        errors += 1
                        print(f"[{completed+errors}] ERROR {path.name} profile={ix} "
                              f"url={url}: {exc}", file=sys.stderr, flush=True)
            except Exception as exc:
                errors += 1
                print(f"FILE READ ERROR {path.name}: {exc}", file=sys.stderr, flush=True)
            if args.limit and completed + errors >= args.limit:
                break
    finally:
        if conn is not None:
            conn.close()
    print(f"DONE: succeeded={completed} errors={errors} files={len(paths)}", flush=True)
    if not args.dry_run:
        print(f"Total processed fields (not new record count): {totals}", flush=True)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
