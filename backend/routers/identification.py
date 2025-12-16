from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.databases.db import SQLiteSessionLocal, get_postgres_db
from backend.models.employees import Employees
from backend.models.reports import Reports
from backend.schemas import EmployeeDisplay

from backend.services.qr_service import decode_qr_from_bytes

router = APIRouter(
    prefix="/identify",
    tags=["Identification"]
)


def save_log_background(employee_id: int | None, status_msg: str, reason: str | None):
    
    db = SQLiteSessionLocal()
    try:
        report = Reports(
            employee_id=employee_id,
            status=status_msg,
            denial_reason=reason
        )
        db.add(report)
        db.commit()
        print(f" [BACKGROUND] Log saved: {status_msg} (ID: {report.id})")
    except Exception as e:
        print(f" [BACKGROUND] Error saving log: {e}")
    finally:
        db.close()

# --- ENDPOINT ---
@router.post("/qr", response_model=EmployeeDisplay)
async def identify_user_by_qr(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_postgres_db)
):
    
    content = await file.read()
    
    qr_code_data = decode_qr_from_bytes(content)

    if not qr_code_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No QR code detected in the image or file is corrupted."
        )

    
    result = await db.execute(select(Employees).where(Employees.qr_value == qr_code_data))
    employee = result.scalars().first()

    # --- Unknown QR Code ---
    if not employee:
        masked = qr_code_data[:3] + "..." + qr_code_data[-3:] if len(qr_code_data) > 6 else "???"
        print(f" Attempt to enter with unknown code: {masked}")
        
        background_tasks.add_task(save_log_background, None, "Error", f"Unknown code: {masked}")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Unknown QR code."
        )

    # --- Dismissed/Inactive Employee ---
    if getattr(employee, 'dismissed', False) or (hasattr(employee, 'dismissal_date') and employee.dismissal_date is not None):
        print(f" Entry attempt by dismissed employee: {employee.email}")
        
        background_tasks.add_task(save_log_background, employee.id, "Error", "Employee dismissed")
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied (Employee inactive)."
        )
    
    # --- Success ---
    log_message = f"Logged in successfully: {employee.first_name} {employee.last_name}"
    print(f"{log_message}")

    background_tasks.add_task(save_log_background, employee.id, "OK", log_message)
    
    return employee