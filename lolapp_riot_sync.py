#!/usr/bin/env python3
"""LoLApp official Riot API -> existing PostgreSQL schema (separate from JSONL importer).

Read README_RIOT_SYNC_TR.md before use. Stores ranks ONLY for ACTIVE ranked_seasons.
No Riot API calls on import. Live and matches supported only when explicitly requested.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import time
from urllib.parse import quote

import requests

LOG = logging.getLogger("lolapp.riot")
PLATFORM_TO_REGION = {
    "EUW1": "europe", "EUN1": "europe", "TR1": "europe", "RU": "europe", "ME1": "europe",
    "NA1": "americas", "BR1": "americas", "LA1": "americas", "LA2": "americas",
    "KR": "asia", "JP1": "asia",
    "OC1": "sea", "PH2": "sea", "SG2": "sea", "TH2": "sea", "TW2": "sea", "VN2": "sea",
}
QUEUES = ("RANKED_SOLO_5x5", "RANKED_FLEX_SR")
ALLOWED_MATCH_QUEUES = {420, 440}  # Ranked Solo and Flex (no custom matches)


def utc_now():
    return datetime.now(timezone.utc)


def millis_to_datetime(value):
    if not value:
        return None
    return datetime.fromtimestamp(int(value) / 1000, timezone.utc)


def to_json(value):
    return json.dumps(value, ensure_ascii=False)


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

    def mastery(self, platform, puuid):
        return self.get(platform, f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{quote(puuid, safe='')}")

    def match_ids(self, region, puuid, queue, start, count):
        return self.get(region, f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids",
                        {"queue": queue, "start": start, "count": count})

    def match(self, region, match_id):
        return self.get(region, f"/lol/match/v5/matches/{quote(match_id, safe='')}", not_found_ok=True)

    def live(self, platform, puuid):
        return self.get(platform, f"/lol/spectator/v5/active-games/by-summoner/{quote(puuid, safe='')}",
                        not_found_ok=True)


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
             WHERE 1=1"""
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
    puuid = account["puuid"]
    # If PUUID is already known, confirm latest Riot ID from official API.
    official = (client.account_by_puuid(region, puuid) if puuid else
                client.account_by_riot_id(region, account["game_name"], account["tag_line"]))
    if not official or not official.get("puuid"):
        LOG.warning("Account %s Riot ID not resolved: %s#%s", account["id"],
                    account["game_name"], account["tag_line"])
        return None
    new_puuid = official["puuid"]
    if puuid and puuid != new_puuid:
        raise ValueError("Riot returned a different PUUID than the stored one")

    candidates = ([account["platform_id"].upper()] if account["platform_id"] else []) + platforms
    candidates = list(dict.fromkeys(candidates))
    summoner, platform = None, None
    for candidate in candidates:
        summoner = client.summoner(candidate, new_puuid)
        if summoner:
            platform = candidate
            break
    if platform is None:
        LOG.warning("Account %s PUUID found but no valid platform in %s. Use --platforms.",
                    account["id"], ",".join(candidates))

    now = utc_now()
    with conn.transaction():
        with conn.cursor() as cur:
            # Refuse to overwrite a different row linked to the same PUUID.
            cur.execute("SELECT id, player_id FROM riot_accounts WHERE puuid=%s AND id<>%s",
                        (new_puuid, account["id"]))
            conflict = cur.fetchone()
            if conflict:
                raise ValueError(f"Duplicate PUUID! Riot accounts {account['id']} and {conflict['id']} "
                                 "must be reviewed/merged manually")
            new_name = official.get("gameName") or account["game_name"]
            new_tag = official.get("tagLine") or account["tag_line"]
            if (new_name, new_tag) != (account["game_name"], account["tag_line"]):
                # Internal history only (not for display).
                cur.execute("""INSERT INTO riot_id_history
                             (account_id, game_name, tag_line, first_seen_at, last_seen_at)
                             VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                            (account["id"], account["game_name"], account["tag_line"], now, now))
            cur.execute("""UPDATE riot_accounts SET puuid=%s, game_name=%s, tag_line=%s,
                         platform_id=COALESCE(%s,platform_id),
                         summoner_level=COALESCE(%s,summoner_level),
                         profile_icon_id=COALESCE(%s,profile_icon_id),last_synced_at=now()
                         WHERE id=%s""",
                        (new_puuid, new_name, new_tag, platform,
                         summoner.get("summonerLevel") if summoner else None,
                         summoner.get("profileIconId") if summoner else None, account["id"]))
            # Old match participants become clickable once their pro account is resolved.
            cur.execute("UPDATE match_participants SET account_id=%s WHERE puuid=%s AND account_id IS NULL",
                        (account["id"], new_puuid))
            cur.execute("UPDATE live_game_participants SET account_id=%s WHERE puuid=%s AND account_id IS NULL",
                        (account["id"], new_puuid))
            ensure_sync_row(cur, account["id"])
            cur.execute("UPDATE account_sync_state SET last_account_sync_at=now(),updated_at=now() WHERE account_id=%s",
                        (account["id"],))
    return {"puuid": new_puuid, "platform": platform,
            "game_name": official.get("gameName") or account["game_name"],
            "tag_line": official.get("tagLine") or account["tag_line"]}


def seed_champions(conn):
    """Data Dragon has public data (not consuming the user's Riot API rate limit)."""
    try:
        versions = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=20)
        versions.raise_for_status()
        version = versions.json()[0]
        resp = requests.get(f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json",
                            timeout=25)
        resp.raise_for_status()
        champs = resp.json().get("data", {})
    except (requests.RequestException, ValueError, KeyError) as exc:
        LOG.warning("Data Dragon unavailable; will use champion placeholders where needed: %s", exc)
        return 0
    with conn.transaction():
        with conn.cursor() as cur:
            for alias, champ in champs.items():
                try:
                    champion_id = int(champ["key"])
                except (KeyError, ValueError, TypeError):
                    continue
                cur.execute("""INSERT INTO champions (id,ddragon_key,name,image_filename)
                             VALUES (%s,%s,%s,%s) ON CONFLICT (id) DO UPDATE
                             SET ddragon_key=EXCLUDED.ddragon_key, name=EXCLUDED.name,
                                 image_filename=EXCLUDED.image_filename,updated_at=now()""",
                            (champion_id, alias, champ["name"], champ.get("image", {}).get("full")))
    return len(champs)


def ensure_champion(cur, champion_id):
    if not champion_id:
        return None
    champion_id = int(champion_id)
    cur.execute("""INSERT INTO champions(id,ddragon_key,name)
                   VALUES (%s,%s,%s) ON CONFLICT (id) DO NOTHING""",
                (champion_id, f"unknown_{champion_id}", f"Unknown champion {champion_id}"))
    return champion_id


def sync_ranks(conn, client, account_id, platform, puuid):
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


def sync_mastery(conn, client, account_id, platform, puuid):
    entries = client.mastery(platform, puuid)
    stamped = utc_now()
    with conn.transaction():
        with conn.cursor() as cur:
            for entry in entries:
                champ_id = ensure_champion(cur, entry.get("championId"))
                if not champ_id:
                    continue
                cur.execute("""INSERT INTO champion_masteries
                             (account_id,champion_id,mastery_level,mastery_points,points_since_last_level,
                              points_until_next_level,marks_earned,last_play_at,observed_at,extra_data)
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                             ON CONFLICT (account_id,champion_id) DO UPDATE SET
                             mastery_level=EXCLUDED.mastery_level,mastery_points=EXCLUDED.mastery_points,
                             points_since_last_level=EXCLUDED.points_since_last_level,
                             points_until_next_level=EXCLUDED.points_until_next_level,
                             marks_earned=EXCLUDED.marks_earned,last_play_at=EXCLUDED.last_play_at,
                             observed_at=EXCLUDED.observed_at,extra_data=EXCLUDED.extra_data""",
                            (account_id, champ_id, entry.get("championLevel", 0),
                             entry.get("championPoints", 0), entry.get("championPointsSinceLastLevel"),
                             entry.get("championPointsUntilNextLevel"), entry.get("marksEarned"),
                             millis_to_datetime(entry.get("lastPlayTime")), stamped, to_json(entry)))
            ensure_sync_row(cur, account_id)
            cur.execute("UPDATE account_sync_state SET last_mastery_sync_at=now(),updated_at=now() WHERE account_id=%s",
                        (account_id,))
    return len(entries)


def import_match(conn, match_data):
    info = match_data["info"]
    match_id = match_data["metadata"]["matchId"]
    queue_id = int(info["queueId"])
    if queue_id not in ALLOWED_MATCH_QUEUES:
        return False  # Never store custom games through this job.
    platform = match_id.split("_", 1)[0].upper()
    epoch = info.get("gameStartTimestamp") or info.get("gameCreation")
    if not epoch:
        raise ValueError(f"Match {match_id} has no start timestamp")
    began = millis_to_datetime(epoch)
    duration = info.get("gameDuration")
    # Recent Match-V5 gameDuration is seconds; older matches may return milliseconds.
    if isinstance(duration, (int, float)) and duration > 86400:
        duration = int(duration / 1000)
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO matches
                         (match_id,platform_id,queue_id,game_mode,map_id,game_version,started_at,
                          duration_seconds,raw_data)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                         ON CONFLICT (match_id) DO NOTHING""",
                        (match_id, platform, queue_id, info.get("gameMode"), info.get("mapId"),
                         info.get("gameVersion"), began, duration, to_json(match_data)))
            for team in info.get("teams", []):
                tid = team.get("teamId")
                if tid is None:
                    continue
                objectives = team.get("objectives", {})
                def o(name):
                    return (objectives.get(name) or {}).get("kills")
                cur.execute("""INSERT INTO match_teams
                             (match_id,team_id,win,champion_kills,baron_kills,dragon_kills,tower_kills,
                              inhibitor_kills,objectives_json,bans_json)
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)
                             ON CONFLICT (match_id,team_id) DO NOTHING""",
                            (match_id,tid,team.get("win"),o("champion"),o("baron"),o("dragon"),
                             o("tower"),o("inhibitor"),to_json(objectives),to_json(team.get("bans", []))))
            participants = info.get("participants", [])
            for part in participants:
                pid = part.get("participantId")
                tid = part.get("teamId")
                if pid is None or tid is None:
                    continue
                champion_id = ensure_champion(cur, part.get("championId"))
                puuid = part.get("puuid") or None
                cur.execute("SELECT id FROM riot_accounts WHERE puuid=%s LIMIT 1", (puuid,))
                existing = cur.fetchone()
                account_id = existing["id"] if existing else None
                cur.execute("""INSERT INTO match_participants
                             (match_id,participant_id,puuid,account_id,team_id,champion_id,
                              team_position,individual_position,win,kills,deaths,assists,
                              total_minions_killed,neutral_minions_killed,gold_earned,damage_to_champions,
                              damage_taken,vision_score,wards_placed,wards_killed,spell1_id,spell2_id,
                              items_json,perks_json,extra_stats)
                             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                     %s::jsonb,%s::jsonb,%s::jsonb)
                             ON CONFLICT (match_id,participant_id) DO NOTHING""",
                            (match_id,pid,puuid,account_id,tid,champion_id,
                             part.get("teamPosition"),part.get("individualPosition"),part.get("win"),
                             part.get("kills"),part.get("deaths"),part.get("assists"),
                             part.get("totalMinionsKilled"),part.get("neutralMinionsKilled"),
                             part.get("goldEarned"),part.get("totalDamageDealtToChampions"),
                             part.get("totalDamageTaken"),part.get("visionScore"),
                             part.get("wardsPlaced"),part.get("wardsKilled"),
                             part.get("summoner1Id"),part.get("summoner2Id"),
                             to_json([part.get(f"item{i}", 0) for i in range(7)]),
                             to_json(part.get("perks", {})),to_json(part)))
    return True


def sync_matches(conn, client, account_id, platform, puuid, per_queue=10, max_start=0):
    region = PLATFORM_TO_REGION[platform]
    fetched = 0
    for queue in sorted(ALLOWED_MATCH_QUEUES):
        match_ids = client.match_ids(region, puuid, queue, max_start, per_queue)
        for match_id in match_ids:
            existing = db_one(conn, "SELECT 1 FROM matches WHERE match_id=%s", (match_id,))
            if existing:
                continue
            match_data = client.match(region, match_id)
            if not match_data:
                continue
            if import_match(conn, match_data):
                fetched += 1
    update_sync(conn, account_id, "last_match_sync_at")
    return fetched


def sync_live(conn, client, account_id, platform, puuid):
    data = client.live(platform, puuid)
    with conn.transaction():
        with conn.cursor() as cur:
            if data is None:
                # Only mark as ended if this account was a participant in a cached game.
                cur.execute("""UPDATE live_games SET ended_at=now(),expires_at=now()
                             WHERE ended_at IS NULL AND id IN
                             (SELECT live_game_id FROM live_game_participants WHERE account_id=%s)""",
                            (account_id,))
            else:
                game_id = data["gameId"]
                cur.execute("""INSERT INTO live_games
                             (platform_id,riot_game_id,queue_id,game_mode,map_id,started_at,
                              expires_at,bans_json)
                             VALUES (%s,%s,%s,%s,%s,%s,now()+interval '5 minutes',%s::jsonb)
                             ON CONFLICT (platform_id,riot_game_id) DO UPDATE SET
                             last_seen_at=now(),expires_at=now()+interval '5 minutes',ended_at=NULL,
                             bans_json=EXCLUDED.bans_json RETURNING id""",
                            (platform,game_id,data.get("gameQueueConfigId"),data.get("gameMode"),
                             data.get("mapId"),millis_to_datetime(data.get("gameStartTime")),
                             to_json(data.get("bannedChampions", []))))
                live_id = cur.fetchone()["id"]
                cur.execute("DELETE FROM live_game_participants WHERE live_game_id=%s", (live_id,))
                for slot, part in enumerate(data.get("participants", []), start=1):
                    champ = ensure_champion(cur, part.get("championId"))
                    participant_puuid = part.get("puuid") or None
                    cur.execute("SELECT id FROM riot_accounts WHERE puuid=%s LIMIT 1", (participant_puuid,))
                    row = cur.fetchone()
                    cur.execute("""INSERT INTO live_game_participants
                                 (live_game_id,slot,puuid,account_id,team_id,champion_id,
                                  spell1_id,spell2_id,profile_icon_id,is_bot,perks_json)
                                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                                (live_id, slot, participant_puuid, row["id"] if row else None,
                                 part.get("teamId"),champ,part.get("spell1Id"),part.get("spell2Id"),
                                 part.get("profileIconId"), bool(part.get("bot", False)),
                                 to_json(part.get("perks", {}))))
            ensure_sync_row(cur, account_id)
            cur.execute("UPDATE account_sync_state SET last_live_check_at=now(),updated_at=now() WHERE account_id=%s",
                        (account_id,))
    return bool(data)


