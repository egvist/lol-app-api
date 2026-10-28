import httpx

from api.config import settings

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

    def get(self, path:str, params:dict | None = None):
        try:
            response = self.client.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response_code
            raise PandaScoreError(f"PandaScore returned HTTP {status}") from exc
        except httpx.RequestError as exc:
            raise PandaScoreError("Could not connect to PandaScore") from exc

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