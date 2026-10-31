

from typing import Generic, TypeVar
from pydantic import BaseModel
from enum import Enum

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


# 2. Player Roles
class Role(str, Enum):
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"
    UTILITY = "UTILITY"


# 3. Ranked Queue Types
class QueueType(str, Enum):
    RANKED_SOLO = "RANKED_SOLO_5x5"
    RANKED_FLEX = "RANKED_FLEX_SR"


# 4. Season Status
class SeasonStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    FINISHED = "FINISHED"


# 5. Error Response (Optional)
class ErrorResponse(BaseModel):
    detail: str