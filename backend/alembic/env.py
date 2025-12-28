from __future__ import annotations

import sys
import importlib
import pkgutil
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Make sure project root is on sys.path ---
# env.py is: /app/backend/alembic/env.py
# project root is: /app
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Alembic config ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Import Base (metadata) ---
# Your project likely uses LogBase as declarative base
try:
    from backend.models.base import LogBase as Base  # preferred in your case
except Exception:
    from backend.models.base import Base  # fallback if you named it Base

# --- Import all model modules so metadata includes all tables ---
import backend.models as models_pkg

for _, module_name, is_pkg in pkgutil.iter_modules(models_pkg.__path__):
    if is_pkg:
        continue
    if module_name in ("base", "__init__"):
        continue
    importlib.import_module(f"{models_pkg.__name__}.{module_name}")

target_metadata = Base.metadata


def _is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite:")


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = _is_sqlite_url(url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=is_sqlite,  # important for SQLite migrations
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = _is_sqlite_url(url)

    connect_args = {}
    if is_sqlite:
        connect_args = {"check_same_thread": False}

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
