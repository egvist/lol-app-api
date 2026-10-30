def analyze_team_coverage(teams: list[dict]) -> dict:
    complete = 0
    partial = 0
    insufficient = 0

    total_players = 0
    ranked_players = 0
    eligible_teams = 0

    details = []

    for team in teams:
        summary = team["summary"]
        ranking = team["ranking"]

        total = summary["total_players"]
        ranked = summary["ranked_players"]

        total_players += total
        ranked_players += ranked

        if total > 0 and ranked == total:
            status = "complete"
            complete += 1
        elif ranking["eligible"]:
            status = "partial"
            partial += 1
        else:
            status = "insufficient"
            insufficient += 1

        if ranking["eligible"]:
            eligible_teams += 1

        details.append({
            "team_id": team["team_id"],
            "team_name": team["team_name"],
            "status": status,
            "eligible": ranking["eligible"],
            "ranked_players": ranked,
            "total_players": total,
            "coverage_percent": (
                round(ranked / total * 100, 2)
                if total else 0
            ),
        })

    return {
        "total_teams": len(teams),
        "eligible_teams": eligible_teams,
        "complete_teams": complete,
        "partial_teams": partial,
        "insufficient_teams": insufficient,
        "total_players": total_players,
        "ranked_players": ranked_players,
        "overall_coverage_percent": (
            round(ranked_players / total_players * 100, 2)
            if total_players else 0
        ),
        "teams": details,
    }