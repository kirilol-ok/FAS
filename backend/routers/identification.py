from datetime import datetime
import pickle

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import cv2
import numpy as np
import os

# --- IMPORTY SQLITE (Główna baza) ---
from backend.databases.db import get_sqlite_db

# Modele
from backend.models.employees import Employees
from backend.models.reports import Reports
from backend.models.image_files import ImageFiles
from backend.schemas import EmployeeDisplay
from backend.services.face_recognision_service import FaceRecognitionService

router = APIRouter(
    prefix="/identify",
    tags=["Identification"]
)

face_service = FaceRecognitionService()

# ==============================================================================
# KONFIGURACJA POSTGRES (ASYNC)
# ==============================================================================
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
    bind=pg_async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# ==============================================================================
# ZADANIE W TLE (ASYNC)
# ==============================================================================
async def save_log_background(employee_id: int | None, status_msg: str, reason: str | None):
    print(f"--- [DEBUG] Próba zapisu do Postgres: {status_msg} ({reason}) ---")

    async with AsyncSessionPG() as db:
        try:
            local_now = datetime.now()
            report = Reports(
                employee_id=employee_id,
                status=status_msg,
                denial_reason=reason,
                created_at=local_now
            )
            db.add(report)
            await db.commit()
            print(f"✅ [LOG ASYNC] COMMIT WYKONANY: {status_msg} -> {reason}")
        except Exception as e:
            await db.rollback()
            print(f"❌ [LOG ERROR] {e}")

# ==============================================================================
# ENDPOINT DO PODGLĄDU LOGÓW (GET)
# ==============================================================================
@router.get("/logs")
async def get_all_logs():
    async with AsyncSessionPG() as db:
        result = await db.execute(select(Reports).order_by(Reports.id.desc()).limit(50))
        logs = result.scalars().all()
        return logs

# ==============================================================================
# GŁÓWNY ENDPOINT (POST)
# ==============================================================================
@router.post("/qr", response_model=EmployeeDisplay)
async def identify_user_by_qr(
    background_tasks: BackgroundTasks,
    qr_code: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_sqlite_db)
):
    print(f"\n### OTRZYMANO KOD QR: {qr_code} ###")

    # 1. Sprawdzenie kodu QR w bazie SQLite
    result = await db.execute(select(Employees).where(Employees.qr_value == qr_code))
    employee = result.scalars().first()

    # --- SCENARIUSZ 3: ZŁY QR ---
    if not employee:
        print(f"--- [SCENARIUSZ 3] Nieznany QR. Loguję błąd...")
        await save_log_background(None, "Error", f"Nieznany kod QR: {qr_code}")
        raise HTTPException(status_code=404, detail="Unknown QR code.")

    if employee.dismissed:
        await save_log_background(employee.id, "Error", "Pracownik zwolniony")
        raise HTTPException(status_code=403, detail="Employee inactive.")

    # 2. Przygotowanie do weryfikacji twarzy (embedding w DB)
    if not employee.image_id:
        await save_log_background(employee.id, "Error", "Brak embeddingu wzorcowego")
        raise HTTPException(status_code=403, detail="No reference embedding (upload photo first).")

    img_result = await db.execute(select(ImageFiles).where(ImageFiles.id == employee.image_id))
    ref_image_file = img_result.scalars().first()

    # ZAMIANA: wcześniej było ref_image_file.data (raw image)
    # Teraz w DB mamy ref_image_file.embedding (pickled bytes)
    if not ref_image_file or not ref_image_file.embedding:
        await save_log_background(employee.id, "Error", "Embedding wzorcowy uszkodzony/brak")
        raise HTTPException(status_code=500, detail="Reference embedding corrupted or missing.")

    try:
        reference_embedding = pickle.loads(ref_image_file.embedding)
        if not isinstance(reference_embedding, (list, tuple)) or len(reference_embedding) == 0:
            raise ValueError("Bad embedding format")
        reference_embedding = list(reference_embedding)
    except Exception as e:
        await save_log_background(employee.id, "Error", f"Nie można odczytać embeddingu: {str(e)}")
        raise HTTPException(status_code=500, detail="Reference embedding corrupted (unpickle error).")

    # 3. Odczyt i dekodowanie klatki z kamery
    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame_bgr is None:
        await save_log_background(employee.id, "Error", "Niepoprawny obraz z kamery")
        raise HTTPException(status_code=400, detail="Invalid camera frame.")

    print(f"--- [FACE] Weryfikacja embeddingów dla: {employee.first_name} {employee.last_name}...")
    print(f"--- [DEBUG] Reference embedding length: {len(reference_embedding)}")

    # 4. Porównanie embeddingów (kamera vs baza)
    try:
        is_verified = face_service.verify_face_with_embedding(
            frame=frame_bgr,                       # BGR OK (cv.imwrite w serwisie)
            reference_embedding=reference_embedding # list[float]
        )
    except Exception as e:
        await save_log_background(employee.id, "Error", f"Błąd algorytmu: {str(e)}")
        raise HTTPException(status_code=403, detail="Face verification error")

    # --- DECYZJA KOŃCOWA ---
    if is_verified:
        print(f"--- [SCENARIUSZ 1] Sukces. Zapisuję log...")
        await save_log_background(employee.id, "OK", "Weryfikacja pomyślna")
        return employee
    else:
        print("--- [SCENARIUSZ 2] Twarz niezgodna. Zapisuję log...")
        await save_log_background(employee.id, "Error", "Twarz niezgodna")
        raise HTTPException(status_code=403, detail="Face verification failed.")
