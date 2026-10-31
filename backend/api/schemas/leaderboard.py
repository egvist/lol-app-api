
from pydantic import BaseModel

from api.schemas.common import Page


class LeaderboardEntry(BaseModel):
    rank_position: int

    player_id: int
    nickname: str
    slug: str

    account_id: int
    game_name: str
    tag_line: str
    platform_id: str

    queue_type: str

    tier: str
    division: str | None = None
    lp: int
    wins: int | None = None
    losses: int | None = None
    previous_rank: int | None = None
    rank_change: int | None = None


class LeaderboardResponse(Page[LeaderboardEntry]):
    season: int
    queue_type: str