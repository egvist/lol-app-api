

def extract_career_entry(tournament: dict, player_id: int,) -> dict | None:
    for roster in tournament.get("expected_roster") or []:
        players = roster.get("players") or []

        found = any(player["id"] == player_id for player in players)

        if not found:
            continue

        team = roster.get("team")

        if not team:
            continue

        league = tournament.get("league") or {}

        return {
            "tournament_id": tournament["id"],
            "tournament_name": tournament["name"],
            "league_name": league.get("name"),
            "begin_at": tournament.get("begin_at"),
            "end_at": tournament.get("end_at"),
            "team": {
                "id": team["id"],
                "name": team["name"],
                "image_url": team.get("image_urk"),
            },
        }
    return None


def build_career_history(
    tournaments: list[dict],
    player_id: int,
) -> list[dict]:

    history = []

    for tournament in tournaments:
        entry = extract_career_entry(
            tournament,
            player_id,
        )

        if entry is not None:
            history.append(entry)

    history.sort(
        key=lambda item: item["begin_at"] or "",
        reverse=True,
    )

    return history