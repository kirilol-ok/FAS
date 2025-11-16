from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from backend.models.base import CoreBase

class Admins(CoreBase):
    __tablename__ = "Admins"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    password = Column(String, nullable=False)
    qr_value = Column(String, index=True, nullable=True, unique=True)