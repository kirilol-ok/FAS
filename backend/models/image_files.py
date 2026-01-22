from sqlalchemy import Column, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import CoreBase


class ImageFiles(CoreBase):

    __tablename__ = "ImageFiles"
    __table_args__ = (UniqueConstraint("hash", name="uq_image_files_hash"),)

    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String(64), nullable=False, index=True)
    embedding = Column(LargeBinary, nullable=False)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True, default=0)

    employees = relationship("Employees", back_populates="image")
