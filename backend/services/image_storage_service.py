from __future__ import annotations

import hashlib
import mimetypes
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.employees import Employees
from backend.models.image_files import ImageFiles


class ImageStorageService:
    def __init__(self, session: Session):
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

    def save_image(self, data: bytes, filename: Optional[str] = None) -> ImageFiles:
        if not data:
            raise ValueError("Image data is empty")

        hash_hex = self._sha256_hex(data)

        existing = self.session.execute(
            select(ImageFiles).where(ImageFiles.hash == hash_hex)
        ).scalar_one_or_none()
        if existing:
            return existing

        image = ImageFiles(
            hash=hash_hex,
            data=data,
            mime_type=self._guess_mime_type(filename),
            size_bytes=len(data),
        )
        self.session.add(image)

        # Handle race (2 uploads same image at once)
        try:
            self.session.flush()
            return image
        except IntegrityError:
            self.session.rollback()
            existing = self.session.execute(
                select(ImageFiles).where(ImageFiles.hash == hash_hex)
            ).scalar_one_or_none()
            if existing:
                return existing
            raise

    def assign_employee_image(self, employee_id: int, image: ImageFiles) -> Employees:
        employee = self.session.execute(
            select(Employees).where(Employees.id == employee_id)
        ).scalar_one()

        employee.image = image
        self.session.flush()
        return employee

    def get_image_bytes(self, image_id: int) -> Optional[Tuple[bytes, str]]:
        image = self.session.execute(
            select(ImageFiles).where(ImageFiles.id == image_id)
        ).scalar_one_or_none()

        if not image:
            return None
        return image.data, image.mime_type

    def get_image_bytes_by_hash(self, hash_hex: str) -> Optional[Tuple[bytes, str]]:
        if not hash_hex:
            raise ValueError("Hash value must be provided")

        image = self.session.execute(
            select(ImageFiles).where(ImageFiles.hash == hash_hex)
        ).scalar_one_or_none()

        if not image:
            return None
        return image.data, image.mime_type