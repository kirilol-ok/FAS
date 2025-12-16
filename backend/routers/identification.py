from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Pamiętaj o poprawnych importach z Twojej struktury projektu
from backend.databases.db import SQLiteSessionLocal, get_postgres_db
from backend.models.employees import Employees
from backend.models.reports import Reports
from backend.schemas import EmployeeDisplay
# Importujemy nową funkcję, którą stworzyliśmy wyżej
from backend.services.qr_service import decode_qr_from_bytes

router = APIRouter(
    prefix="/identify",
    tags=["Identification (Kiosk/Camera)"]
)

# Ta funkcja musi być synchroniczna (def, nie async def), 
# aby działać w BackgroundTasks bez blokowania pętli zdarzeń
def save_log_background(employee_id: int | None, status_msg: str, reason: str | None):
    """Zapisuje log w osobnej sesji (SQLite)"""
    db = SQLiteSessionLocal()
    try:
        report = Reports(
            employee_id=employee_id,
            status=status_msg,
            denial_reason=reason
        )
        db.add(report)
        db.commit()
        print(f" [BACKGROUND] Zapisano log: {status_msg} (ID: {report.id})")
    except Exception as e:
        print(f" [BACKGROUND] Błąd zapisu logu: {e}")
    finally:
        db.close()

# --- ENDPOINT ---
@router.post("/qr", response_model=EmployeeDisplay)
async def identify_user_by_qr(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_postgres_db)
):
    # 1. Odczyt pliku
    content = await file.read()
    
    # 2. Dekodowanie QR (użycie funkcji z qr_service.py)
    qr_code_data = decode_qr_from_bytes(content)

    if not qr_code_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Nie wykryto kodu QR na zdjęciu lub plik jest uszkodzony."
        )

    # 3. Szukanie pracownika w bazie (Postgres)
    result = await db.execute(select(Employees).where(Employees.qr_value == qr_code_data))
    employee = result.scalars().first()

    # --- SCENARIUSZ: Nieznany kod ---
    if not employee:
        masked = qr_code_data[:3] + "..." + qr_code_data[-3:] if len(qr_code_data) > 6 else "???"
        print(f"⚠️ Próba wejścia nieznanym kodem: {masked}")
        
        # Logowanie błędu w tle
        background_tasks.add_task(save_log_background, None, "Error", f"Nieznany kod: {masked}")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Kod QR nieznany."
        )

    # --- SCENARIUSZ: Pracownik zwolniony ---
    # Zakładam, że pole nazywa się 'dismissal_date' lub 'is_active', 
    # w Twoim kodzie było 'dismissed', dostosuj do swojego modelu.
    if getattr(employee, 'dismissed', False) or (hasattr(employee, 'dismissal_date') and employee.dismissal_date is not None):
        print(f"⛔ Próba wejścia zwolnionego: {employee.email}")
        
        background_tasks.add_task(save_log_background, employee.id, "Error", "Pracownik zwolniony")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Dostęp zabroniony (Pracownik nieaktywny)."
        )
    
    # --- SCENARIUSZ: Sukces ---
    log_message = f"Zalogowano: {employee.first_name} {employee.last_name}"
    print(f"✅ {log_message}")

    # Logowanie sukcesu w tle
    background_tasks.add_task(save_log_background, employee.id, "OK", log_message)
    
    return employee