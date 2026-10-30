def calculate_team_soloq_summary(
    roster: list[dict],
) -> dict:

    ranked = [
        player["solo_queue"]
        for player in roster
        if player.get("solo_queue") is not None
        and player["solo_queue"].get("lp") is not None
        and player["solo_queue"].get("tier") is not None
    ]

    average_lp = (
        sum(rank["lp"] for rank in ranked) / len(ranked)
        if ranked else None
    )

    return {
        "total_players": len(roster),
        "ranked_players": len(ranked),
        "average_lp": (
            round(average_lp, 2)
            if average_lp is not None
            else None
        ),
        "challenger_count": sum(
            rank["tier"] == "CHALLENGER"
            for rank in ranked
        ),
        "grandmaster_count": sum(
            rank["tier"] == "GRANDMASTER"
            for rank in ranked
        ),
        "master_count": sum(
            rank["tier"] == "MASTER"
            for rank in ranked
        ),
    }