# backend/models/image_file.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, UniqueConstraint
from .base import CoreBase


class ImageFiles(CoreBase):
    __tablename__ = "image_files"
    __table_args__ = (
        UniqueConstraint("hash", name="uq_image_files_hash"),
    )

    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String(64), nullable=False, index=True)
    path = Column(String, nullable=False)