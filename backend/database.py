"""
EmuFlow — Async SQLAlchemy 2.0 database layer.

Exposes:
- ``engine``       : the global ``AsyncEngine`` instance.
- ``SessionLocal`` : ``async_sessionmaker`` for producing AsyncSessions.
- ``Base``         : declarative base for ORM models.
- ``get_session``  : FastAPI dependency yielding an ``AsyncSession``.
- ``init_models``  : helper that creates all tables (used by tests).

The DSN comes from the ``DATABASE_URL`` env var. Railway/Heroku style
``postgresql://`` URLs are transparently rewritten to
``postgresql+asyncpg://`` so callers don't have to think about it.

For SQLite (used in unit tests), ``sqlite://`` is rewritten to
``sqlite+aiosqlite://``. We don't ship aiosqlite as a runtime dep — tests
install it on demand.
"""
from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from typing import Final

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

DEFAULT_SQLITE_URL: Final[str] = "sqlite+aiosqlite:///./emuflow_dev.db"


def _normalise_database_url(url: str) -> str:
    """Convert a synchronous DSN to an async-compatible one.

    >>> _normalise_database_url("postgresql://u:p@h:5432/db")
    'postgresql+asyncpg://u:p@h:5432/db'
    >>> _normalise_database_url("sqlite:///./test.db")
    'sqlite+aiosqlite:///./test.db'
    """
    if url.startswith("postgres://"):  # legacy Heroku style
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("sqlite://") and "+aiosqlite" not in url:
        return "sqlite+aiosqlite://" + url[len("sqlite://") :]
    return url


def get_database_url() -> str:
    """Return the resolved (async) database URL."""
    raw = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
    return _normalise_database_url(raw)


def _make_engine(url: str) -> AsyncEngine:
    """Create an ``AsyncEngine`` with sensible defaults per backend."""
    is_sqlite = url.startswith("sqlite")
    kwargs: dict[str, object] = {"future": True, "echo": False}
    if is_sqlite:
        # SQLite + StaticPool is fine for tests; default for file-based dev DB.
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
        kwargs["pool_pre_ping"] = True
    return create_async_engine(url, **kwargs)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# Module-level singletons — initialised at import time using current env.
DATABASE_URL: str = get_database_url()
engine: AsyncEngine = _make_engine(DATABASE_URL)
SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


def reconfigure(url: str) -> None:
    """Recreate the engine + sessionmaker against a new URL.

    Used by the test suite to swap in an in-memory SQLite DB without
    spawning a fresh process. **Not** intended for production code.
    """
    global DATABASE_URL, engine, SessionLocal
    DATABASE_URL = _normalise_database_url(url)
    engine = _make_engine(DATABASE_URL)
    SessionLocal = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )
    logger.info("Database engine reconfigured: %s", DATABASE_URL.split("@")[-1])


async def init_models() -> None:
    """Create all tables on the current engine.

    Useful for tests and quick local bootstraps. Production should rely on
    Alembic migrations.
    """
    # Import models so they register on Base.metadata.
    import models  # noqa: F401  (re-export for metadata registration)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an ``AsyncSession``."""
    async with SessionLocal() as session:
        yield session
