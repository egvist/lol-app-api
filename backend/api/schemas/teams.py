from pydantic import BaseModel


class TeamSummary(BaseModel):
    id: int
    name: str
    acronym: str | None = None
    location: str | None = None
    image_url: str | None = None


class RosterPlayer(BaseModel):
    id: int
    nickname: str
    first_name: str | None = None
    last_name: str | None = None
    nationality: str | None = None
    role: str | None = None
    image_url: str | None = None
    active: bool = False


class TeamDetail(TeamSummary):
    roster: list[RosterPlayer]