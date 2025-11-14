from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum, func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from backend.models.base import Base

def teraz_utc() -> datetime:
    return datetime.utcnow()


def domyslna_data_usuniecia() -> datetime:
    return datetime.utcnow() + timedelta(days=180)

class Raporty(Base):
    __tablename__ = "Raporty"

    id = Column(Integer, primary_key=True, index=True)
    utworzono = Column(DateTime, index=True, default=teraz_utc(), nullable=False)
    retencja_do = Column(DateTime, default=domyslna_data_usuniecia(), nullable=False)
    pracownik = Column(String, index=True)
    status = Column(Enum('OK', 'Error'), index=True)
    przyczyna_odmowy = Column(String)
