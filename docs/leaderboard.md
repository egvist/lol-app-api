# Rank updates and leaderboard snapshots

Rank data is updated in two ways:

1. **Weekly manual update:** ranks are synced for all accounts, then a leaderboard snapshot is taken. There is no scheduled job (cron / Task Scheduler); the command is run by hand.
2. **When a player is requested:** `GET /players/{slug}/ranks` refreshes that player's accounts in the background.

## Weekly update

From the `backend/` folder, with `.venv` activated:

```bash
python -m scripts.weekly_leaderboard_update --season 2026 -- python lolapp_rank_sync.py
```

Arguments before `--` belong to the update tool; everything after it is the rank sync command. The command:

1. Runs the rank sync, which writes current ranks and LP to PostgreSQL.
2. Stops without taking a snapshot if the sync exits with a non-zero code.
3. If the sync succeeds, saves the ranking from the `v_current_pro_leaderboard` view into the `leaderboard_snapshots` and `leaderboard_entries` tables.

An exit code of `0` does not guarantee that every account was updated (rate limits, an invalid key, filters such as `--limit`). Check the sync logs before relying on the snapshot.

If you already ran the sync separately, take only a snapshot (no Riot API requests):

```bash
python -m scripts.create_leaderboard_snapshot --season 2026
```

## Leaderboard fields

In the `GET /leaderboard?season=2026` response:

- `rank_position`: current position in the database.
- `previous_rank`: position in the previous snapshot; `null` if there is nothing to compare against.
- `rank_change`: difference between the last two snapshots (`previous - latest`). A positive value means the account moved up.

The comparison is between the last two snapshots, which are not necessarily exactly 7 days apart. `rank_position` comes from the live view and `rank_change` from snapshots, so a sync run after the latest snapshot can make the two fields refer to different points in time.

To check the latest snapshots:

```sql
SELECT s.id, s.captured_at, s.platform_id, s.queue_type, COUNT(e.account_id) AS entries
FROM leaderboard_snapshots s
LEFT JOIN leaderboard_entries e ON e.snapshot_id = s.id
GROUP BY s.id
ORDER BY s.captured_at DESC
LIMIT 5;
```

## Automatic refresh on player requests

`GET /players/{slug}/ranks?season=<active season>` returns the stored data immediately and refreshes the player's accounts in the background with `BackgroundTasks` (stale-while-revalidate). Updated values appear on the next request. The work is done in `api/services/rank_refresh.py`, which reuses `sync_ranks` from `lolapp_rank_sync.py`.

- Only runs for the `ACTIVE` season; accounts updated in the last 48 hours are skipped.
- If `RIOT_API_KEY` is invalid or rate limited, the old data keeps being served.
- `/players`, `/players/{slug}` and `/leaderboard` do not trigger a refresh.

Known limitations:

- `BackgroundTasks` is not a persistent job queue; a job can be cut off if the process stops. The account lock expires after 5 minutes and the account can then be retried.
- Do not run it at the same time as the weekly sync; both use `account_sync_state.next_retry_at`.
- Running several uvicorn workers would need a shared limiter for the Riot rate limit.

## Switching seasons

Change `--season` to the new active season year. The snapshot service only accepts the `ACTIVE` season and does not compare against snapshots from the previous season. Season switch example: [`backend/sql/switch_season_example.sql`](../backend/sql/switch_season_example.sql).
