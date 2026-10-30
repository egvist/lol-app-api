from api.services.pandascore_client import PandaScoreClient, PandaScoreError
from api.services.player_matching import match_player
from threading import RLock
from cachetools import TTLCache, cached

def get_pro_profile(local_player: dict) -> dict:
    try:
        return _fetch_pro_profile(
            player_id=local_player["id"],
            nickname=local_player["nickname"],
            country_code=local_player.get("country_code"),
            main_role=local_player.get("main_role"),
        )

    except PandaScoreError:
        return {
            "player_id": local_player["id"],
            "nickname": local_player["nickname"],
            "status": "unavailable",
            "pro_player": None,
        }


profile_cache = TTLCache(maxsize=1000, ttl=3600)
cache_lock = RLock()

@cached(cache=profile_cache, lock=cache_lock)
def _fetch_pro_profile(
    player_id: int,
    nickname: str,
    country_code: str | None,
    main_role: str | None,
) -> dict:
    local_player = {
        "id": player_id,
        "nickname": nickname,
        "country_code": country_code,
        "main_role": main_role,
    }

    with PandaScoreClient() as client:
        candidates = client.get_player_candidates(nickname)

        matched = match_player(local_player, candidates)

        if matched is None:
            return {
                "player_id": player_id,
                "nickname": nickname,
                "status": "not_matched",
                "pro_player": None,
            }

        return {
            "player_id": player_id,
            "nickname": nickname,
            "status": "matched",
            "pro_player": {
                "id": matched["id"],
                "nickname": matched["name"],
                "first_name": matched.get("first_name"),
                "last_name": matched.get("last_name"),
                "role": matched.get("role"),
                "image_url": matched.get("image_url"),
                "current_team": matched.get("current_team"),
            },
        }

    