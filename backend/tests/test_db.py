import asyncio

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from backend.databases.db import (
    sqlite_engine,
    postgres_engine,
    SQLiteSessionLocal,
    PostgresAsyncSession,
    init_sqlite_db,
    init_postgres_db,
)


@pytest.fixture(scope="session", autouse=True)
def _dispose_engines_after_tests():
    yield

    async def _dispose():
        await sqlite_engine.dispose()
        await postgres_engine.dispose()

    asyncio.run(_dispose())


def test_engines_are_async():
    assert isinstance(sqlite_engine, AsyncEngine)
    assert isinstance(postgres_engine, AsyncEngine)


@pytest.mark.asyncio
async def test_sqlite_session_factory_returns_async_session():
    async with SQLiteSessionLocal() as session:
        assert isinstance(session, AsyncSession)
        res = await session.execute(text("SELECT 1"))
        assert res.scalar_one() == 1


@pytest.mark.asyncio
async def test_postgres_session_factory_returns_async_session():
    async with PostgresAsyncSession() as session:
        assert isinstance(session, AsyncSession)


@pytest_asyncio.fixture
async def require_postgres():
    try:
        async with postgres_engine.connect() as conn:
            res = await conn.execute(text("SELECT 1"))
            assert res.scalar_one() == 1
    except Exception:
        pytest.skip("Postgres is not available / not reachable from tests")


@pytest.mark.asyncio
async def test_init_sqlite_db_creates_tables():
    await init_sqlite_db()

    async with sqlite_engine.connect() as conn:
        res = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        )
        assert res.scalar_one() is not None


@pytest.mark.asyncio
async def test_init_postgres_db_runs(require_postgres):
    await init_postgres_db()

    async with postgres_engine.connect() as conn:
        res = await conn.execute(text("SELECT 1"))
        assert res.scalar_one() == 1
