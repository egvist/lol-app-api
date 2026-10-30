from pydantic import BaseModel, Field

from api.schemas.tournament_results import MatchSummary


class MatchesResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[MatchSummary] = Field(default_factory=list)