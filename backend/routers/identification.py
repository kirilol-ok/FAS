# from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
#                      UploadFile, status)
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from backend.databases.db import SQLiteSessionLocal, get_postgres_db
# from backend.models.employees import Employees
# from backend.models.reports import Reports
# from backend.schemas import EmployeeDisplay
# from backend.services.qr_service import decode_qr_from_bytes

# router = APIRouter(
#     prefix="/identify",
#     tags=["Identification (Kiosk/Camera)"]
# )


# def save_log_background(employee_id: int | None, status: str, reason: str | None):
#     """write log in another session to dont stop the server"""
#     db = SQLiteSessionLocal()
#     try:
#         report = Reports(
#             employee_id=employee_id,
#             status=status,
#             denial_reason=reason
#         )
#         db.add(report)
#         db.commit()
#         print(f" [BACKGROUND] Zapisano log: {status} (ID: {report.id})")
#     except Exception as e:
#         print(f" [BACKGROUND] Błąd zapisu: {e}")
#     finally:
#         db.close()

# # --- ENDPOINT ---
# @router.post("/qr", response_model=EmployeeDisplay)
# async def identify_user_by_qr(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...),
#     db: AsyncSession = Depends(get_postgres_db)
# ):
    
    
#     content = await file.read()
#     qr_code_data = decode_qr_from_bytes(content)

#     if not qr_code_data:
#         raise HTTPException(status_code=400, detail="Brak kodu QR")

#     result = await db.execute(select(Employees).where(Employees.qr_value == qr_code_data))
#     employee = result.scalars().first()

#     # --- WE dont know the code ---
#     if not employee:
#         masked = qr_code_data[:8] + "..."
#         print(f"⚠️ Próba wejścia nieznanym kodem: {masked}")
        
       
#         save_log_background(None, "Error", f"Nieznany kod: {masked}")
        
#         raise HTTPException(status_code=404, detail="Kod QR nieznany.")

#     # --- dissmised employee---
#     if employee.dismissed:
#         print(f"⛔ Próba wejścia zwolnionego: {employee.email}")
        
        
#         save_log_background(employee.id, "Error", "Pracownik zwolniony")
        
#         raise HTTPException(status_code=403, detail="Pracownik zwolniony.")
    
#     # ---autorized access -- secuess ---
    
#     # new log
#     log_message = f"Zalogowano pomyślnie: {employee.first_name} {employee.last_name}"

#     # log messege is third argument
#     background_tasks.add_task(save_log_background, employee.id, "OK", log_message)
    
#     print(f"✅ Zalogowano wejście: {employee.first_name} {employee.last_name}")
    
#     return employee