from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from backend.models.base import CoreBase

class Employees(CoreBase):
    __tablename__ = "Employees"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False, unique=True)
    qr_value = Column(String, index=True, nullable=True, unique=True)

    image_id = Column(Integer, ForeignKey("image_files.id"), nullable=True)
    image = relationship("ImageFiles", backref="employees")