def snapshot_leaderboards(conn):
    groups = db_all(conn, """SELECT DISTINCT platform_id,queue_type FROM v_current_pro_leaderboard
                             ORDER BY platform_id,queue_type""")
    saved = 0
    for grp in groups:
        with conn.transaction():
            with conn.cursor() as cur:
                season = active_season(cur)
                cur.execute("""INSERT INTO leaderboard_snapshots
                             (season_id,platform_id,queue_type) VALUES (%s,%s,%s) RETURNING id""",
                            (season["id"], grp["platform_id"],grp["queue_type"]))
                snap_id = cur.fetchone()["id"]
                cur.execute("""INSERT INTO leaderboard_entries
                             (snapshot_id,rank_position,account_id,tier,division,lp,wins,losses)
                             SELECT %s,rank_position,account_id,tier,division,lp,wins,losses
                             FROM v_current_pro_leaderboard WHERE season_id=%s AND platform_id=%s
                             AND queue_type=%s""",
                            (snap_id,season["id"],grp["platform_id"],grp["queue_type"]))
                saved += 1
    return saved


def main():
    parser = argparse.ArgumentParser(description="LoLApp PostgreSQL Riot API data sync")
    parser.add_argument("--sections", default="accounts,ranks", help="accounts,ranks,mastery,matches,live or all")
    parser.add_argument("--limit", type=int, default=5, help="Max number of Riot accounts (default 5 for safety; 0=all)")
    parser.add_argument("--account-id", type=int, help="Process one riot_accounts.id")
    parser.add_argument("--after-id", type=int, default=0, help="Continue from an account ID (noninclusive)")
    parser.add_argument("--platforms", default="EUW1", help="Comma-separated platforms to try when unknown (default EUW1)")
    parser.add_argument("--account-region", default="europe", choices=["europe","americas","asia","sea"])
    parser.add_argument("--match-count", type=int, default=10, help="Most recent match IDs per queue, max 100")
    parser.add_argument("--match-start", type=int, default=0, help="Match API offset for manual backfill")
    parser.add_argument("--delay", type=float, default=1.3, help="Minimum interval between Riot API requests")
    parser.add_argument("--leaderboard-snapshot", action="store_true")
    parser.add_argument("--retry-failed", action="store_true", help="Ignore DB next_retry_at throttle")
    parser.add_argument("--dry-run", action="store_true", help="Only list accounts; no Riot API requests or database updates")
    args = parser.parse_args()
    if args.limit < 0 or not 0 <= args.match_count <= 100 or args.match_start < 0 or args.delay < 0 or args.after_id < 0:
        parser.error("invalid --limit/--match-count/--match-start/--delay/--after-id")
    sections = {s.strip().lower() for s in args.sections.split(",") if s.strip()}
    if sections == {"all"}:
        sections = {"accounts", "ranks", "mastery", "matches", "live"}
    if not sections or not sections <= {"accounts", "ranks", "mastery", "matches", "live"}:
        parser.error("invalid --sections")
    platforms = [p.strip().upper() for p in args.platforms.split(",") if p.strip()]
    if any(p not in PLATFORM_TO_REGION for p in platforms):
        parser.error("unknown platform in --platforms")

    from dotenv import load_dotenv
    load_dotenv()
    if not args.dry_run and not os.getenv("RIOT_API_KEY"):
        parser.error("RIOT_API_KEY missing: set it in .env")
    conn = pg_connect()
    try:
        if "ranks" in sections:
            season = db_all(conn, "SELECT id,label FROM ranked_seasons WHERE status='ACTIVE'")
            if len(season) != 1:
                parser.error("ranked_seasons must contain exactly one ACTIVE season")
            LOG.info("Current ACTIVE ranked season: %s", season[0]["label"])
        accounts = load_accounts(conn, args.limit, args.account_id, args.retry_failed, args.after_id)
        LOG.info("Found %d accounts (limit=%d)", len(accounts), args.limit)
        if args.dry_run:
            for acc in accounts:
                print(f"id={acc['id']} player={acc['nickname']} riot_id={acc['game_name']}#{acc['tag_line']} "
                      f"platform={acc['platform_id'] or '?'} puuid={'yes' if acc['puuid'] else 'no'}")
            return 0
        client = RiotClient(os.environ["RIOT_API_KEY"], args.delay)
        if {"matches", "mastery", "live"} & sections:
            LOG.info("Data Dragon: %d champions", seed_champions(conn))
        errors = 0
        for i, acc in enumerate(accounts, start=1):
            aid = acc["id"]
            LOG.info("[%d/%d] %s#%s (account id=%s)", i, len(accounts), acc["game_name"], acc["tag_line"], aid)
            try:
                # Resolve PUUID and platform once. Other sections may then run independently.
                if "accounts" in sections or not acc["puuid"] or not acc["platform_id"]:
                    info = refresh_account(conn, client, acc, args.account_region, platforms)
                    if info is None:
                        LOG.warning("id=%s skipped: Riot ID unresolved", aid)
                        continue
                    puuid, platform = info["puuid"], info["platform"]
                else:
                    puuid, platform = acc["puuid"], acc["platform_id"].upper()
                if not platform:
                    LOG.warning("id=%s skipping platform-bound endpoints; PUUID recorded", aid)
                    continue
                if "ranks" in sections:
                    LOG.info("    rank entries: %s", sync_ranks(conn, client, aid, platform, puuid))
                if "mastery" in sections:
                    LOG.info("    champion masteries: %s", sync_mastery(conn, client, aid, platform, puuid))
                if "matches" in sections and args.match_count > 0:
                    LOG.info("    new matches: %s", sync_matches(conn, client, aid, platform, puuid,
                                                                 args.match_count, args.match_start))
                if "live" in sections:
                    LOG.info("    live game: %s", sync_live(conn, client, aid, platform, puuid))
                update_sync(conn, aid, status="OK")
            except Exception as exc:
                errors += 1
                LOG.error("    failed account id=%s: %s", aid, exc)
                update_sync(conn, aid, status="FAILED", error=str(exc))
                if isinstance(exc, RiotError) and exc.status in (401, 403, 429):
                    LOG.error("Stop sync: authentication or rate-limit failure. Inspect Riot API key/limits.")
                    break
        if args.leaderboard_snapshot:
            LOG.info("Leaderboard snapshots: %d", snapshot_leaderboards(conn))
        LOG.info("Finished: accounts=%d failures=%d", len(accounts), errors)
        return 1 if errors else 0
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    raise SystemExit(main())
