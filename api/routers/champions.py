# =============================================================================
# routers/champions.py — /champions endpoint'leri (Adım 9)
# =============================================================================
#
# HAZIRLIK: APIRouter(prefix="/champions", tags=["champions"])
#
# ENDPOINT 1: GET /champions
#   Cevap: Champion listesi
#
# ENDPOINT 2: GET /champions/{champion_id}
#   Cevap: Champion, yoksa 404
#
# ENDPOINT 3: GET /champions/{champion_id}/top-pros?queue_id=420&min_games=5&limit=20
#   Cevap: ChampionProStats listesi
#   GÖREV: Önce şampiyonun var olduğunu kontrol et (404), sonra istatistikleri al.
#
# ARAŞTIR:
#   - Bazı kullanıcılar şampiyonu ID ile değil adıyla arar ("Ahri").
#     /champions/{champion_id} ile /champions/by-name/{name} ayrı mı olmalı,
#     yoksa tek endpoint iki şeyi de mi kabul etmeli? İkisinin artısı/eksisi ne?
#
# CEVAP: Ayrı tutmak daha iyi. Tek endpoint (/champions/{id_or_name}) kısa
#   görünür ama parametrenin tipi str olmak zorunda kalır, "266"nın sayı mı
#   ad mı olduğunu kodla tahmin edersin; FastAPI'nin int doğrulaması ve
#   /docs'taki açık tip kaybolur. Ayrı endpoint'lerde her biri tek iş yapar.
#   Daha REST'e uygun bir alternatif: adı liste endpoint'inde filtre yapmak,
#   GET /champions?name=ahri. ID kaynağın kimliği, ad ise bir arama kriteri.
# =============================================================================
