from pydantic import BaseModel, Field


class TeamCatalogEntry(BaseModel):
    id: int
    name: str | None = None
    acronym: str | None = None
    image_url: str | None = None
    league_ids: list[int] = Field(default_factory=list)
    series_ids: list[int] = Field(default_factory=list)


class TeamCatalogResponse(BaseModel):
    season: int
    total: int
    limit: int
    offset: int
    items: list[TeamCatalogEntry]