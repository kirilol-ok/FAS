from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from backend.models.base import Base

class Pracowniki(Base):
    __tablename__ = "Pracowniki"

    id = Column(Integer, primary_key=True, index=True)
    imie = Column(String, index=True, nullable=False)
    nazwisko = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    qr_value = Column(String, index=True, nullable=True, unique=True)