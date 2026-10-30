from pydantic import BaseModel, Field


class MatchTeam(BaseModel):
    id: int
    name: str
    acronym: str | None = None
    image_url: str | None = None


class StandingEntry(BaseModel):
    rank: int
    team: MatchTeam


class TournamentStandingsResponse(BaseModel):
    tournament_id: int
    total: int
    limit: int
    offset: int
    items: list[StandingEntry] = Field(default_factory=list)


class MatchOpponent(BaseModel):
    team: MatchTeam
    score: int | None = None


class GameSummary(BaseModel):
    id: int
    position: int
    status: str | None = None
    winner_id: int | None = None


class MatchSummary(BaseModel):
    id: int
    name: str | None = None
    status: str
    scheduled_at: str | None = None
    begin_at: str | None = None
    end_at: str | None = None
    winner_id: int | None = None
    number_of_games: int | None = None
    league_id: int | None = None
    serie_id: int | None = None
    tournament_id: int
    opponents: list[MatchOpponent] = Field(default_factory=list)
    games: list[GameSummary] = Field(default_factory=list)


class TournamentMatchesResponse(BaseModel):
    tournament_id: int
    total: int
    limit: int
    offset: int
    items: list[MatchSummary] = Field(default_factory=list)