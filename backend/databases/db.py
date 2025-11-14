from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.base import Base

DATABASE_URL = "sqlite:///./databases/app.db"

engine = create_engine(
    DATABASE_URL,
    echo=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def init_db():
    from backend.models import administrator, pracownik, raport

    Base.metadata.create_all(bind=engine)