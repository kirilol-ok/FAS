# backend/tests/test_db_init.py
from datetime import timedelta

from sqlalchemy import inspect

from backend.databases.db import sqlite_engine, SQLiteSessionLocal, init_sqlite_db
from backend.models.reports import Reports


def test_tables_are_created_sqlite():
    """
    Sprawdza, czy po wywołaniu init_sqlite_db()
    tabela 'reports' istnieje w bazie SQLite.
    """
    init_sqlite_db()

    inspector = inspect(sqlite_engine)
    table_names = inspector.get_table_names()

    assert "Reports" in table_names


def test_create_report_and_defaults_sqlite():
    """
    Sprawdza, czy w bazie logów (SQLite) można utworzyć Report
    i czy poprawnie ustawiają się daty: created_at i retention_until.
    """
    init_sqlite_db()

    db = SQLiteSessionLocal()
    try:
        report = Reports(employee_id=1)
        db.add(report)
        db.commit()
        db.refresh(report)

        assert report.id is not None
        assert report.created_at is not None
        assert report.retention_until is not None
        assert report.retention_until > report.created_at

        diff = report.retention_until - report.created_at
        assert timedelta(days=150) <= diff <= timedelta(days=210)
    finally:
        db.close()
