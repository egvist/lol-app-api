from pydantic import BaseModel, Field

from api.schemas.team_catalog import TeamCatalogEntry


class LeagueSummary(BaseModel):
    id: int
    name: str
    image_url: str | None = None
    slug: str | None = None


class LeagueListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[LeagueSummary]


class LeagueDetail(LeagueSummary):
    series: list[dict] = Field(default_factory=list)


class LeagueTeamsResponse(BaseModel):
    league_id: int
    season: int
    total: int
    limit: int
    offset: int
    items: list[TeamCatalogEntry]