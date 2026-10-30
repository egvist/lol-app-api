from api.schemas.account import SeasonRank


TIER_ORDER = {
    "IRON": 0,
    "BRONZE": 1,
    "SILVER": 2,
    "GOLD": 3,
    "PLATINUM": 4,
    "EMERALD": 5,
    "DIAMOND": 6,
    "MASTER": 7,
    "GRANDMASTER": 8,
    "CHALLENGER": 9,
}

DIVISION_ORDER = {
    "IV": 0,
    "III": 1,
    "II": 2,
    "I": 3,
}


def rank_sort_key(rank: SeasonRank) -> tuple[int, int, int]:
    current = rank.current

    tier_value = TIER_ORDER.get(current.tier or "", -1)
    division_value = DIVISION_ORDER.get(
        current.division or "", 0
    )
    lp_value = current.lp if current.lp is not None else -1

    return tier_value, division_value, lp_value


def select_best_soloq_rank(
    ranks: list[SeasonRank],
) -> SeasonRank | None:

    soloq_ranks = [
        rank
        for rank in ranks
        if rank.queue_type == "RANKED_SOLO_5x5"
        and rank.current.tier in TIER_ORDER
        and rank.current.lp is not None
    ]

    if not soloq_ranks:
        return None

    return max(soloq_ranks, key=rank_sort_key)