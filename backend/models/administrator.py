from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from backend.models.base import Base

class Administratorze(Base):
    __tablename__ = "Administratorze"

    id = Column(Integer, primary_key=True, index=True)
    imie = Column(String, index=True, nullable=False)
    nazwisko = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    haslo = Column(String, nullable=False)
    qr_value = Column(String, index=True, nullable=True, unique=True)