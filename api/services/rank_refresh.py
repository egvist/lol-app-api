"""On-demand, stale-while-revalidate EUW1 rank refresh.

Run through FastAPI BackgroundTasks. Uses account_sync_state.next_retry_at as a
short claim/retry lease, so duplicate requests don't start duplicate refreshes.
Do not run this simultaneously with an unrelated sync job that modifies this field.
"""

from __future__ import annotations

import logging
import os
from threading import Lock

from dotenv import load_dotenv

# Keep the standalone rank-only script at the project root.
from lolapp_rank_sync import (
    RiotClient,
    RiotError,
    pg_connect,
    refresh_account,
    sync_ranks,
    update_sync,
)

LOG = logging.getLogger(__name__)
# One worker process at a time makes calls through this service. For a multi-worker
# deployment, replace with a distributed Riot API rate limiter/job queue.
_process_riot_lock = Lock()


def _claim_stale_accounts(conn, player_id: int) -> list[dict]:
    """Claim eligible accounts atomically using row locks and a temporary lease.

    The 48h TTL uses last *successful* rank sync, not the generic updated_at.
    The lease also prevents immediate retries after an API error.
    """
    with conn.transaction():
        with conn.cursor() as cur:
            # Avoid creating state for non-EUW accounts.
            cur.execute(
                """INSERT INTO account_sync_state(account_id)
                   SELECT id FROM riot_accounts
                   WHERE player_id=%s AND (platform_id='EUW1' OR platform_id IS NULL)
                   ON CONFLICT (account_id) DO NOTHING""",
                (player_id,),
            )
            cur.execute(
                """WITH claimed AS (
                       SELECT st.account_id
                       FROM account_sync_state st
                       JOIN riot_accounts a ON a.id=st.account_id
                       WHERE a.player_id=%s
                         AND (a.platform_id='EUW1' OR a.platform_id IS NULL)
                         AND (st.last_rank_sync_at IS NULL
                              OR st.last_rank_sync_at <= now() - interval '48 hours')
                         AND (st.next_retry_at IS NULL OR st.next_retry_at <= now())
                       FOR UPDATE OF st SKIP LOCKED
                   ), updated AS (
                       UPDATE account_sync_state st
                       SET next_retry_at=now()+interval '5 minutes', updated_at=now()
                       FROM claimed c
                       WHERE st.account_id=c.account_id
                       RETURNING st.account_id
                   )
                   SELECT a.id,a.player_id,a.puuid,a.game_name,a.tag_line,a.platform_id
                   FROM riot_accounts a JOIN updated u ON a.id=u.account_id
                   ORDER BY a.id""",
                (player_id,),
            )
            return cur.fetchall()


def refresh_player_ranks(player_id: int) -> None:
    """FastAPI background task: return cached response first, then refresh due accounts."""
    load_dotenv()
    key = os.getenv("RIOT_API_KEY")
    if not key:
        LOG.error("RIOT_API_KEY missing; cannot refresh player_id=%s", player_id)
        return

    # Keep all Riot calls serialized within a single API process.
    with _process_riot_lock:
        with pg_connect() as conn:
            accounts = _claim_stale_accounts(conn, player_id)
            if not accounts:
                return
            client = RiotClient(key, delay=1.3)
            for account in accounts:
                account_id = account["id"]
                try:
                    if not account["puuid"] or not account["platform_id"]:
                        info = refresh_account(conn, client, account, "europe", ["EUW1"])
                        if info is None:
                            raise ValueError("Account not resolved on EUW1")
                        puuid, platform = info["puuid"], info["platform"]
                    else:
                        puuid, platform = account["puuid"], account["platform_id"].upper()
                    sync_ranks(conn, client, account_id, platform, puuid)
                    update_sync(conn, account_id, status="OK")
                    LOG.info("Updated player=%s account=%s", player_id, account_id)
                except Exception as exc:
                    LOG.warning("Rank refresh failed for account=%s: %s", account_id, exc)
                    try:
                        update_sync(conn, account_id, status="FAILED", error=str(exc))
                    except Exception:
                        LOG.exception("Could not record sync failure account=%s", account_id)
                    if isinstance(exc, RiotError) and exc.status in (401, 403, 429):
                        LOG.error("Riot auth/rate-limit failure; remaining accounts retain claim lease")
                        break
