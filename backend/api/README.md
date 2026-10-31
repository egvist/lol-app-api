# API architecture

For setup, running and the endpoint list, see the root [README](../../README.md).

## Layers

```text
HTTP request → routers/ → services/ or repositories/ → PostgreSQL / PandaScore / local JSON
                  ↓
              schemas/ (Pydantic) → JSON response
```

| Folder | Responsibility |
|---|---|
| `main.py` | App setup, routers, CORS, rate limiting, exception handlers, `/health` |
| `config.py`, `db.py` | `.env` settings and the `psycopg_pool` connection pool |
| `routers/` | Parameter validation and HTTP errors; no SQL |
| `repositories/` | PostgreSQL queries (players, accounts, leaderboard) |
| `services/` | PandaScore client, player/team matching, team ranking, catalog loading, background rank refresh |
| `schemas/` | Response models: the shape of the JSON the API returns |
| `tests/` | pytest + `TestClient`; the database and PandaScore are mocked |

## Data sources

- **PostgreSQL:** players, Riot accounts, ranks, rank history, leaderboard.
- **Local JSON (`backend/data/`):** the league catalog (`pandascore_lol_leagues.json`) and the EMEA team catalog (`emea_teams_{season}.json`). If a file is missing, the related endpoints return 503 or 404.
- **PandaScore:** teams, rosters, series, tournaments, standings, matches, pro profiles and careers.

Local players are matched to PandaScore players by nickname, country and role (`services/player_matching.py`, `services/team_player_matching.py`). When no match is found, the response has `status: "not_matched"`.

## Caching and limits

| What | How |
|---|---|
| PandaScore requests | 1-hour `TTLCache`; limited to 50 requests per minute and 900 per hour (`services/pandascore_limiter.py`). After a PandaScore 429, no new requests are sent until `Retry-After` has passed. |
| Team leaderboard | Built on the first request from teams in currently running series and cached for 1 hour. The first request can take 10–20 seconds. |
| Pro profile and career | Cached for 1 hour (tournament matches for 6 hours) |
| Whole API | 200 requests per minute per IP (`slowapi`) |

Match lists (`/leagues/{id}/matches`, `/teams/{id}/matches`) fetch every PandaScore page for the requested status. That makes `status=finished` the most expensive request; after the first call it is served from the cache.

## Team Solo Queue ranking

`services/team_ranking.py` turns each roster member's best Solo Queue rank into a score (`tier × 10000 + LP`; below Master the division is also taken into account). The team score is the average of those scores, and a team needs at least 3 ranked players to be ranked. This is not an official ranking.

## Error format

All errors have the same shape:

```json
{ "error": { "code": "NOT_FOUND", "message": "Player not found" } }
```

| Code | When |
|---|---|
| 404 `NOT_FOUND` | Record does not exist |
| 422 `VALIDATION_ERROR` | Invalid parameter; the `details` field says which one |
| 429 `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| 503 `HTTP_ERROR` | PandaScore, a local catalog or the active season is unavailable |
| 500 `INTERNAL_ERROR` | Unexpected error (written to the server log) |

## CORS

`main.py` only allows local development origins (`localhost:5173`, `127.0.0.1:5173`, `localhost:3000`) and only `GET` requests. Add other origins to `allow_origins` if the API is called from elsewhere.
