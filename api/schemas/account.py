# =============================================================================
# schemas/account.py — Riot hesabı, rank ve mastery modelleri (Adım 8)
# =============================================================================
# Kaynak tablolar: riot_accounts, account_season_ranks, rank_snapshots,
#                  ranked_seasons, champion_masteries
#
# GÖREV: Şu modelleri yaz:
#
#   1. AccountSummary  → oyuncu detayında hesap listesi
#        id, game_name, tag_line, platform_id, summoner_level, profile_icon_id
#
#        !!! puuid'yi dışarı vermeli misin? Araştır: PUUID Riot'un kalıcı hesap
#        kimliği. Gizli değil ama gerekli de değil. Kararını yorum olarak yaz.
#
#   2. SeasonRank  → bir hesabın bir sezondaki bir kuyruktaki durumu
#        season_label (ranked_seasons.label, ör. "S16"), queue_type,
#        current: tier/division/lp/wins/losses
#        peak: tier/division/lp
#
#        İPUCU: current ve peak'i düz alanlar yerine iç içe iki küçük model
#        (RankValue) yapmak JSON'u daha okunur yapar:
#          {"current": {"tier": "CHALLENGER", "lp": 1200, ...}, "peak": {...}}
#        Ama SQL'den düz satır gelecek. Düz satırı iç içe modele kim çevirecek?
#        Repository mi, router mı? Karar ver.
#
#   3. AccountDetail  → AccountSummary + ranks: SeasonRank listesi
#
#   4. RankSnapshot  → LP grafiği için tek bir nokta
#        tier, division, lp, wins, losses, observed_at
#
#   5. ChampionMastery
#        champion_id, champion_name, mastery_level, mastery_points, last_play_at
#        (champion_name champions tablosundan JOIN ile gelecek)
#
# ARAŞTIR:
#   - datetime alanları JSON'a nasıl çevrilir? Pydantic bunu otomatik yapıyor
#     mu? Sonuçtaki formatın adı ne? (ISO 8601)
#   - Kazanma oranı (winrate) gibi hesaplanan bir alanı modele nasıl eklersin?
#     Pydantic "computed_field" araştır. wins+losses = 0 ise ne olmalı?
#
# CEVAP:
#   - Evet, otomatik. Pydantic datetime'ı JSON'a ISO 8601 string'i olarak
#     yazar: "2026-10-13T12:23:20.668849Z" ya da "...+03:00". TIMESTAMPTZ
#     kolonları psycopg'den saat dilimli datetime olarak geldiği için saat
#     dilimi bilgisi korunur.
#   - @computed_field + @property ile tanımlanan değer, JSON çıktısına ve
#     /docs şemasına normal bir alan gibi eklenir ama girdi olarak beklenmez:
#       @computed_field
#       @property
#       def winrate(self) -> float | None: ...
#   - wins + losses = 0 (ya da NULL) ise 0 değil None dön. 0 "hep kaybetti"
#     anlamına gelir; None "hesaplanamıyor" demektir.
#
# YASAK: riot_id_history tablosundan hiçbir alan burada OLMAYACAK.
# =============================================================================

from datetime import datetime
from pydantic import BaseModel, Field


class AccountSummary(BaseModel):
    id: int
    game_name: str
    tag_line: str
    platform_id: str | None = None
    summoner_level: int | None = None

class RankValue(BaseModel):
    tier: str | None = None
    division: str | None = None
    lp: int | None = None
    wins: int | None = None
    losses: int | None = None

class SeasonRank(BaseModel):
    account_id: int
    season_label: str
    queue_type: str
    current: RankValue
    peak: RankValue


class AccountDetail(AccountSummary):
    player_id: int


class RankHistoryEntry(BaseModel):
    tier: str | None = None
    division: str | None = None
    lp: int | None = None
    wins: int | None = None
    losses: int | None = None
    observed_at: datetime


class RankHistoryResponse(BaseModel):
    account_id: int
    season_label: str
    queue_type: str
    history: list[RankHistoryEntry] = Field(default_factory=list)