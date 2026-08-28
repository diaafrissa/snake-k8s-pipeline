"""
Shared pytest fixtures for the Snake Game API test suite.

Key idea: we monkeypatch redis.asyncio.Redis so that whenever the app's
lifespan tries to open a connection, it gets a FakeRedis instance instead.
Because a fresh FakeRedis is created every time the fixture runs, each
test gets a clean, isolated "database" automatically - no manual flushing,
no dependency on a real Redis server, and no test pollution between runs.
"""
import os
import sys

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient

# Make "app/" importable as a top-level package (main.py lives there)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import main as app_module  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    """
    Yields a TestClient wired to an isolated in-memory fake Redis.
    Use this fixture in any test that needs to call the API.
    """

    def _fake_redis_factory(*_args, **_kwargs):
        return fakeredis.aioredis.FakeRedis(decode_responses=True)

    monkeypatch.setattr(app_module.redis, "Redis", _fake_redis_factory)

    with TestClient(app_module.app) as test_client:
        yield test_client
