from backend.models.base import CoreBase
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Boolean 
from sqlalchemy.orm import relationship
import uuid

def generate_uuid():
    return str(uuid.uuid4())


class Employees(CoreBase):
    __tablename__ = "Employees"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    qr_value = Column(String, index=True, nullable=True, unique=True)
    dismissed = Column(Boolean, default=False)
    dismissal_date = Column(DateTime, nullable=True)
    hire_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)
    image_id = Column(Integer, ForeignKey("ImageFiles.id"), nullable=True)
    image = relationship("ImageFiles", back_populates="employees")
