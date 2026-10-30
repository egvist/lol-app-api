from api.services.solo_queue_ranking import TIER_ORDER


TIER_WEIGHT = 10_000
MAX_LP = TIER_WEIGHT - 1
MIN_RANKED_PLAYERS = 3


def calculate_player_score(
    solo_queue: dict | None,
) -> int | None:

    if solo_queue is None:
        return None

    tier = solo_queue.get("tier")
    lp = solo_queue.get("lp")
    division = solo_queue.get("division")

    if tier not in TIER_ORDER:
        return None

    if not isinstance(lp, int) or isinstance(lp, bool) or lp < 0:
        return None

    tier_score = TIER_ORDER[tier] * TIER_WEIGHT

    # Master+ tier'larda division bulunmaz.
    if tier in {"MASTER", "GRANDMASTER", "CHALLENGER"}:
        return tier_score + min(lp, MAX_LP)

    division_order = {
        "IV": 0,
        "III": 1,
        "II": 2,
        "I": 3,
    }

    if division not in division_order:
        return None

    # Alt tier'larda division, LP'den daha önemli.
    division_score = division_order[division] * 2500

    return tier_score + division_score + min(lp, 2499)


def calculate_team_ranking(
    roster: list[dict],
) -> dict:

    scores = []

    for player in roster:
        score = calculate_player_score(
            player.get("solo_queue")
        )

        if score is not None:
            scores.append(score)

    ranked_count = len(scores)

    if ranked_count < MIN_RANKED_PLAYERS:
        return {
            "eligible": False,
            "ranking_score": None,
            "ranked_players": ranked_count,
            "total_players": len(roster),
        }

    average_score = sum(scores) / ranked_count

    return {
        "eligible": True,
        "ranking_score": round(average_score, 2),
        "ranked_players": ranked_count,
        "total_players": len(roster),
    }