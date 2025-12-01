from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

BASE_DIR = Path(__file__).resolve().parents[1]
DB_DIR = BASE_DIR / "backend" / "databases"
DB_DIR.mkdir(parents=True, exist_ok=True)

from backend.databases.db import (PostgresSessionLocal, SQLiteSessionLocal,
                                  init_sqlite_db, postgres_engine,
                                  sqlite_engine)


def is_postgres_available() -> bool:

    try:
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            _ = result.scalar()
        return True
    except OperationalError:
        return False


postgres_required = pytest.mark.skipif(
    not is_postgres_available(), reason="Postgres is not available"
)


def test_sqlite_engine_connect():

    with sqlite_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1


def test_sqlite_session_basic_query():

    db = SQLiteSessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1
    finally:
        db.close()


def test_init_sqlite_db_does_not_fail():

    init_sqlite_db()

    with sqlite_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@postgres_required
def test_postgres_engine_connect():

    with postgres_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1


@postgres_required
def test_postgres_session_basic_query():

    db = PostgresSessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1
    finally:
        db.close()


@postgres_required
def test_init_postgres_db_does_not_fail():
    with postgres_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
