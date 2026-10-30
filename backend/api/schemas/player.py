# =============================================================================
# schemas/player.py — Oyuncu modelleri (Adım 4)
# =============================================================================
# Pydantic modeli = API'nin dışarı verdiği JSON'un sözleşmesi.
# Veritabanı tablosuyla birebir aynı OLMAK ZORUNDA DEĞİL. Hatta çoğu zaman
# olmamalı: bazı kolonları gizlersin, bazılarını birleştirirsin.
#
# Kaynak tablolar: players, player_socials, riot_accounts (bkz. sql/schema.sql)
#
# GÖREV: Aşağıdaki modelleri yaz (pydantic.BaseModel'den türet):
#
#   1. SocialLink
#        platform, url
#
#   2. PlayerSummary  → liste sayfasında (/players) her satır için
#        id, nickname, slug, country_code, main_role
#        (main_role için common.py'deki Role enum'unu kullan; boş olabilir!)
#
#   3. PlayerDetail  → tek oyuncu sayfasında (/players/{slug})
#        PlayerSummary'deki her şey + profile_image_url
#        + socials: SocialLink listesi
#        + accounts: hesap listesi (schemas/account.py'deki AccountSummary)
#
# ARAŞTIR:
#   - Optional[str] / `str | None` — veritabanında NULL olabilen kolonlar.
#     Hangi kolonlar NULL olabilir? schema.sql'de "NOT NULL" yazmayanlar.
#   - Kalıtım: PlayerDetail, PlayerSummary'den türeyebilir mi? Avantajı ne?
#   - Pydantic Field(): description ve examples vermek /docs sayfasını
#     nasıl iyileştiriyor?
#
# CEVAP:
#   - players: country_code, main_role, profile_image_url NULL olabilir
#     (nickname ve slug NOT NULL). riot_accounts: puuid, platform_id,
#     summoner_level, profile_icon_id, last_synced_at NULL olabilir.
#     player_socials'ta platform ve url NOT NULL. NULL olabilenler modelde
#     `str | None = None`.
#   - Evet: class PlayerDetail(PlayerSummary). Ortak alanlar tek yerde durur;
#     PlayerSummary'ye bir alan eklersen detaya da otomatik eklenir.
#   - Field(description="ISO 3166-1 alpha-2 ülke kodu", examples=["GR"]):
#     /docs'ta alanın yanında açıklama, örnek cevapta gerçekçi bir değer
#     görünür. Frontend yazan kişi kodu açmadan alanın ne olduğunu anlar.
#
# KARAR VER (cevabın doğrusu yok, ama nedenini yazabilmelisin):
#   - created_at / updated_at dışarı verilmeli mi?
#   - id dışarı verilmeli mi, yoksa sadece slug mı? URL'lerde hangisini
#     kullanacaksın? (İpucu: lolpros.gg/player/<slug>)
# =============================================================================


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