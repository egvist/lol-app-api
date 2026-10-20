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
# KARAR VER (cevabın doğrusu yok, ama nedenini yazabilmelisin):
#   - created_at / updated_at dışarı verilmeli mi?
#   - id dışarı verilmeli mi, yoksa sadece slug mı? URL'lerde hangisini
#     kullanacaksın? (İpucu: lolpros.gg/player/<slug>)
# =============================================================================
