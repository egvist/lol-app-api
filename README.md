# LoL Data API

A self-hostable **League of Legends and esports REST API** built with **FastAPI** and **PostgreSQL**. It brings together a local player database, Riot Games data, and PandaScore esports data behind one backend.

The project includes a PostgreSQL snapshot so contributors can run and explore the API locally without needing access to the original database server.

> **Project status:** Backend under active development. Some integrations require your own API credentials. This repository is designed for local development; it is not a hosted public API.

## Features

### Player data

- Browse and inspect player profiles stored in PostgreSQL.
- Access linked League of Legends accounts and rank information.
- Explore player career information and Solo Queue leaderboards.
- Synchronize Riot-derived information where supported by the configured credentials and rate limits.

### Professional esports

- Browse professional teams, including an EMEA-focused team catalog.
- Explore team rosters and Solo Queue-based team leaderboard data.
- Retrieve league, series, tournament, and match information through the PandaScore integration.
- View tournament standings and associated match results.

### Backend and development

- REST API with interactive OpenAPI/Swagger documentation.
- PostgreSQL connection pooling using `psycopg` / `psycopg_pool`.
- Health checking, CORS support, and request rate limiting.
- Docker Compose setup for the API and PostgreSQL 18.
- Automatic database restoration on the first initialization of a new PostgreSQL volume.

## Tech stack

| Layer | Technology |
| --- | --- |
| API | Python, FastAPI, Uvicorn |
| Database | PostgreSQL 18 |
| PostgreSQL client | psycopg, psycopg_pool |
| External data | Riot Games API, PandaScore API |
| Local infrastructure | Docker, Docker Compose |
| Documentation | OpenAPI / Swagger UI |

## Architecture

```text
API clients / Swagger UI
          |
          v
      FastAPI
          |
          +---- PostgreSQL (players, accounts, ranks, local data)
          |
          +---- Riot Games API (supported player/account updates)
          |
          +---- PandaScore API (esports teams, competitions, matches)
```

The PostgreSQL snapshot is a **starting dataset**, not a live shared database. Each person running the project gets their own copy and can modify it independently.

## Getting started (Docker — recommended)

### Requirements

- Git
- Docker Engine and Docker Compose (or Docker Desktop)
- Optional: Riot Games and PandaScore API credentials for endpoints that use those services

### 1. Clone the repository

```bash
git clone https://github.com/egvist/lol-app-api.git
cd lol-app-api
```

### 2. Configure the environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```dotenv
PGHOST=localhost
PGPORT=5432
PGDATABASE=lol-data
PGUSER=postgres
PGPASSWORD=replace_with_your_local_password

