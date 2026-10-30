import httpx
from copy import deepcopy
from threading import RLock
from api.services.pandascore_limiter import pandascore_limiter
from cachetools import TTLCache
from api.config import settings
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from api.services.pandascore_limiter import pandascore_limiter

pandascore_cache = TTLCache(
    maxsize=2000,
    ttl=3600,
)

cache_lock = RLock()

class PandaScoreError(Exception):
    """PandaScore API request failed."""


class PandaScoreClient:
    BASE_URL = "https://api.pandascore.co"

    def __init__(self):
        if not settings.pandascore_token:
            raise ValueError("PANDASCORE_TOKEN is missing")

        self.client = httpx.Client(
            base_url = self.BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.pandascore_token}",
                "Accept": "application/json",
            },
            timeout=15.0
        )

    def get(self, path: str, params: dict | None = None):
        cache_key = (
            path,
            tuple(sorted((params or {}).items())),
        )

        with cache_lock:
            cached_data = pandascore_cache.get(cache_key)
        
        if cached_data is not None:
            return deepcopy(cached_data)
        
        pandascore_limiter.acquire()

        try:
            response = self.client.get(path, params=params)
            response.raise_for_status()

            data = response.json()

            with cache_lock:
                pandascore_cache[cache_key] = deepcopy(data)

            return data

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            if status == 429:
                retry_after = parse_retry_after(
                    exc.response.headers.get("Retry-After")
                )

                pandascore_limiter.set_cooldown(retry_after)

                raise PandaScoreError(
                    f"PandaScore rate limit exceeded. "
                    f"Retry after {retry_after:.0f} seconds."
                ) from exc

            raise PandaScoreError(
                f"PandaScore returned HTTP {status}"
            ) from exc

        except httpx.RequestError as exc:
            raise PandaScoreError(
                "Could not connect to PandaScore"
            ) from exc

    def get_players(self, page: int = 1, per_page: int = 20):
        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError("Invalid pagination parameters")
        return self.get(
            "/lol/players",
            params={
                "page": page,
                "per_page": per_page,
            },
        )

    def close(self):
        self.client.close()


    def search_players(self, name:str, page:int = 1):
        name = name.strip()

        if not name:
            raise ValueError("Player name cannot be empty")

        return self.get(
            "/lol/players",
            params={
                "search[name]": name,
                "page": page,
                "per_page": 100,
            },

        )

    def get_player_candidates(self, name: str):
        searches = [
            name.strip(),
            name.replace(" ", "").strip(),
        ]

        candidates = {}

        for search in dict.fromkeys(searches):
            if not search:
                continue

            players = self.search_players(search)

            for player in players:
                candidates[player["id"]] = player

        return list(candidates.values())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def get_player_tournaments(self, player_id: int, page: int = 1, per_page: int = 50,):
        if player_id < 1:
            raise ValueError("Invalid player ID")

        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError("Invalid pagination parameters")

        return self.get(
            f"/players/{player_id}/tournaments",
            params={
                "page": page,
                "per_page": per_page,
            },
        )


    def get_all_player_tournaments(
        self,
        player_id: int,
    ) -> list[dict]:

        all_tournaments = []
        page = 1
        per_page = 100

        while True:
            tournaments = self.get_player_tournaments(
                player_id=player_id,
                page=page,
                per_page=per_page,
            )

            all_tournaments.extend(tournaments)

            if len(tournaments) < per_page:
                break

            page += 1

        return all_tournaments

    def get_tournament_matches(self, tournament_id: int, page: int = 1, per_page: int = 100,):
        if tournament_id < 1:
            raise ValueError("Invalid tournament ID")

        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError("Invalid pagination parameters")

        return self.get(f"/tournaments/{tournament_id}/matches", params={"page": page, "per_page":per_page},)


    def get_tournament_standings(
    self,
    tournament_id: int,
    page: int = 1,
    per_page: int = 100,):
        if tournament_id < 1:
            raise ValueError("Invalid tournament ID")

        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError("Invalid pagination parameters")

        return self.get(
            f"/tournaments/{tournament_id}/standings",
            params={
                "page": page,
                "per_page": per_page,
            },
        )
    def get_teams(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
    ):
        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError("Invalid pagination parameters")

        params = {
            "page": page,
            "per_page": per_page,
        }

        if search and search.strip():
            params["search[name]"] = search.strip()

        return self.get(
            "/lol/teams",
            params=params,
        )


    def get_team(self, team_id: int):
        if team_id < 1:
            raise ValueError("Invalid team ID")

        return self.get(f"/teams/{team_id}")

        
    def get_running_lol_series(
        self,
        page: int = 1,
        per_page: int = 20,
    ):
        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError("Invalid pagination parameters")

        return self.get(
            "/lol/series/running",
            params={
                "page": page,
                "per_page": per_page,
            },
        )


    def get_series_teams(
        self,
        series_id: int,
        page: int = 1,
        per_page: int = 100,
    ):
        if series_id < 1:
            raise ValueError("Invalid series ID")

        if page < 1 or not 1 <= per_page <= 100:
            raise ValueError("Invalid pagination parameters")

        return self.get(
            f"/lol/series/{series_id}/teams",
            params={
                "page": page,
                "per_page": per_page,
            },
        )
    def get_lol_leagues(
    self,
    page: int = 1,
    per_page: int = 100,
    ):
        return self.get(
            "/lol/leagues",
            params={
                "page": page,
                "per_page": per_page,
            },
        )
    
    def get_league_series(
    self,
    league_id: int,
    page: int = 1,
    per_page: int = 100,
    ):
        if league_id < 1 or page < 1:
            raise ValueError("Invalid league ID or page")

        if not 1 <= per_page <= 100:
            raise ValueError("Invalid per_page")

        return self.get(
            f"/leagues/{league_id}/series",
            params={
                "page": page,
                "per_page": per_page,
                "sort": "-begin_at",
            },
        )
    
    def get_series_tournaments(
        self,
        series_id: int,
        page: int = 1,
        per_page: int = 100,
    ):
        if series_id < 1 or page < 1:
            raise ValueError("Invalid series ID or page")

        if not 1 <= per_page <= 100:
            raise ValueError("Invalid per_page")

        return self.get(
            f"/series/{series_id}/tournaments",
            params={
                "page": page,
                "per_page": per_page,
            },
        )
    
    def get_league_matches(
        self,
        league_id: int,
        page: int = 1,
        per_page: int = 100,
        status: str | None = None,
    ):
        if league_id < 1 or page < 1:
            raise ValueError("Invalid league ID or page")

        if not 1 <= per_page <= 100:
            raise ValueError("Invalid per_page")

        params = {"page": page, "per_page": per_page}

        if status is not None:
            params["filter[status]"] = status

        return self.get(
            f"/leagues/{league_id}/matches",
            params=params,
        )


    def get_team_matches(
        self,
        team_id: int,
        page: int = 1,
        per_page: int = 100,
        status: str | None = None,
    ):
        if team_id < 1 or page < 1:
            raise ValueError("Invalid team ID or page")

        if not 1 <= per_page <= 100:
            raise ValueError("Invalid per_page")

        params = {"page": page, "per_page": per_page}

        if status is not None:
            params["filter[status]"] = status

        return self.get(
            f"/teams/{team_id}/matches",
            params=params,
        )

    def get_tournament(self, tournament_id: int):
        if tournament_id < 1:
            raise ValueError("Invalid tournament ID")

        return self.get(
            f"/tournaments/{tournament_id}"
        )
def parse_retry_after(value: str | None) -> float:
    if not value:
        return 60.0

    value = value.strip()

    if value.isdecimal():
        return float(value)

    try:
        retry_date = parsedate_to_datetime(value)

        if retry_date.tzinfo is None:
            retry_date = retry_date.replace(tzinfo=timezone.utc)

        return max(
            0.0,
            (retry_date - datetime.now(timezone.utc)).total_seconds(),
        )
    except (TypeError, ValueError, OverflowError):
        return 60.0
