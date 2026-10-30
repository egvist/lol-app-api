from api.schemas.account import RankValue, SeasonRank
from api.services.solo_queue_ranking import select_best_soloq_rank


def make_rank(
    account_id: int,
    queue_type: str,
    tier: str | None,
    division: str | None,
    lp: int | None,
) -> SeasonRank:
    return SeasonRank(
        account_id=account_id,
        season_label="2026",
        queue_type=queue_type,
        current=RankValue(
            tier=tier,
            division=division,
            lp=lp,
        ),
        peak=RankValue(),
    )


def test_select_best_soloq_rank():
    ranks = [
        make_rank(1, "RANKED_SOLO_5x5", "MASTER", None, 500),
        make_rank(2, "RANKED_SOLO_5x5", "GRANDMASTER", None, 200),
        make_rank(3, "RANKED_SOLO_5x5", "CHALLENGER", None, 100),
    ]

    result = select_best_soloq_rank(ranks)

    assert result is not None
    assert result.account_id == 3


def test_ignore_flex_rank():
    ranks = [
        make_rank(1, "RANKED_FLEX_SR", "CHALLENGER", None, 1000),
        make_rank(2, "RANKED_SOLO_5x5", "DIAMOND", "I", 80),
    ]

    result = select_best_soloq_rank(ranks)

    assert result is not None
    assert result.account_id == 2


def test_no_valid_soloq_rank():
    ranks = [
        make_rank(1, "RANKED_FLEX_SR", "MASTER", None, 200),
        make_rank(2, "RANKED_SOLO_5x5", None, None, None),
    ]

    assert select_best_soloq_rank(ranks) is None


def test_same_tier_higher_lp():
    ranks = [
        make_rank(1, "RANKED_SOLO_5x5", "MASTER", None, 250),
        make_rank(2, "RANKED_SOLO_5x5", "MASTER", None, 650),
    ]

    result = select_best_soloq_rank(ranks)

    assert result is not None
    assert result.account_id == 2