from pydantic import BaseModel


class SoloQRank(BaseModel):
    account_id: int
    tier: str
    division: str | None = None
    lp: int
    wins: int | None = None
    losses: int | None = None


class TeamSoloQPlayer(BaseModel):
    pro_player_id: int
    nickname: str
    role: str | None = None
    image_url: str | None = None
    local_player_id: int | None = None
    solo_queue: SoloQRank | None = None


class TeamSoloQSummary(BaseModel):
    total_players: int
    ranked_players: int
    average_lp: float | None = None
    challenger_count: int
    grandmaster_count: int
    master_count: int


class TeamSoloQResponse(BaseModel):
    team_id: int
    team_name: str
    team_image_url: str | None = None
    season: int
    summary: TeamSoloQSummary
    roster: list[TeamSoloQPlayer]

class TeamRanking(BaseModel):
    eligible: bool
    ranking_score: float | None = None
    ranked_players: int
    total_players: int


class TeamLeaderboardEntry(TeamSoloQResponse):
    position: int | None = None
    ranking: TeamRanking


class TeamLeaderboardResponse(BaseModel):
    season: int
    total: int
    limit: int
    offset: int
    items: list[TeamLeaderboardEntry]