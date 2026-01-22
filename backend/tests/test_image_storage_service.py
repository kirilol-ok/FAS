import hashlib
import pickle
from typing import Sequence

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (AsyncSession, async_scoped_session,
                                    create_async_engine)
from sqlalchemy.orm import sessionmaker

from backend.models.base import CoreBase
from backend.models.employees import Employees
from backend.models.image_files import ImageFiles
from backend.services.image_storage_service import ImageStorageService


@pytest.fixture()
async def session():
    """
    Provide a new asynchronous in-memory SQLite session for each test.

    All tables defined on CoreBase are created in the temporary database.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(CoreBase.metadata.create_all)
    SessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with SessionLocal() as db:
        yield db
    await engine.dispose()


@pytest.fixture()
async def service(session):
    return ImageStorageService(session)


@pytest.fixture()
def sample_image_bytes() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"fake-image-bytes"


@pytest.mark.asyncio
async def test_save_image_creates_row(
    monkeypatch,
    service: ImageStorageService,
    session: AsyncSession,
    sample_image_bytes: bytes,
) -> None:
    """save_image should create a new ImageFiles row with computed embedding data."""
    # patch _compute_embedding to return a known vector
    embedding: Sequence[float] = [0.1, 0.2, 0.3]
    monkeypatch.setattr(
        ImageStorageService, "_compute_embedding", lambda self, data: embedding
    )
    img = await service.save_image(sample_image_bytes, filename="photo.png")
    assert img.id is not None
    expected_bytes = pickle.dumps(list(embedding))
    expected_hash = hashlib.sha256(expected_bytes).hexdigest()
    assert img.hash == expected_hash
    assert img.embedding == expected_bytes
    assert img.size_bytes == len(expected_bytes)
    assert img.mime_type == "image/png"
    # verify only one record exists
    res = await session.execute(select(func.count(ImageFiles.id)))
    count = res.scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_save_image_deduplicates_by_hash(
    monkeypatch,
    service: ImageStorageService,
    session: AsyncSession,
    sample_image_bytes: bytes,
) -> None:
    """Calling save_image twice with identical embeddings should return the same record."""
    embedding: Sequence[float] = [0.5, 0.5]
    monkeypatch.setattr(
        ImageStorageService, "_compute_embedding", lambda self, data: embedding
    )
    img1 = await service.save_image(sample_image_bytes, filename="a.png")
    img2 = await service.save_image(sample_image_bytes, filename="b.png")
    assert img1.id == img2.id
    assert img1.hash == img2.hash
    # ensure only one row in the table
    res = await session.execute(select(func.count(ImageFiles.id)))
    assert res.scalar_one() == 1


@pytest.mark.asyncio
async def test_save_image_empty_data_raises(service: ImageStorageService) -> None:
    """save_image should raise ValueError when given empty bytes."""
    with pytest.raises(ValueError):
        await service.save_image(b"", filename="empty.png")


@pytest.mark.asyncio
async def test_save_image_returns_existing_if_already_in_db(
    monkeypatch,
    service: ImageStorageService,
    session: AsyncSession,
    sample_image_bytes: bytes,
) -> None:
    """If a matching hash exists in the DB, save_image should return it rather than creating a new row."""
    embedding: Sequence[float] = [1.0]
    monkeypatch.setattr(
        ImageStorageService, "_compute_embedding", lambda self, data: embedding
    )
    # manually insert an existing image
    embedding_bytes = pickle.dumps(list(embedding))
    hash_hex = hashlib.sha256(embedding_bytes).hexdigest()
    existing = ImageFiles(
        hash=hash_hex,
        embedding=embedding_bytes,
        mime_type="image/png",
        size_bytes=len(embedding_bytes),
    )
    session.add(existing)
    await session.commit()
    img = await service.save_image(sample_image_bytes, filename="photo.png")
    assert img.id == existing.id
    res = await session.execute(select(func.count(ImageFiles.id)))
    assert res.scalar_one() == 1


@pytest.mark.asyncio
async def test_assign_employee_image_sets_fk(
    monkeypatch,
    service: ImageStorageService,
    session: AsyncSession,
    sample_image_bytes: bytes,
) -> None:
    """assign_employee_image should set the employee.image relationship and foreign key."""
    # patch embedding
    embedding: Sequence[float] = [0.9]
    monkeypatch.setattr(
        ImageStorageService, "_compute_embedding", lambda self, data: embedding
    )
    employee = Employees(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        qr_value=None,
        hire_date=__import__("datetime").date.today(),
    )
    session.add(employee)
    await session.flush()
    image = await service.save_image(sample_image_bytes, filename="photo.png")
    await service.assign_employee_image(employee_id=employee.id, image=image)
    await session.flush()
    await session.refresh(employee)
    assert employee.image_id == image.id
    assert employee.image is not None
    assert employee.image.hash == image.hash


@pytest.mark.asyncio
async def test_get_embedding_returns_list(
    monkeypatch,
    service: ImageStorageService,
    session: AsyncSession,
    sample_image_bytes: bytes,
) -> None:
    """get_embedding should return the deserialized embedding list for an existing image."""
    embedding: Sequence[float] = [2.5, 3.5]
    monkeypatch.setattr(
        ImageStorageService, "_compute_embedding", lambda self, data: embedding
    )
    image = await service.save_image(sample_image_bytes, filename="photo.png")
    await session.commit()
    result = await service.get_embedding(image.id)
    assert isinstance(result, list)
    assert result == list(embedding)


@pytest.mark.asyncio
async def test_get_embedding_returns_none_for_missing_id(
    service: ImageStorageService,
) -> None:
    """get_embedding should return None when the image id is not present."""
    result = await service.get_embedding(999999)
    assert result is None


@pytest.mark.asyncio
async def test_get_embedding_by_hash_returns_list(
    monkeypatch,
    service: ImageStorageService,
    session: AsyncSession,
    sample_image_bytes: bytes,
) -> None:
    """get_embedding_by_hash should return the embedding list for a known hash."""
    embedding: Sequence[float] = [4.2]
    monkeypatch.setattr(
        ImageStorageService, "_compute_embedding", lambda self, data: embedding
    )
    image = await service.save_image(sample_image_bytes, filename="photo.png")
    await session.commit()
    result = await service.get_embedding_by_hash(image.hash)
    assert isinstance(result, list)
    assert result == list(embedding)


@pytest.mark.asyncio
async def test_get_embedding_by_hash_raises_for_empty(
    monkeypatch, service: ImageStorageService
) -> None:
    """get_embedding_by_hash should raise a ValueError when an empty hash is provided."""
    with pytest.raises(ValueError):
        await service.get_embedding_by_hash("")
