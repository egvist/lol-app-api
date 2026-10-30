from typing import Literal
from pydantic import BaseModel


class CareerTeam(BaseModel):
    id: int
    name: str
    image_url: str | None = None

class CareerPlayer(BaseModel):
    id: int
    nickname: str
    role: str | None = None
    image_url: str | None = None

class CareerOpponent(BaseModel):
    id: int
    name: str
    image_url: str | None = None


class LastResult(BaseModel):
    match_id: int
    opponent: CareerOpponent | None = None
    team_score: int | None = None
    opponent_score: int | None = None
    winner_id: int | None = None

class CareerEntry(BaseModel):
    tournament_id: int
    tournament_name: str
    league_name: str | None = None
    begin_at: str | None = None
    end_at: str | None = None
    placement: str | None = None
    last_result: LastResult | None = None
    team: CareerTeam
    roster: list[CareerPlayer]

class CareerHistoryResponse(BaseModel):
    player_id: int
    status: Literal["matched", "not_matched", "unavailable"]
    total: int
    limit: int
    offset: int
    items: list[CareerEntry]
