from api.routers import tournaments
from contextlib import asynccontextmanager
from api.routers import players
from fastapi import FastAPI, HTTPException
from psycopg import OperationalError
from psycopg_pool import PoolTimeout
from api.routers import accounts
from api.db import connection_pool, open_pool, close_pool
from api.routers import players, accounts, leaderboard
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from api.routers import teams
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from api.routers import leagues
from api.limiter import limiter
from api.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    open_pool()
    try:
        yield
    finally:
        close_pool()


app = FastAPI(
    title="LoL Stats API",
    version="0.1.0",
    description="LoL Stats API, player statistics and account information",
    lifespan=lifespan
)


# Shared limiter instance
app.state.limiter = limiter


# Consistent JSON response for rate limit errors
async def rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded,
):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
            }
        },
    )


app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_handler,
)

# Apply default limits to API routes
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    global_exception_handler,
)
app.include_router(players.router)
app.include_router(accounts.router)
app.include_router(leaderboard.router)
app.include_router(teams.router)
app.include_router(leagues.router)
app.include_router(tournaments.router)
@app.get("/health")
def health_check():
    try:
        with connection_pool.connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "ok"}

    except (OperationalError, PoolTimeout):
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "database": "error"}
        )
