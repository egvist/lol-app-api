from pydantic import BaseModel, Field


class SeriesSummary(BaseModel):
    id: int
    name: str | None = None
    begin_at: str | None = None
    end_at: str | None = None


class LeagueSeriesResponse(BaseModel):
    league_id: int
    season: int | None = None
    total: int
    limit: int
    offset: int
    items: list[SeriesSummary] = Field(default_factory=list)