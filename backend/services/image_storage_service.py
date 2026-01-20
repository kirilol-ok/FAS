"""
Enhanced image storage service that stores and retrieves face embeddings.

This service computes a face embedding for each uploaded image using DeepFace
and stores the pickled embedding in the database. The hash associated with each
record is derived from the serialized embedding.

IMPORTANT: this version is ASYNC and works with SQLAlchemy AsyncSession.
"""

from __future__ import annotations

import hashlib
import mimetypes
import os
import pickle
import tempfile
from typing import Optional

from deepface import DeepFace  # type: ignore
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.employees import Employees
from backend.models.image_files import ImageFiles


class ImageStorageService:
    """Service for computing and persisting face embeddings (async)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _sha256_hex(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _guess_mime_type(filename: Optional[str]) -> str:
        if not filename:
            return "application/octet-stream"
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"

    def _compute_embedding(self, image_bytes: bytes) -> list[float]:
        """Compute embedding from image bytes (sync, DeepFace is sync)."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name

        try:
            representations = DeepFace.represent(
                img_path=tmp_path,
                model_name="VGG-Face",
                enforce_detection=False,
                detector_backend="opencv",
            )
            if not representations:
                raise ValueError("No face embedding could be extracted from the image")

            embedding = representations[0].get("embedding")
            if not isinstance(embedding, (list, tuple)):
                raise ValueError("DeepFace returned an unexpected embedding format")

            return list(embedding)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    async def save_image(self, data: bytes, filename: Optional[str] = None) -> ImageFiles:
        """
        Persist a face embedding computed from the given image bytes.
        If an identical embedding already exists (determined by its hash),
        the existing record is returned.
        """
        if not data:
            raise ValueError("Image data is empty")

        embedding_vector = self._compute_embedding(data)
        embedding_bytes = pickle.dumps(embedding_vector)
        hash_hex = self._sha256_hex(embedding_bytes)

        res = await self.session.execute(select(ImageFiles).where(ImageFiles.hash == hash_hex))
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        image = ImageFiles(
            hash=hash_hex,
            embedding=embedding_bytes,
            mime_type=self._guess_mime_type(filename),
            size_bytes=len(embedding_bytes),
        )
        self.session.add(image)

        try:
            await self.session.flush()
            return image
        except IntegrityError:
            await self.session.rollback()
            res = await self.session.execute(select(ImageFiles).where(ImageFiles.hash == hash_hex))
            existing = res.scalar_one_or_none()
            if existing:
                return existing
            raise

    async def assign_employee_image(self, employee_id: int, image: ImageFiles) -> Employees:
        """Associate a stored embedding with an employee."""
        res = await self.session.execute(select(Employees).where(Employees.id == employee_id))
        employee = res.scalar_one()  # бросит исключение если нет сотрудника
        employee.image = image
        await self.session.flush()
        return employee

    async def get_embedding(self, image_id: int) -> Optional[list[float]]:
        res = await self.session.execute(select(ImageFiles).where(ImageFiles.id == image_id))
        image = res.scalar_one_or_none()
        if not image:
            return None
        try:
            return pickle.loads(image.embedding)
        except Exception:
            return None

    async def get_embedding_by_hash(self, hash_hex: str) -> Optional[list[float]]:
        if not hash_hex:
            raise ValueError("Hash value must be provided")

        res = await self.session.execute(select(ImageFiles).where(ImageFiles.hash == hash_hex))
        image = res.scalar_one_or_none()
        if not image:
            return None

        try:
            return pickle.loads(image.embedding)
        except Exception:
            return None
