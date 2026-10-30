from pydantic import BaseModel, Field


class TournamentSummary(BaseModel):
    id: int
    name: str | None = None
    slug: str | None = None
    begin_at: str | None = None
    end_at: str | None = None
    league_id: int | None = None
    serie_id: int | None = None


class TournamentDetail(TournamentSummary):
    winner_id: int | None = None


class SeriesTournamentsResponse(BaseModel):
    series_id: int
    total: int
    limit: int
    offset: int
    items: list[TournamentSummary] = Field(default_factory=list)