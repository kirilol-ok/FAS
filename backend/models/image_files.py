"""
Redefinition of the ImageFiles model for storing face embeddings.

This module replaces the original ImageFiles model that stored raw image
bytes on disk.  Instead of storing the image file itself, we now keep a
serialized representation of the face embedding.  Each embedding is
represented as a pickled NumPy array, which can be deserialized and used
directly for face comparison.  The hash column is computed from the
embedding bytes to ensure uniqueness.

Attributes
----------
id : int
    Primary key for the table.
hash : str
    Hex‑encoded SHA‑256 digest of the embedding bytes.  A unique
    constraint ensures that duplicate embeddings are not stored multiple
    times.
embedding : bytes
    Pickled representation of the face embedding vector.  This field is
    mandatory; without it the record is incomplete.
mime_type : str | None
    Optional original MIME type of the uploaded image.  Stored for
    informational purposes and possible debugging.
size_bytes : int | None
    Size in bytes of the serialized embedding.  Retained for auditing
    and potential storage management.

Relationships
-------------
employees : list[Employees]
    A one‑to‑many relationship back to the Employees table.  Each
    employee can reference a single ImageFiles record via the
    ``image_id`` foreign key.

"""

from sqlalchemy import Column, Integer, String, UniqueConstraint, LargeBinary
from sqlalchemy.orm import relationship

from .base import CoreBase


class ImageFiles(CoreBase):
    """SQLAlchemy model for storing face embeddings instead of raw images."""

    __tablename__ = "ImageFiles"
    __table_args__ = (UniqueConstraint("hash", name="uq_image_files_hash"),)

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)
    # A unique digest of the embedding bytes
    hash = Column(String(64), nullable=False, index=True)
    # Serialized (pickled) face embedding
    embedding = Column(LargeBinary, nullable=False)
    # Optional MIME type of the original file; retained for debugging
    mime_type = Column(String, nullable=True)
    # Size of the serialized embedding in bytes
    size_bytes = Column(Integer, nullable=True, default=0)

    # Relationship back to Employees; each ImageFiles record can be referenced
    # by many employees but each employee references at most one image
    employees = relationship("Employees", back_populates="image")