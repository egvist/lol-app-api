from api.services.pandascore_client import PandaScoreClient


def get_team_list(
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> list[dict]:
    with PandaScoreClient() as client:
        teams = client.get_teams(
            search=search,
            page=page,
            per_page=per_page,
        )

    return [
        {
            "id": team["id"],
            "name": team["name"],
            "acronym": team.get("acronym"),
            "location": team.get("location"),
            "image_url": team.get("image_url"),
        }
        for team in teams
    ]


def get_team_detail(team_id: int) -> dict:
    with PandaScoreClient() as client:
        team = client.get_team(team_id)

    return {
        "id": team["id"],
        "name": team["name"],
        "acronym": team.get("acronym"),
        "location": team.get("location"),
        "image_url": team.get("image_url"),
        "roster": [
            {
                "id": player["id"],
                "nickname": player["name"],
                "first_name": player.get("first_name"),
                "last_name": player.get("last_name"),
                "nationality": player.get("nationality"),
                "role": player.get("role"),
                "image_url": player.get("image_url"),
                "active": player.get("active", False),
            }
            for player in team.get("players") or []
        ],
    }