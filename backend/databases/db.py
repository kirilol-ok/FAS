# backend/databases/db.py
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.base import CoreBase, LogBase

SQLITE_URL = f"sqlite:///./backend/databases/app.db"

# PostgreSQL (użytkownicy, role, uprawnienia, profile twarzy itd.)
# Zmień na swoje dane dostępu
POSTGRES_URL = (
    "postgresql+psycopg2://user:password@localhost:5432/your_db_name"
)

# --- Silniki ---

sqlite_engine = create_engine(
    SQLITE_URL,
    echo=True,
    future=True,
)

postgres_engine = create_engine(
    POSTGRES_URL,
    echo=True,
    future=True,
)

SQLiteSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sqlite_engine,
)

PostgresSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=postgres_engine,
)

def init_sqlite_db() -> None:
    from backend.models import reports
    LogBase.metadata.create_all(bind=sqlite_engine)


def init_postgres_db() -> None:
    from backend.models import employees, admins
    CoreBase.metadata.create_all(bind=postgres_engine)


def init_all_db() -> None:
    init_sqlite_db()
    init_postgres_db()
