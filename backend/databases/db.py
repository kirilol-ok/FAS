import os
from pathlib import Path

from backend.models.base import CoreBase, LogBase
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)
SQLITE_URL = "sqlite:///./backend/databases/app.db"

POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
POSTGRES_DB = os.getenv("POSTGRES_DB", "fas-project-database")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres_databases")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

POSTGRES_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Engines
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

# Session fabrics
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

    from backend.models import admins, employees, image_files

    LogBase.metadata.create_all(bind=sqlite_engine)


def init_all_db() -> None:
    init_sqlite_db()
