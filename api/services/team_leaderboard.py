from api.repositories import players as player_repo
from api.services.player_matching import normalize_name
from api.services.team_player_matching import match_roster_player
from api.services.team_service import get_team_detail
from api.services.solo_queue_ranking import select_best_soloq_rank
from api.services.team_soloq_summary import (
    calculate_team_soloq_summary,
)
from api.services.team_ranking import calculate_team_ranking
from threading import Lock

from api.services.pandascore_client import PandaScoreClient
from api.services.team_discovery import discover_running_teams
from api.services.team_leaderboard_cache import (
    get_cached_leaderboard,
    set_cached_leaderboard,
)

_leaderboard_build_lock = Lock()
def get_team_soloq_roster(
    conn,
    team_id: int,
    season: int,
) -> list[dict]:

    team = get_team_detail(team_id)
    roster = team["roster"]

    normalized_names = [
        normalize_name(player["nickname"])
        for player in roster
    ]

    local_players = player_repo.find_players_by_names(
        conn,
        normalized_names,
    )

    result = []

    for pro_player in roster:
        matched = match_roster_player(
            pro_player,
            local_players,
        )

        player_data = {
            "pro_player_id": pro_player["id"],
            "nickname": pro_player["nickname"],
            "role": pro_player.get("role"),
            "image_url": pro_player.get("image_url"),
            "local_player_id": matched["id"] if matched else None,
            "solo_queue": None,
        }

        if matched:
            ranks = player_repo.get_player_ranks(
                conn,
                matched["id"],
                season,
            )

            best = select_best_soloq_rank(ranks)

            if best is not None:
                player_data["solo_queue"] = {
                    "account_id": best.account_id,
                    "tier": best.current.tier,
                    "division": best.current.division,
                    "lp": best.current.lp,
                    "wins": best.current.wins,
                    "losses": best.current.losses,
                }

        result.append(player_data)

    return result


def get_team_soloq(
    conn,
    team_id: int,
    season: int,
) -> dict:

    team = get_team_detail(team_id)

    roster = get_team_soloq_roster(
        conn=conn,
        team_id=team_id,
        season=season,
    )

    summary = calculate_team_soloq_summary(roster)

    return {
        "team_id": team["id"],
        "team_name": team["name"],
        "team_image_url": team.get("image_url"),
        "season": season,
        "summary": summary,
        "roster": roster,
    }

INITIAL_TEAM_IDS = [88, 134078, 126536]


def build_team_leaderboard(
    teams: list[dict],
) -> list[dict]:
    for team in teams:
        ranking = calculate_team_ranking(team["roster"])
        team["ranking"] = ranking

    teams.sort(
        key=lambda team: (
            team["ranking"]["eligible"],
            team["ranking"]["ranking_score"] or 0,
            team["ranking"]["ranked_players"],
        ),
        reverse=True,
    )

    position = 0

    for team in teams:
        if team["ranking"]["eligible"]:
            position += 1
            team["position"] = position
        else:
            team["position"] = None

    return teams


def get_teams_leaderboard(
    conn,
    season: int,
    limit: int = 10,
    offset: int = 0,
) -> dict:

    ranked_teams = get_cached_leaderboard(season)

    if ranked_teams is None:
        with _leaderboard_build_lock:
            # Başka bir request cache'i doldurmuş olabilir.
            ranked_teams = get_cached_leaderboard(season)

            if ranked_teams is None:
                with PandaScoreClient() as client:
                    discovered_teams = discover_running_teams(
                        client,
                        max_series=20,
                    )

                teams = []

                for team in discovered_teams:
                    team_data = get_team_soloq(
                        conn=conn,
                        team_id=team["id"],
                        season=season,
                    )
                    teams.append(team_data)

                ranked_teams = build_team_leaderboard(teams)

                set_cached_leaderboard(
                    season,
                    ranked_teams,
                )

    return {
        "season": season,
        "total": len(ranked_teams),
        "limit": limit,
        "offset": offset,
        "items": ranked_teams[offset:offset + limit],
    }