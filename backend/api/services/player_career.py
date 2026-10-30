from api.services.pandascore_client import PandaScoreClient,PandaScoreError
from api.services.player_matching import match_player
from threading import Condition
from cachetools import TTLCache, cached
from datetime import datetime, timezone
career_cache = TTLCache(maxsize=1000, ttl=3600)
matches_cache = TTLCache(maxsize=2000, ttl=21600)

career_condition = Condition()
matches_condition = Condition()


def extract_career_entry(tournament: dict, player_id: int) -> dict | None:
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
            "placement": None,
            "last_result": None,
            "team": {
                "id": team["id"],
                "name": team["name"],
                "image_url": team.get("image_url"),
            },
            "roster": [
                {
                    "id": player["id"],
                    "nickname": player["name"],
                    "role": player.get("role"),
                    "image_url": player.get("image_url"),
                }
                for player in players
            ],
        }

    return None

def build_career_history(
    tournaments: list[dict],
    player_id: int,
    client: PandaScoreClient
) -> list[dict]:

    history = []

    for tournament in tournaments:
        entry = extract_career_entry(
            tournament=tournament,
            player_id=player_id,
        )

        if entry is None:
            continue

        team_id = entry["team"]["id"]

        matches = client.get_tournament_matches(
            tournament_id=tournament["id"],
        )

        entry["last_result"] = find_last_result(
            matches=matches,
            team_id=team_id,
        )

        history.append(entry)

    history.sort(
        key=lambda item: item["begin_at"] or "",
        reverse=True,
    )

    return history


def get_player_career(
    local_player: dict,
    limit: int = 5,
    offset: int = 0,
) -> dict:

    player_id = local_player["id"]

    try:
        career = load_career_entries(
            player_id=player_id,
            nickname=local_player["nickname"],
            country_code=local_player.get("country_code"),
            main_role=local_player.get("main_role"),
        )

    except PandaScoreError:
        return {
            "player_id": player_id,
            "status": "unavailable",
            "total": 0,
            "limit": limit,
            "offset": offset,
            "items": [],
        }

    all_entries = career["items"]
    total = len(all_entries)

    page_entries = [
        {
            **entry,
            "last_result": None,
        }
        for entry in all_entries[offset:offset + limit]
    ]

    for entry in page_entries:
        team_id = entry["team"]["id"]
        tournament_id = entry["tournament_id"]

        # Turnuva henüz bitmediyse final placement gösterme.
        end_at = entry.get("end_at")

        is_finished = False

        if end_at:
            end_date = datetime.fromisoformat(
                end_at.replace("Z", "+00:00")
            )
            is_finished = end_date <= datetime.now(timezone.utc)

        if is_finished:
            try:
                standings = load_tournament_standings(
                    tournament_id
                )

                entry["placement"] = extract_placement(
                    standings=standings,
                    team_id=team_id,
                )

            except PandaScoreError:
                entry["placement"] = None

        try:
            matches = load_tournament_matches(
                tournament_id
            )

        except PandaScoreError:
            break

        entry["last_result"] = find_last_result(
            matches=matches,
            team_id=team_id,
        )

    return {
        "player_id": player_id,
        "status": career["status"],
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": page_entries,
    }

def load_tournament_standings(tournament_id: int) -> list[dict]:
    with PandaScoreClient() as client:
        return client.get_tournament_standings(
            tournament_id=tournament_id
        )
    
def extract_placement(
    standings: list[dict],
    team_id: int,
) -> str | None:

    for entry in standings:
        team = entry.get("team") or {}

        if team.get("id") != team_id:
            continue

        rank = entry.get("rank")

        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            return None

        suffix = (
            "th"
            if 11 <= rank % 100 <= 13
            else {1: "st", 2: "nd", 3: "rd"}.get(rank % 10, "th")
        )

        return f"{rank}{suffix}"

    return None

def find_last_result(matches: list[dict], team_id: int, ) -> dict | None:
        relevant_matches = []
        for match in matches:
            if match.get("status") != "finished":
                continue

            opponents = [
                item["opponent"] 
                for item in match.get("opponents") or []
                if item.get("type") == "Team" and item.get("opponent")
            ]

            team_ids = {team["id"] for team in opponents}

            if team_id not in team_ids:
                continue
            if not match.get("end_at"):
                continue

            relevant_matches.append(match)

        if not relevant_matches:
            return None

        last_match = max(relevant_matches, key=lambda match: match["end_at"],)
        opponents = [
            item["opponent"]
            for item in last_match.get("opponents") or []
            if item.get("type") == "Team" and item.get("opponent")
        ]

        opponent = next((team for team in opponents if team["id"] != team_id), None, )



        
        scores = {
            result["team_id"]: result["score"]
            for result in last_match.get("results") or []
        }

        return {
            "match_id": last_match["id"],
            "opponent": {
                "id": opponent["id"],
                "name": opponent["name"],
                "image_url": opponent.get("image_url"),
            } if opponent else None,
            "team_score": scores.get(team_id),
            "opponent_score": (
                scores.get(opponent["id"]) if opponent else None
            ),
            "winner_id": last_match.get("winner_id"),
        }


@cached(cache=career_cache, condition=career_condition)
def load_career_entries(
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
                "status": "not_matched",
                "items": [],
            }

        tournaments = client.get_all_player_tournaments(
            matched["id"]
        )

    entries = []

    for tournament in tournaments:
        entry = extract_career_entry(
            tournament=tournament,
            player_id=matched["id"],
        )

        if entry is not None:
            entries.append(entry)

    entries.sort(
        key=lambda entry: entry["begin_at"] or "",
        reverse=True,
    )

    return {
        "status": "matched",
        "items": entries,
    }


@cached(cache=matches_cache, condition=matches_condition)
def load_tournament_matches(tournament_id: int) -> list[dict]:

    with PandaScoreClient() as client:
        matches = []
        page = 1
        per_page = 100

        while True:
            batch = client.get_tournament_matches(
                tournament_id=tournament_id,
                page=page,
                per_page=per_page,
            )

            matches.extend(batch)

            if len(batch) < per_page:
                break

            page += 1

        return matches


def prepare_career_entries(
    tournaments: list[dict],
    player_id: int,
) -> list[dict]:

    entries = []

    for tournament in tournaments:
        entry = extract_career_entry(
            tournament=tournament,
            player_id=player_id,
        )

        if entry is not None:
            entries.append(entry)

    entries.sort(
        key=lambda entry: entry["begin_at"] or "",
        reverse=True,
    )

    return entries