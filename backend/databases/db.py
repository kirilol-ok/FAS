import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.models import admins, employees, image_files
from backend.models.base import CoreBase, LogBase

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)
SQLITE_DB_PATH = BASE_DIR / "backend" / "databases" / "app.db"
SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH}"



POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
POSTGRES_DB = os.getenv("POSTGRES_DB", "fas-project-database")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres_databases")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

POSTGRES_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Engines
sqlite_engine = create_async_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False}, # Potrzebne dla SQLite
    echo=True,
)

# Async engine for PostgreSQL
postgres_engine = create_async_engine(
    POSTGRES_URL,
    echo=True,
    future=True,
    connect_args={"ssl": False} 
)

# Session fabrics
SQLiteSessionLocal = sessionmaker(
    bind=sqlite_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

PostgresAsyncSession = sessionmaker(
    bind=postgres_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_sqlite_db():
    async with sqlite_engine.begin() as conn:
        await conn.run_sync(LogBase.metadata.create_all)

# --- "RETRY LOGIC" ---
async def init_postgres_db() -> None:
    
    
    retries = 10  # 
    while retries > 0:
        try:
            print(f" Próba połączenia z bazą ({POSTGRES_HOST})...")
            async with postgres_engine.begin() as conn:
                await conn.run_sync(CoreBase.metadata.create_all)
            print(" Połączono z bazą danych pomyślnie!")
            return  # 
            
        except Exception as e:
            print(f" Błąd połączenia z bazą: {e}")
            print(" Czekam 5 sekund na start bazy...")
            await asyncio.sleep(5)
            retries -= 1
    
    print(" Nie udało się połączyć z bazą po wielu próbach. Aplikacja może nie działać poprawnie.")

async def init_all_db() -> None:
    await init_sqlite_db()
    await init_postgres_db()


# --- DEPENDENCY INJECTION ---

async def get_sqlite_db() -> AsyncGenerator:
    db = SQLiteSessionLocal()
    try:
        yield db
    finally:
        await db.close()

async def get_postgres_db() -> AsyncGenerator:
    async with PostgresAsyncSession() as db:
        yield db