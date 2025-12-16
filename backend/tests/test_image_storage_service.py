import hashlib

import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from backend.models.base import CoreBase
from backend.models.employees import Employees
from backend.models.image_files import ImageFiles
from backend.services.image_storage_service import ImageStorageService


@pytest.fixture()
def session():
    """
    Fast unit/integration style test DB (SQLite in-memory).
    If your ImageFiles.data uses PostgreSQL BYTEA type, switch it to LargeBinary
    in models OR run tests against Postgres.
    """
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    CoreBase.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def service(session):
    return ImageStorageService(session)


@pytest.fixture()
def sample_image_bytes():
    return b"\x89PNG\r\n\x1a\n" + b"fake-image-bytes"


def test_save_image_creates_row(service, session, sample_image_bytes):
    img = service.save_image(sample_image_bytes, filename="photo.png")

    assert img.id is not None
    assert img.hash == hashlib.sha256(sample_image_bytes).hexdigest()
    assert img.data == sample_image_bytes
    assert img.size_bytes == len(sample_image_bytes)
    assert img.mime_type == "image/png"

    count = session.execute(select(func.count(ImageFiles.id))).scalar_one()
    assert count == 1


def test_save_image_deduplicates_by_hash(service, session, sample_image_bytes):
    img1 = service.save_image(sample_image_bytes, filename="a.png")
    img2 = service.save_image(sample_image_bytes, filename="b.png")

    assert img1.id == img2.id
    assert img1.hash == img2.hash

    count = session.execute(select(func.count(ImageFiles.id))).scalar_one()
    assert count == 1


def test_save_image_empty_data_raises(service):
    with pytest.raises(ValueError):
        service.save_image(b"", filename="empty.png")


def test_save_image_returns_existing_if_already_in_db(service, session, sample_image_bytes):
    hash_hex = hashlib.sha256(sample_image_bytes).hexdigest()
    existing = ImageFiles(
        hash=hash_hex,
        data=sample_image_bytes,
        mime_type="image/png",
        size_bytes=len(sample_image_bytes),
    )
    session.add(existing)
    session.commit()

    img = service.save_image(sample_image_bytes, filename="photo.png")
    assert img.id == existing.id

    count = session.execute(select(func.count(ImageFiles.id))).scalar_one()
    assert count == 1


def test_assign_employee_image_sets_fk(service, session, sample_image_bytes):
    employee = Employees(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        qr_value=None,
    )
    session.add(employee)
    session.flush()

    image = service.save_image(sample_image_bytes, filename="photo.png")
    service.assign_employee_image(employee_id=employee.id, image=image)

    session.flush()
    session.refresh(employee)

    assert employee.image_id == image.id
    assert employee.image is not None
    assert employee.image.hash == image.hash


def test_get_image_bytes_returns_bytes_and_mime(service, session, sample_image_bytes):
    image = service.save_image(sample_image_bytes, filename="photo.png")
    session.commit()

    result = service.get_image_bytes(image.id)
    assert result is not None

    data, mime = result
    assert data == sample_image_bytes
    assert mime == "image/png"


def test_get_image_bytes_returns_none_for_missing_id(service):
    assert service.get_image_bytes(999999) is None
