import asyncio

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from backend.databases.db import (PostgresAsyncSession, SQLiteSessionLocal,
                                  init_postgres_db, init_sqlite_db,
                                  postgres_engine, sqlite_engine)


@pytest.fixture(scope="session", autouse=True)
def _dispose_engines_after_tests():
    """Dispose of database engines after all tests have completed."""
    yield

    async def _dispose() -> None:
        await sqlite_engine.dispose()
        await postgres_engine.dispose()

    asyncio.run(_dispose())


def test_engines_are_async() -> None:
    """Verify that the created engines are asynchronous engines."""
    assert isinstance(sqlite_engine, AsyncEngine)
    assert isinstance(postgres_engine, AsyncEngine)


@pytest.mark.asyncio
async def test_sqlite_session_factory_returns_async_session() -> None:
    """Ensure that the SQLite session factory yields an AsyncSession and can execute queries."""
    async with SQLiteSessionLocal() as session:
        assert isinstance(session, AsyncSession)
        res = await session.execute(text("SELECT 1"))
        assert res.scalar_one() == 1


@pytest.mark.asyncio
async def test_postgres_session_factory_returns_async_session() -> None:
    """Ensure that the Postgres session factory yields an AsyncSession (if available)."""
    # The connection itself may fail if Postgres isn't available; we just test type here.
    session = PostgresAsyncSession()
    assert isinstance(session, AsyncSession)


@pytest_asyncio.fixture
async def require_postgres():
    """Skip tests requiring Postgres if it cannot be reached."""
    try:
        async with postgres_engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            assert res.scalar_one() == 1
    except Exception:
        pytest.skip("Postgres is not available / not reachable from tests")


@pytest.mark.asyncio
async def test_init_sqlite_db_creates_tables() -> None:
    """init_sqlite_db should create tables on the SQLite database."""
    await init_sqlite_db()
    async with sqlite_engine.connect() as conn:
        res = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        )
        assert res.scalar_one() is not None


@pytest.mark.asyncio
async def test_init_postgres_db_runs(require_postgres) -> None:
    """init_postgres_db should attempt to initialise the Postgres database (if reachable)."""
    await init_postgres_db()
    async with postgres_engine.connect() as conn:
        res = await conn.execute(text("SELECT 1"))
        assert res.scalar_one() == 1
