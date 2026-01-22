"""Alembic migration environment.

This ``env.py`` configures Alembic for both offline and online migrations.
It imports the unified declarative ``Base`` class from ``backend.models.base``
and ensures all model modules are imported so that Alembic's autogeneration
can discover every table.  See the commentary in ``backend/models/base.py``
for details on why a single base is used.

The code includes logic for SQLite migrations: when the target database URL
starts with ``sqlite:``, batch mode is enabled via ``render_as_batch`` so
ALTER TABLE operations work correctly.  For other databases like PostgreSQL,
standard migrations apply.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make sure project root is on sys.path.  ``env.py`` lives under
# ``backend/alembic``, so the root project directory is two levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Alembic Config object, which provides access to values within the
# ``alembic.ini`` file.  This is a global configuration and will have
# attributes set when invoked via the Alembic command line.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all model modules so that they register their tables with ``Base``.
import backend.models as models_pkg
# Import the unified Base for all models.  Previously the project used
# separate ``LogBase`` and ``CoreBase`` classes.  Now both point to
# the same ``Base``, so importing ``Base`` suffices.
from backend.models.base import Base

for _, module_name, is_pkg in pkgutil.iter_modules(models_pkg.__path__):
    if is_pkg:
        continue
    # Skip base definitions and package initialisation modules.
    if module_name in ("base", "__init__"):
        continue
    importlib.import_module(f"{models_pkg.__name__}.{module_name}")

# Set the target metadata to the metadata of our unified Base.  Alembic
# uses this to compare against the database and autogenerate migrations.
target_metadata = Base.metadata


def _is_sqlite_url(url: str) -> bool:
    """Return True if the given SQLAlchemy URL points at an SQLite database."""
    return url.startswith("sqlite:")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though
    an Engine is acceptable here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to ``context.execute()`` here emit the given string to the script output.
    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with
    the context.
    """
    section = config.get_section(config.config_ini_section) or {}
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = _is_sqlite_url(url)

    connect_args = {}
    if is_sqlite:
        # When connecting to SQLite in a multithreaded environment, pass
        # ``check_same_thread=False`` so that the same connection can be used
        # across threads.  Without this, Alembic will raise an error.
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
