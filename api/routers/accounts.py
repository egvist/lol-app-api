from fastapi import APIRouter, Depends, HTTPException, Path, Query
from psycopg import Connection

from api.db import get_conn
from api.repositories import accounts as account_repo
from api.schemas.account import (
    AccountDetail,
    SeasonRank,
    RankHistoryResponse,
    RankHistoryEntry,
)
from api.schemas.common import QueueType

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)


@router.get("/{account_id}", response_model=AccountDetail)
def get_account_detail(account_id: int = Path(ge=1), conn: Connection = Depends(get_conn),):
    account = account_repo.get_account_by_id(conn, account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    return AccountDetail(**account)


@router.get("/{account_id}/ranks", response_model=list[SeasonRank])
def get_account_ranks(account_id: int = Path(ge=1),season: int = Query(..., ge=2026),conn: Connection = Depends(get_conn),):
    account = account_repo.get_account_by_id(conn, account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    ranks = account_repo.get_account_ranks(
        conn,
        account_id,
        season,
    )

    return ranks



@router.get("/{account_id}/rank-history",response_model=RankHistoryResponse,)
def get_account_rank_history(account_id: int = Path(ge=1),season: int = Query(..., ge=2026),queue_type: QueueType = Query(...),limit: int = Query(100, ge=1, le=500),conn: Connection = Depends(get_conn),):
    account = account_repo.get_account_by_id(conn, account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    season_row = account_repo.get_season_by_year(conn, season)

    if season_row is None:
        raise HTTPException(
            status_code=404,
            detail="Season not found",
        )

    history = account_repo.get_account_rank_history(
        conn,
        account_id,
        season,
        queue_type.value,
        limit,
    )

    return RankHistoryResponse(
        account_id=account_id,
        season_label=season_row["label"],
        queue_type=queue_type.value,
        history=[
            RankHistoryEntry(**row)
            for row in history
        ],
    )