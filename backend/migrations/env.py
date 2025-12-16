from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# ---- Ustawiamy ścieżki ----
# Ten plik: /app/backend/migrations/env.py
# Struktura:
#   /app/
#     .env
#     backend/
#       __init__.py
#       models/
#       databases/
#       migrations/env.py  (ten plik)

# katalog /app
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# dodajemy /app do sys.path, żeby można było importować pakiet "backend"
sys.path.insert(0, str(PROJECT_ROOT))

# ---- Konfiguracja Alembica ----

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- Ładowanie .env z /app/.env ----

ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    "postgresql+psycopg2://admin:admin@postgres_databases:5432/fas-project-database",
)

# ---- Import modeli i metadata ----

# Importujemy wszystkie moduły z modelami, które dziedziczą po CoreBase
from backend.models import (admins, employees, image_files,  # noqa: F401, E402
                            reports)
from backend.models.base import CoreBase  # noqa: E402

target_metadata = CoreBase.metadata


def run_migrations_offline() -> None:
    """Uruchamianie migracji w trybie offline (bez połączenia z bazą)."""
    url = POSTGRES_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Uruchamianie migracji w trybie online (z połączeniem do bazy)."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = POSTGRES_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
