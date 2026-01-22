import os
import pickle
from datetime import date, datetime

import cv2
import numpy as np
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.databases.db import get_sqlite_db
from backend.models.employees import Employees
from backend.models.image_files import ImageFiles
from backend.models.reports import Reports
from backend.schemas import EmployeeDisplay
from backend.services.face_recognision_service import FaceRecognitionService


router = APIRouter(prefix="/identify", tags=["Identification"])

face_service = FaceRecognitionService()

POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
POSTGRES_DB = os.getenv("POSTGRES_DB", "fas-project-database")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres_databases")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

POSTGRES_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

pg_async_engine = create_async_engine(POSTGRES_URL, echo=True)

AsyncSessionPG = sessionmaker(
    bind=pg_async_engine, class_=AsyncSession, expire_on_commit=False
)


async def save_log_background(
    employee_id: int | None, status_msg: str, reason: str | None
):
    """
    Save an access attempt log to the Reports table asynchronously.

    Args:
        employee_id (int | None): ID of the employee, or None if unknown.
        status_msg (str): Status message describing the outcome.
        reason (str | None): Detailed reason for the outcome.
    """
    print(f"--- [DEBUG] Attempt to save to Postgres: {status_msg} ({reason}) ---")

    async with AsyncSessionPG() as db:
        try:
            local_now = datetime.now()
            report = Reports(
                employee_id=employee_id,
                status=status_msg,
                denial_reason=reason,
                created_at=local_now,
            )
            db.add(report)
            await db.commit()
            print(f"вњ… [LOG ASYNC] COMMIT COMPLETED: {status_msg} -> {reason}")
        except Exception as e:
            await db.rollback()
            print(f"вќЊ [LOG ERROR] {e}")


@router.get("/logs")
async def get_all_logs():
    """
    Retrieve recent access attempt logs.
    """
    async with AsyncSessionPG() as db:
        result = await db.execute(select(Reports).order_by(Reports.id.desc()).limit(50))
        logs = result.scalars().all()
        return logs


@router.post("/qr", response_model=EmployeeDisplay)
async def identify_user_by_qr(
    background_tasks: BackgroundTasks,
    qr_code: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_sqlite_db),
):
    """
    Identify a user based on a QR code and uploaded face image.

    This endpoint performs the following steps:
    1. Look up the employee by QR code.
    2. Validate that the account is active and has not expired.
    3. Decode the stored facial embedding and compare it to the uploaded frame.
    4. Log the outcome asynchronously.

    Returns:
        EmployeeDisplay: The employee record on successful verification.

    Raises:
        HTTPException: If the QR code is unknown, the account has expired,
        the employee is inactive, a reference image is missing or corrupted,
        or the face verification fails.
    """
    print(f"\n### RECEIVED QR CODE: {qr_code} ###")

    # Look up the employee by QR code
    result = await db.execute(select(Employees).where(Employees.qr_value == qr_code))
    employee = result.scalars().first()

    if not employee:
        print(f"--- [SCENARIO 3] Unknown QR code. Returning error...")
        await save_log_background(None, "Error", f"Unknown QR code: {qr_code}")
        raise HTTPException(status_code=404, detail="Unknown QR code.")

    # Check if account has expired. Automatically dismiss and invalidate QR code if needed.
    if employee.expiration_date and employee.expiration_date < date.today():
        # If the account hasn't been dismissed yet, mark it as dismissed and remove QR code
        if not employee.dismissed:
            print(f"вљ пёЏ Account expired for {employee.email}. Dismissing automatically.")
            employee.dismissed = True
            employee.dismissal_date = date.today()
            # Invalidate the QR code so that future scans immediately fail
            employee.qr_value = None
            await db.commit()
            await db.refresh(employee)

        await save_log_background(employee.id, "Error", "Account expired")
        raise HTTPException(
            status_code=403,
            detail="Account expired (Account expired).",
        )

    # Check if the employee is dismissed (inactive)
    if employee.dismissed:
        await save_log_background(employee.id, "Error", "Employee inactive")
        raise HTTPException(status_code=403, detail="Employee inactive.")

    # Ensure the employee has a reference image uploaded
    if not employee.image_id:
        await save_log_background(employee.id, "Error", "No reference embedding")
        raise HTTPException(
            status_code=403,
            detail="No reference embedding (upload photo first).",
        )

    # Retrieve the reference image file record
    img_result = await db.execute(
        select(ImageFiles).where(ImageFiles.id == employee.image_id)
    )
    ref_image_file = img_result.scalars().first()

    # Validate that the reference embedding exists and is valid
    if not ref_image_file or not ref_image_file.embedding:
        await save_log_background(
            employee.id, "Error", "Reference embedding corrupted or missing"
        )
        raise HTTPException(
            status_code=500,
            detail="Reference embedding corrupted or missing.",
        )

    try:
        reference_embedding = pickle.loads(ref_image_file.embedding)
        if (
            not isinstance(reference_embedding, (list, tuple))
            or len(reference_embedding) == 0
        ):
            raise ValueError("Bad embedding format")
        reference_embedding = list(reference_embedding)
    except Exception as e:
        await save_log_background(
            employee.id, "Error", f"Reference embedding corrupted: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Reference embedding corrupted (unpickle error).",
        )

    # Read and decode the uploaded face image
    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame_bgr is None:
        await save_log_background(employee.id, "Error", "Invalid camera frame")
        raise HTTPException(status_code=400, detail="Invalid camera frame.")

    print(
        f"--- [FACE] Verifying embeddings for: {employee.first_name} {employee.last_name}..."
    )
    print(f"--- [DEBUG] Reference embedding length: {len(reference_embedding)}")

    try:
        is_verified = face_service.verify_face_with_embedding(
            frame=frame_bgr,
            reference_embedding=reference_embedding,
        )
    except Exception as e:
        await save_log_background(
            employee.id, "Error", f"Algorithm error: {str(e)}"
        )
        raise HTTPException(status_code=403, detail="Face verification error")

    if is_verified:
        print(f"--- [SCENARIO 1] Success. Saving log...")
        await save_log_background(employee.id, "OK", "Verification completed")
        return employee
    else:
        print("--- [SCENARIO 2] Face mismatch. Saving log...")
        await save_log_background(employee.id, "Error", "Face verification failed")
        raise HTTPException(status_code=403, detail="Face verification failed.")