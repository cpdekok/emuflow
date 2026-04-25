"""
Pytest fixtures: in-process FastAPI client backed by SQLite in-memory DB.

We override ``DATABASE_URL`` *before* importing ``main`` so the module-level
engine in ``database`` picks up the test DSN. A shared async-aware
``StaticPool`` keeps the in-memory DB alive across connections.
"""
from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

# Ensure the SQLite-aiosqlite URL is in place before any backend import.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

# Make ``backend/`` importable when running pytest from anywhere.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import database  # noqa: E402
import models  # noqa: F401, E402
from main import app  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Yield a fresh AsyncClient with a clean in-memory SQLite DB.

    A ``StaticPool`` engine is required so all sessions share the same
    in-memory database across connections.
    """
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_sessionmaker = async_sessionmaker(
        bind=test_engine, expire_on_commit=False
    )

    # Patch the module-level engine + sessionmaker for the duration of the test.
    database.engine = test_engine
    database.SessionLocal = test_sessionmaker

    async with test_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)

    # Reset rate-limiter state between tests so quota does not leak.
    from api.routers.devices import limiter

    limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with test_engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.drop_all)
    await test_engine.dispose()