RIOT_API_KEY=
PANDASCORE_TOKEN=
```

- **Set `PGPASSWORD`** to a password of your choice. Docker Compose uses it for both the PostgreSQL service and the API's database connection.
- **Leave `PGHOST=localhost` in this file** for non-Docker local use. The Compose configuration overrides the API container's host to `db`, using Docker's internal network.
- Add valid Riot Games / PandaScore credentials if you want to use routes that depend on those providers. Without credentials, database-only endpoints can still be used; provider-backed endpoints may fail or return limited data.
- **Never commit `backend/.env` or real API keys.**

### 3. Start the services

```bash
docker compose --env-file backend/.env up -d --build
```

On first startup with an **empty PostgreSQL volume**, the PostgreSQL container creates the `lol-data` database and runs `database/init-db.sh` to restore `database/lol-data.dump`. The API container starts after PostgreSQL passes its health check.

Check the services:

```bash
docker compose --env-file backend/.env ps
```

### 4. Explore the API

- **Swagger UI:** http://127.0.0.1:8000/docs
- **OpenAPI schema:** http://127.0.0.1:8000/openapi.json
- **Health check:** http://127.0.0.1:8000/health

Try:

```bash
curl http://127.0.0.1:8000/health
```

A healthy database connection should produce a successful health status.

### 5. Stop the services

```bash
docker compose --env-file backend/.env down
```

This leaves the named PostgreSQL volume intact, so your changes persist between runs. **Do not use `down -v` unless you intentionally want to delete the local database volume.**

## API overview

The routes below highlight the backend's main areas. For the complete, current set of paths, parameters, and response schemas, consult **`/docs`** when the API is running.

| Area | Examples / capabilities |
| --- | --- |
| Health | `GET /health` |
| Players | Player listing, player profiles, linked accounts and ranks |
| Leaderboards | Player Solo Queue leaderboard and initial team leaderboard |
| Teams | Team catalog, rosters, Solo Queue information, team matches |
| Leagues | Leagues, series, tournaments, and league matches |
| Tournaments | `GET /tournaments/{id}`, `GET /tournaments/{id}/standings`, `GET /tournaments/{id}/matches` |
| Series | `GET /series/{id}/tournaments` |
| Matches | Match details and competition-related match lists |

Other implemented routes include `GET /leagues/{id}/matches` and `GET /teams/{id}/matches`, with supported status filters. Some API behavior and route availability may evolve while the project is under development.

## Repository layout

```text
.
├── backend/             # FastAPI source, configuration, dependencies
│   ├── .env.example     # Example local settings (safe to commit)
│   └── .env             # Your local secrets (do not commit)
├── database/
│   ├── lol-data.dump    # PostgreSQL snapshot
│   └── init-db.sh       # First-time database restore
├── compose.yaml         # API + PostgreSQL services
├── Dockerfile           # API container image
└── README.md
```

Source files and subdirectories inside `backend/` may evolve as new routes and services are added.

## Database snapshot

The included snapshot contains the project's starting player and related database records (approximately **5,900 player pages** in the original dataset). The snapshot is static:

- Changes you make locally do **not** affect the original author's database or other users.
- Changes to the upstream dataset do **not** automatically update your local copy.
- On subsequent container starts, PostgreSQL reuses the existing named volume rather than importing the snapshot again.

### Inspect the imported tables

```bash
docker compose --env-file backend/.env exec db \
  psql -U postgres -d lol-data -c '\dt'
```

### Restore a snapshot manually (advanced)

Normally you do **not** need to restore the dump by hand. If restoring into a separate, **empty** PostgreSQL database:

```bash
pg_restore -U postgres -d your_empty_database \
  --no-owner --no-acl --exit-on-error \
  database/lol-data.dump
```

The command assumes PostgreSQL client tools are installed and can connect to the target database. Do not restore into an already-populated database unless you know how to handle conflicting objects.

## Troubleshooting

**The API returns `503` or reports database `degraded`.**

Check that PostgreSQL is healthy:

```bash
docker compose --env-file backend/.env ps
```

Inspect API or database logs:

```bash
docker compose --env-file backend/.env logs --tail=100 api
docker compose --env-file backend/.env logs --tail=100 db
```

**Database password authentication fails.**

`PGPASSWORD` in `backend/.env` must match the password of the PostgreSQL user in the existing database volume. Changing the value in `.env` **does not reset the password of a database already initialized**.

**`localhost:5432` fails from inside the API container.**

In Docker, `localhost` refers to the API container itself. Compose must supply `PGHOST=db` to the API container; the database service listens internally on port `5432`. The host-side database mapping (if enabled) uses `127.0.0.1:5433`.

**The snapshot does not import again after editing it.**

Initialization scripts run only when PostgreSQL creates a fresh data directory. Existing named volumes preserve previously imported data.

**An external-provider endpoint fails.**

Check the corresponding API token, access tier, upstream availability, and rate limits. A working local database does not guarantee access to Riot Games or PandaScore services.

## Data sources and usage

This project integrates information from Riot Games and PandaScore. Riot Games and PandaScore are third-party services and are not affiliated with this repository.

**Before distributing a database snapshot or republishing third-party data, verify that your data sources and API plans permit redistribution.** If any data cannot be redistributed, exclude it from the public dump and use permitted sample data instead. Users must comply with the relevant providers' terms, attribution requirements, and rate limits.

## Development status

The backend currently covers player/account/rank data, player career information, Solo Queue and team-oriented leaderboard features, team data, and core leagues/series/tournaments/matches integration. Additional UI features, filtering, pagination, and polish are under development and should not be assumed complete.

---

Built as a practical project for learning and developing database-backed APIs, integrations, and self-hosted services.
