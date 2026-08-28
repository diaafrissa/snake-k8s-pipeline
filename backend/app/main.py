"""
Snake Game API
--------------
FastAPI backend for the Phosphor Snake game.
Handles score submission and leaderboard retrieval using Redis
as the storage engine (sorted set = perfect fit for a leaderboard).
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import List

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration (all overridable via environment variables -> maps 1:1 to
# ConfigMap/Secret values later in Kubernetes)
# ---------------------------------------------------------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
LEADERBOARD_KEY = os.getenv("LEADERBOARD_KEY", "snake:leaderboard")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
MAX_LEADERBOARD_SIZE = int(os.getenv("MAX_LEADERBOARD_SIZE", "100"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("snake-api")

redis_client: redis.Redis | None = None


# ---------------------------------------------------------------------------
# Lifespan: open/close the Redis connection pool with the app's lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )
    try:
        await redis_client.ping()
        logger.info("Connected to Redis at %s:%s", REDIS_HOST, REDIS_PORT)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis not reachable at startup: %s", exc)

    yield

    await redis_client.aclose()
    logger.info("Redis connection closed")


app = FastAPI(
    title="Snake Game API",
    description="Score & leaderboard service for the Phosphor Snake arcade game",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ScoreSubmission(BaseModel):
    player: str = Field(..., min_length=1, max_length=20, description="Player name / handle")
    score: int = Field(..., ge=0, le=1_000_000, description="Final score for the run")


class LeaderboardEntry(BaseModel):
    rank: int
    player: str
    score: int


class HealthResponse(BaseModel):
    status: str
    redis: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse, tags=["ops"])
async def health_check():
    """
    Liveness/readiness endpoint for Kubernetes probes.
    Returns 200 even if Redis is briefly unreachable so the pod isn't
    killed on a transient blip, but reports Redis status in the body.
    """
    redis_status = "up"
    try:
        await redis_client.ping()
    except Exception:  # noqa: BLE001
        redis_status = "down"

    return HealthResponse(status="ok", redis=redis_status)


@app.get("/api/ready", tags=["ops"])
async def readiness_check():
    """
    Strict readiness check: fails (503) if Redis is not reachable.
    Use this one for K8s readinessProbe so traffic isn't routed to a pod
    that can't actually serve leaderboard requests.
    """
    try:
        await redis_client.ping()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis unavailable: {exc}",
        ) from exc
    return {"status": "ready"}


@app.post("/api/score", status_code=status.HTTP_201_CREATED, tags=["game"])
async def submit_score(submission: ScoreSubmission):
    """
    Submit a score for a player. Only the player's *best* score is kept
    on the leaderboard (a new lower score won't overwrite a higher one).
    """
    player = submission.player.strip()
    if not player:
        raise HTTPException(status_code=422, detail="Player name cannot be empty")

    try:
        current = await redis_client.zscore(LEADERBOARD_KEY, player)
        if current is None or submission.score > current:
            await redis_client.zadd(LEADERBOARD_KEY, {player: submission.score})

        # keep the sorted set bounded so it can't grow forever
        await redis_client.zremrangebyrank(LEADERBOARD_KEY, 0, -MAX_LEADERBOARD_SIZE - 1)
    except redis.RedisError as exc:
        logger.error("Redis error while submitting score: %s", exc)
        raise HTTPException(status_code=503, detail="Storage unavailable, try again shortly") from exc

    best = await redis_client.zscore(LEADERBOARD_KEY, player)
    return {"player": player, "submitted_score": submission.score, "best_score": int(best)}


@app.get("/api/leaderboard", response_model=List[LeaderboardEntry], tags=["game"])
async def get_leaderboard(limit: int = 10):
    """
    Return the top N players ordered by score, descending.
    """
    limit = max(1, min(limit, MAX_LEADERBOARD_SIZE))

    try:
        raw = await redis_client.zrevrange(LEADERBOARD_KEY, 0, limit - 1, withscores=True)
    except redis.RedisError as exc:
        logger.error("Redis error while fetching leaderboard: %s", exc)
        raise HTTPException(status_code=503, detail="Storage unavailable, try again shortly") from exc

    return [
        LeaderboardEntry(rank=i + 1, player=player, score=int(score))
        for i, (player, score) in enumerate(raw)
    ]


@app.get("/", tags=["ops"])
async def root():
    return {"service": "snake-game-api", "docs": "/docs"}
