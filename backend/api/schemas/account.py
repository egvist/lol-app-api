
from datetime import datetime
from pydantic import BaseModel, Field


class AccountSummary(BaseModel):
    id: int
    game_name: str
    tag_line: str
    platform_id: str | None = None
    summoner_level: int | None = None

class RankValue(BaseModel):
    tier: str | None = None
    division: str | None = None
    lp: int | None = None
    wins: int | None = None
    losses: int | None = None

class SeasonRank(BaseModel):
    account_id: int
    season_label: str
    queue_type: str
    current: RankValue
    peak: RankValue


class AccountDetail(AccountSummary):
    player_id: int


class RankHistoryEntry(BaseModel):
    tier: str | None = None
    division: str | None = None
    lp: int | None = None
    wins: int | None = None
    losses: int | None = None
    observed_at: datetime


class RankHistoryResponse(BaseModel):
    account_id: int
    season_label: str
    queue_type: str
    history: list[RankHistoryEntry] = Field(default_factory=list)