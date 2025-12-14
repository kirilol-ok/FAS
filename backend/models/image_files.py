from datetime import datetime

from sqlalchemy import Column, Integer, String, UniqueConstraint, LargeBinary
from sqlalchemy.orm import relationship

from .base import CoreBase


class ImageFiles(CoreBase):
    __tablename__ = "ImageFiles"
    __table_args__ = (UniqueConstraint("hash", name="uq_image_files_hash"),)

    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String(64), nullable=False, index=True)
    path = Column(String, nullable=True)

    data = Column(LargeBinary, nullable=False)

    mime_type = Column(String, nullable=False, default="application/octet-stream")
    size_bytes = Column(Integer, nullable=False, default=0)

    employees = relationship("Employees", back_populates="image")
