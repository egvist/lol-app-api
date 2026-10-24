#!/usr/bin/env python3
"""Rank-only Riot API sync for existing LoLApp PostgreSQL tables.

Updates ACTIVE season current ranked state for existing riot_accounts,
records rank_snapshots, and retains the existing DB-trigger peak logic.
Does not fetch matches, champion mastery, or live games.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import logging
import os
import time
from urllib.parse import quote

import requests
from dotenv import load_dotenv

LOG = logging.getLogger("lolapp.riot.ranks")
PLATFORM_TO_REGION = {
    "EUW1": "europe", "EUN1": "europe", "TR1": "europe", "RU": "europe", "ME1": "europe",
    "NA1": "americas", "BR1": "americas", "LA1": "americas", "LA2": "americas",
    "KR": "asia", "JP1": "asia",
    "OC1": "sea", "PH2": "sea", "SG2": "sea", "TH2": "sea", "TW2": "sea", "VN2": "sea",
}
QUEUES = ("RANKED_SOLO_5x5", "RANKED_FLEX_SR")



def utc_now():
    return datetime.now(timezone.utc)


def pg_connect():
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"), port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "lolapp"), user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"), autocommit=True, row_factory=dict_row,
    )


def db_all(conn, sql, params=()):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def db_one(conn, sql, params=()):
    rows = db_all(conn, sql, params)
    return rows[0] if rows else None


class RiotError(Exception):
    def __init__(self, status, path, message):
        self.status = status
        super().__init__(f"Riot HTTP {status} {path}: {message}")


class RiotClient:
    def __init__(self, api_key, delay=1.3, retries=4):
        self.session = requests.Session()
        self.session.headers.update({"X-Riot-Token": api_key, "User-Agent": "LoLApp-dev/0.1"})
        self.delay = delay
        self.retries = retries
        self.next_request_at = 0.0

    def get(self, route, path, params=None, not_found_ok=False):
        if route.upper() not in PLATFORM_TO_REGION and route.lower() not in set(PLATFORM_TO_REGION.values()):
            raise ValueError(f"Unknown Riot platform/region: {route}")
        url = f"https://{route.lower()}.api.riotgames.com{path}"
        for attempt in range(self.retries + 1):
            wait = max(0.0, self.next_request_at - time.monotonic())
            if wait:
                time.sleep(wait)
            self.next_request_at = time.monotonic() + self.delay
            try:
                response = self.session.get(url, params=params, timeout=(8, 25))
            except requests.RequestException as exc:
                if attempt == self.retries:
                    raise RuntimeError(f"Connection error for {path}: {exc}") from exc
                time.sleep(min(30, 2 ** attempt))
                continue
            if response.status_code == 200:
                return response.json()
            if response.status_code == 404 and not_found_ok:
                return None
            if response.status_code in (429, 500, 502, 503, 504) and attempt < self.retries:
                retry_after = response.headers.get("Retry-After")
                try:
                    pause = float(retry_after) if retry_after is not None else min(60, 2 ** attempt + 1)
                except ValueError:
                    pause = min(60, 2 ** attempt + 1)
                LOG.warning("HTTP %s %s: retry in %.1fs", response.status_code, path, pause)
                time.sleep(max(1, pause))
                continue
            # A bad/expired key is a terminal error, not something to retry for thousands of profiles.
            text = response.text[:180].replace("\n", " ")
            raise RiotError(response.status_code, path, text)
        raise RuntimeError(f"Exhausted API retries: {path}")

    def account_by_riot_id(self, region, game_name, tag_line):
        a, b = quote(game_name, safe=""), quote(tag_line, safe="")
        return self.get(region, f"/riot/account/v1/accounts/by-riot-id/{a}/{b}", not_found_ok=True)

    def account_by_puuid(self, region, puuid):
        return self.get(region, f"/riot/account/v1/accounts/by-puuid/{quote(puuid, safe='')}", not_found_ok=True)

    def summoner(self, platform, puuid):
        return self.get(platform, f"/lol/summoner/v4/summoners/by-puuid/{quote(puuid, safe='')}", not_found_ok=True)

    def league(self, platform, puuid):
        return self.get(platform, f"/lol/league/v4/entries/by-puuid/{quote(puuid, safe='')}")




def active_season(cur):
    # Share-lock season row during DB write; manual season switch cannot cut through a rank update.
    cur.execute("SELECT id, label, season_year FROM ranked_seasons WHERE status='ACTIVE' FOR SHARE")
    rows = cur.fetchall()
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one ACTIVE season; found {len(rows)}")
    return rows[0]


def ensure_sync_row(cur, account_id):
    cur.execute("INSERT INTO account_sync_state (account_id) VALUES (%s) ON CONFLICT DO NOTHING", (account_id,))


def update_sync(conn, account_id, field=None, status="OK", error=None):
    with conn.transaction():
        with conn.cursor() as cur:
            ensure_sync_row(cur, account_id)
            updates = ["sync_status=%s", "last_error=%s", "updated_at=now()"]
            params = [status, (error or "")[:1500] if error else None]
            if field is not None:
                assert field in ("last_account_sync_at", "last_rank_sync_at", "last_mastery_sync_at",
                                 "last_match_sync_at", "last_live_check_at")
                updates.append(f"{field}=now()")
            if status == "FAILED":
                updates.append("next_retry_at=now() + interval '5 minutes'")
            else:
                updates.append("next_retry_at=NULL")
            cur.execute(f"UPDATE account_sync_state SET {', '.join(updates)} WHERE account_id=%s",
                        (*params, account_id))


def load_accounts(conn, limit, only_id, retry_failed, after_id=0):
    sql = """SELECT a.id,a.player_id,a.puuid,a.game_name,a.tag_line,a.platform_id,
                    p.nickname,st.sync_status,st.next_retry_at
             FROM riot_accounts a JOIN players p ON p.id=a.player_id
             LEFT JOIN account_sync_state st ON st.account_id=a.id
             WHERE (a.platform_id = 'EUW1' OR a.platform_id IS NULL)"""
    params = []
    if only_id is not None:
        sql += " AND a.id=%s"; params.append(only_id)
    if after_id:
        sql += " AND a.id>%s"; params.append(after_id)
    if not retry_failed:
        sql += " AND (st.next_retry_at IS NULL OR st.next_retry_at <= now())"
    sql += " ORDER BY a.id"
    if limit:
        sql += " LIMIT %s"; params.append(limit)
    return db_all(conn, sql, tuple(params))


def refresh_account(conn, client, account, region, platforms):
    """Resolve missing PUUID/platform only, without syncing match/mastery data."""
    puuid = account["puuid"]
    if not puuid:
        official = client.account_by_riot_id(region, account["game_name"], account["tag_line"])
        if not official or not official.get("puuid"):
            LOG.warning("Could not resolve Riot ID for account %s", account["id"])
            return None
        puuid = official["puuid"]
        # Refuse to overwrite a different account with the same PUUID.
        duplicate = db_one(conn, "SELECT id FROM riot_accounts WHERE puuid=%s AND id<>%s", (puuid, account["id"]))
        if duplicate:
            raise ValueError(f"PUUID already belongs to account {duplicate['id']}")
    candidates = ["EUW1"]  # Only EU West (EUW1) is supported.
    platform = None
    for candidate in dict.fromkeys(candidates):
        if client.summoner(candidate, puuid):
            platform = candidate
            break
    if platform is None:
        LOG.warning("Account %s could not be resolved on EUW1", account["id"])
        return None
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("UPDATE riot_accounts SET puuid=%s, platform_id=%s, last_synced_at=now() WHERE id=%s",
                        (puuid, platform, account["id"]))
            ensure_sync_row(cur, account["id"])
            cur.execute("UPDATE account_sync_state SET last_account_sync_at=now(),updated_at=now() WHERE account_id=%s", (account["id"],))
    return {"puuid": puuid, "platform": platform}



def sync_ranks(conn, client, account_id, platform, puuid):
    if platform != "EUW1":
        raise ValueError(f"Only EUW1 accounts are supported, received {platform}")
    entries = client.league(platform, puuid)
    queue_map = {r["queueType"]: r for r in entries if r.get("queueType") in QUEUES}
    timestamp = utc_now()
    with conn.transaction():
        with conn.cursor() as cur:
            season = active_season(cur)
            # Always create a row for both queues; empty/Unranked = NULL current.
            for queue in QUEUES:
                entry = queue_map.get(queue)
                tier = str(entry["tier"]).upper() if entry else None
                division = entry.get("rank") if entry else None
                lp = entry.get("leaguePoints") if entry else None
                wins = entry.get("wins") if entry else None
                losses = entry.get("losses") if entry else None
                if tier in {"MASTER", "GRANDMASTER", "CHALLENGER"}:
                    division = None
                cur.execute("""INSERT INTO account_season_ranks (account_id,season_id,queue_type)
                             VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""",
                            (account_id, season["id"], queue))
                cur.execute("""SELECT * FROM account_season_ranks
                             WHERE account_id=%s AND season_id=%s AND queue_type=%s FOR UPDATE""",
                            (account_id, season["id"], queue))
                previous = cur.fetchone()
                if previous["finalized_at"]:
                    raise RuntimeError(f"ACTIVE season {season['label']} has finalized rank row")
                changed = any((previous[key] != value) for key, value in {
                    "current_tier": tier, "current_division": division, "current_lp": lp,
                    "current_wins": wins, "current_losses": losses
                }.items())
                # Never demote peak; existing DB trigger handles current > peak.
                cur.execute("""UPDATE account_season_ranks SET current_tier=%s,current_division=%s,
                             current_lp=%s,current_wins=%s,current_losses=%s,current_observed_at=%s
                             WHERE id=%s""", (tier, division, lp, wins, losses, timestamp, previous["id"]))
                if changed and entry:
                    cur.execute("""INSERT INTO rank_snapshots
                                 (account_season_rank_id,tier,division,lp,wins,losses,observed_at)
                                 VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                                (previous["id"], tier, division, lp, wins, losses, timestamp))
            ensure_sync_row(cur, account_id)
            cur.execute("UPDATE account_sync_state SET last_rank_sync_at=now(),updated_at=now() WHERE account_id=%s",
                        (account_id,))
    return [(q, queue_map[q].get("leaguePoints")) for q in queue_map]


