from backend.models.base import CoreBase
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean 
from sqlalchemy.orm import relationship


class Employees(CoreBase):
    __tablename__ = "Employees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    qr_value = Column(String, index=True, nullable=True, unique=True)
    dismissed = Column(Boolean, default=False)
    dismissal_date = Column(DateTime, nullable=True)

    image_id = Column(Integer, ForeignKey("ImageFiles.id"), nullable=True)
    image = relationship("ImageFiles", back_populates="employees")
