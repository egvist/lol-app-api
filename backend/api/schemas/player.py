


from pydantic import BaseModel, Field
from api.schemas.common import Role
from api.schemas.account import AccountSummary


class SocialLink(BaseModel):
    platform: str
    url: str

class PlayerSummary(BaseModel):
    id: int
    nickname: str
    slug: str
    country_code: str | None = Field(
        default = None,
        description="ISO 3166-1 alpha-2 country code",
        examples=["KR"]
    )
    main_role: Role | None = None

class PlayerDetail(PlayerSummary):
    profile_image_url: str | None = None
    socials: list[SocialLink] = Field(default_factory=list)
    accounts: list[AccountSummary] = Field(default_factory=list)