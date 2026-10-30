from api.services.player_matching import normalize_name


def match_roster_player(
    pro_player: dict,
    local_players: list[dict],
) -> dict | None:

    pro_name = normalize_name(pro_player["nickname"])

    candidates = [
        player
        for player in local_players
        if normalize_name(player["nickname"]) == pro_name
    ]

    if not candidates:
        return None

    nationality = pro_player.get("nationality")

    if nationality:
        country_matches = [
            player
            for player in candidates
            if player.get("country_code") == nationality
        ]

        if country_matches:
            candidates = country_matches

    if len(candidates) != 1:
        return None

    return candidates[0]