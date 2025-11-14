# tests/test_db_init.py
from datetime import datetime, timedelta

from sqlalchemy import inspect

from ..databases.db import engine, SessionLocal, init_db
from ..models.raport import Raporty


def test_tables_are_created():
    """
    Sprawdza, czy po wywołaniu init_db() w bazie istnieją wymagane tabele.
    """
    init_db()

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "Raporty" in table_names


def test_tables_are_created():
    """
    Sprawdza, czy po wywołaniu init_db() w bazie istnieją wymagane tabele.
    """
    init_db()

    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "Raporty" in table_names


def test_create_raport_and_defaults():
    """
    Sprawdza, czy można utworzyć Raport i czy poprawnie ustawiają się daty.
    """
    init_db()

    db = SessionLocal()
    try:
        raport = Raporty()
        db.add(raport)
        db.commit()
        db.refresh(raport)

        assert raport.id is not None
        assert raport.utworzono is not None
        assert raport.retencja_do is not None
        assert raport.retencja_do > raport.utworzono

        diff = raport.retencja_do - raport.utworzono
        assert timedelta(days=150) <= diff <= timedelta(days=210)
    finally:
        db.close()

