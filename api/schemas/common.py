# =============================================================================
# schemas/common.py — Birden fazla yerde kullanılan modeller (Adım 4)
# =============================================================================
#
# -----------------------------------------------------------------------------
# 1) Sayfalama (pagination) cevabı
# -----------------------------------------------------------------------------
# 5900+ oyuncu var. /players hepsini tek seferde döndürmemeli.
#
# GÖREV: Liste döndüren her endpoint için ortak bir cevap modeli yaz.
#   Alanlar:
#     - items: o sayfadaki kayıtların listesi
#     - total: filtreye uyan toplam kayıt sayısı
#     - limit: bu sayfada istenen kayıt sayısı
#     - offset: kaçıncı kayıttan başlandığı
#
# ARAŞTIR:
#   - Python "Generic" tipler ve Pydantic'te generic model: Page[PlayerSummary],
#     Page[MatchSummary] gibi tek bir sınıfı farklı tiplerle kullanmak.
#     (Pydantic docs: "Generic models")
#   - "offset pagination" ile "cursor/keyset pagination" farkı. Offset büyük
#     sayılarda neden yavaşlar? Bu proje için offset yeterli, ama farkı bil.
#
# -----------------------------------------------------------------------------
# 2) Sabit değerler için Enum'lar
# -----------------------------------------------------------------------------
# Şemada CHECK constraint'lerle sınırlanmış kolonlar var (sql/schema.sql):
#   - players.main_role: TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY
#   - account_season_ranks.queue_type: RANKED_SOLO_5x5, RANKED_FLEX_SR
#   - ranked_seasons.status: UPCOMING, ACTIVE, FINISHED
#
# GÖREV: Bunların her biri için `str` ve `Enum`'dan türeyen bir sınıf yaz
#   (Role, QueueType, SeasonStatus).
#
# ARAŞTIR: Bir query parametresinin tipini Enum yaparsan FastAPI ne yapar?
#   /players?role=ADC isteği atınca hangi durum kodu dönüyor? (Cevap: dene ve gör.)
#
# -----------------------------------------------------------------------------
# 3) Hata cevabı (isteğe bağlı)
# -----------------------------------------------------------------------------
# GÖREV: {"detail": "..."} şeklinde bir ErrorResponse modeli yaz. Router'larda
#   `responses={404: {"model": ErrorResponse}}` olarak verirsen /docs sayfasında
#   olası hatalar da görünür.
# =============================================================================
