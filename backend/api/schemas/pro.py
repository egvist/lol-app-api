from typing import Literal
from pydantic import BaseModel

class ProTeam(BaseModel):
    id: int
    name: str
    acronym: str | None = None
    image_url: str | None = None


class ProPlayer(BaseModel):
    id: int
    nickname: str
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    image_url: str | None = None
    current_team: ProTeam | None = None


class ProProfileResponse(BaseModel):
    player_id: int
    nickname: str
    status: Literal["matched", "not_matched", "unavailable"]
    pro_player: ProPlayer | None = None