def main():
    parser = argparse.ArgumentParser(description="LoLApp current ranks/peak LP sync only")
    parser.add_argument("--limit", type=int, default=5, help="Number of existing accounts (0=all)")
    parser.add_argument("--account-id", type=int, help="One riot_accounts.id")
    parser.add_argument("--after-id", type=int, default=0)
    parser.add_argument("--delay", type=float, default=1.3, help="Minimum time between API calls")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="List accounts without Riot API calls or updates")
    args = parser.parse_args()
    if args.limit < 0 or args.after_id < 0 or args.delay < 0:
        parser.error("--limit, --after-id and --delay must not be negative")
    load_dotenv()
    if not args.dry_run and not os.getenv("RIOT_API_KEY"):
        parser.error("RIOT_API_KEY is missing from the environment/.env")
    with pg_connect() as conn:
        season = db_all(conn, "SELECT id,label FROM ranked_seasons WHERE status='ACTIVE'")
        if len(season) != 1:
            parser.error("Exactly one ACTIVE ranked_seasons row is required")
        LOG.info("ACTIVE ranked season: %s", season[0]["label"])
        accounts = load_accounts(conn, args.limit, args.account_id, args.retry_failed, args.after_id)
        LOG.info("Selected %d accounts", len(accounts))
        if args.dry_run:
            for acc in accounts:
                print(f"id={acc['id']} player={acc['nickname']} riot_id={acc['game_name']}#{acc['tag_line']} "
                      f"platform={acc['platform_id'] or '?'} puuid={'yes' if acc['puuid'] else 'no'}")
            return 0
        client = RiotClient(os.environ["RIOT_API_KEY"], delay=args.delay)
        errors = 0
        for index, acc in enumerate(accounts, 1):
            aid = acc["id"]
            LOG.info("[%s/%s] account=%s player=%s", index, len(accounts), aid, acc["nickname"])
            try:
                if not acc["puuid"] or not acc["platform_id"]:
                    info = refresh_account(conn, client, acc, "europe", ["EUW1"])
                    if info is None:
                        LOG.warning("Skipping account %s (missing PUUID/platform)", aid)
                        continue
                    puuid, platform = info["puuid"], info["platform"]
                else:
                    puuid, platform = acc["puuid"], acc["platform_id"].upper()
                result = sync_ranks(conn, client, aid, platform, puuid)
                LOG.info("    Updated rank LP: %s", result)
                update_sync(conn, aid, status="OK")
            except Exception as exc:
                errors += 1
                LOG.error("Account %s failed: %s", aid, exc)
                update_sync(conn, aid, status="FAILED", error=str(exc))
                if isinstance(exc, RiotError) and exc.status in (401, 403, 429):
                    LOG.error("Stopping due to Riot authentication / rate-limit error")
                    break
        LOG.info("Completed: selected=%d failed=%d", len(accounts), errors)
        return 1 if errors else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    raise SystemExit(main())

