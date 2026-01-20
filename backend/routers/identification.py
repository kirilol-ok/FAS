from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
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
# Host: 'db' (nazwa serwisu z docker-compose)
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
POSTGRES_DB = os.getenv("POSTGRES_DB", "fas-project-database")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres_databases")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

POSTGRES_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Ustawiamy echo=True -> Zobaczysz SQL w terminalu!
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
            # Nie ma tu printa "Połączenie zamknięte" - jeśli go zobaczysz, to stary kod!
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
        # Pobieramy 50 ostatnich logów
        result = await db.execute(select(Reports).order_by(Reports.id.desc()).limit(50))
        logs = result.scalars().all()
        return logs

# ==============================================================================
# GŁÓWNY ENDPOINT (POST)
# ==============================================================================
@router.post("/qr", response_model=EmployeeDisplay)
async def identify_user_by_qr(
    background_tasks: BackgroundTasks, # Możesz to usunąć, jeśli już nie używasz
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
        # AWAIT (czekamy aż się zapisze, potem błąd)
        await save_log_background(None, "Error", f"Nieznany kod QR: {qr_code}")
        raise HTTPException(status_code=404, detail="Unknown QR code.")

    if employee.dismissed:
        await save_log_background(employee.id, "Error", "Pracownik zwolniony")
        raise HTTPException(status_code=403, detail="Employee inactive.")

    # 2. Przygotowanie do weryfikacji twarzy
    if not employee.image_id:
        await save_log_background(employee.id, "Error", "Brak zdjęcia wzorcowego")
        raise HTTPException(status_code=403, detail="No reference photo.")

    img_result = await db.execute(select(ImageFiles).where(ImageFiles.id == employee.image_id))
    ref_image_file = img_result.scalars().first()

    if not ref_image_file or not ref_image_file.data:
        raise HTTPException(status_code=500, detail="Reference photo corrupted.")

    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    print(f"--- [FACE] Weryfikacja dla: {employee.first_name} {employee.last_name}...")
    
    is_verified = False
    try:
        is_verified = face_service.verify_face_with_bytes(
            frame=frame, 
            reference_image_bytes=ref_image_file.data,
            mime_type=ref_image_file.mime_type
        )
    except Exception as e:
        await save_log_background(employee.id, "Error", f"Błąd algorytmu: {str(e)}")
        raise HTTPException(status_code=403, detail="Face verification error")
    

    # ... (dekodowanie zdjęcia powyżej)

    # --- DEBUG WIZUALNY ---
    print("--- [DEBUG] Zapisuję zdjęcia do porównania na dysku...")
    # Zapisujemy to co przyszło z kamery (musimy wrócić do BGR żeby zapisać poprawnie przez OpenCV)
    cv2.imwrite("debug_kamera.jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    
    # Zapisujemy to co jest w bazie
    with open("debug_baza.jpg", "wb") as f:
        f.write(ref_image_file.data)
    # ----------------------

    print(f"--- [FACE] Weryfikacja dla: {employee.first_name} {employee.last_name}...")

    # --- DECYZJA KOŃCOWA ---
    
    if is_verified:
        # --- SCENARIUSZ 1: SUKCES ---
        print(f"--- [SCENARIUSZ 1] Sukces. Zapisuję log...")
        # Tu też użyjmy await dla pewności
        await save_log_background(employee.id, "OK", "Weryfikacja pomyślna")
        return employee
    else:
        # --- SCENARIUSZ 2: ZŁA TWARZ ---
        print("--- [SCENARIUSZ 2] Twarz niezgodna. Zapisuję log...")
        # AWAIT (To naprawi Twój problem)
        await save_log_background(employee.id, "Error", "Twarz niezgodna")
        raise HTTPException(status_code=403, detail="Face verification failed.")