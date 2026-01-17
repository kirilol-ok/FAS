from __future__ import annotations
import hashlib
import mimetypes
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.employees import Employees
from backend.models.image_files import ImageFiles

class ImageStorageService:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _sha256_hex(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _guess_mime_type(filename: Optional[str]) -> str:
        if not filename: return "application/octet-stream"
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"

    async def save_image(self, data: bytes, filename: Optional[str] = None) -> ImageFiles:
        if not data: raise ValueError("Image data is empty")
        hash_hex = self._sha256_hex(data)

        # Sprawdzenie czy obraz już istnieje w SQLite
        result = await self.session.execute(select(ImageFiles).where(ImageFiles.hash == hash_hex))
        existing = result.scalar_one_or_none()
        if existing: return existing

        # Utworzenie nowego
        image = ImageFiles(
            hash=hash_hex,
            data=data,
            mime_type=self._guess_mime_type(filename),
            size_bytes=len(data),
        )
        self.session.add(image)
        
        try:
            await self.session.flush()
            return image
        except IntegrityError:
            await self.session.rollback()
            result = await self.session.execute(select(ImageFiles).where(ImageFiles.hash == hash_hex))
            return result.scalar_one()

    async def assign_employee_image(self, employee_id: int, image: ImageFiles) -> Employees:
        result = await self.session.execute(select(Employees).where(Employees.id == employee_id))
        employee = result.scalar_one()
        employee.image_id = image.id
        await self.session.flush()
        return employee