# backend/routers/admin.py
import uuid
from datetime import date, datetime, time
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.databases.db import get_postgres_db, get_sqlite_db
from backend.email_utils import send_qr_code_email
from backend.models.admins import Admins
from backend.models.employees import Employees
from backend.models.reports import Reports
from backend.schemas import (AdminDisplay, EmployeeCreate, EmployeeDisplay,
                             EmployeeUpdate, LoginRequest, ReportRequest,
                             TokenResponse)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Panel"]
)


@router.post("/login", response_model=TokenResponse)
async def login(form_data: LoginRequest, db: AsyncSession = Depends(get_sqlite_db)):
    # hceck admin in database
    result = await db.execute(select(Admins).where(Admins.email == form_data.email))
    admin = result.scalars().first()

    # dmian veryfication
    if not admin or admin.password != form_data.password:
        raise HTTPException(status_code=401, detail="Nieprawidłowy login lub hasło")

    #here we need to do something with this token
    return {
        "access_token": f"fake-jwt-token-for-{admin.id}",
        "token_type": "bearer",
        "admin_name": admin.first_name
    }




@router.get("/me", response_model=AdminDisplay)
async def get_current_admin_info(email: str, db: AsyncSession = Depends(get_sqlite_db)):
    # W prawdziwej aplikacji email bierzemy z tokena JWT, tutaj symulujemy parametrem
    result = await db.execute(select(Admins).where(Admins.email == email))
    admin = result.scalars().first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return admin





@router.get("/all_employees", response_model=List[EmployeeDisplay])
async def get_workers_table(db: AsyncSession = Depends(get_sqlite_db)):
    result = await db.execute(select(Employees))
    workers = result.scalars().all()
    return workers






@router.get("/employees/{employee_id}", response_model=EmployeeDisplay)
async def get_employee_details(employee_id: int, db: AsyncSession = Depends(get_sqlite_db)):
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    worker = result.scalars().first()
    if not worker:
        raise HTTPException(status_code=404, detail="Pracownik nie istnieje")
    return worker





@router.patch("/update_employees/{employee_id}")
async def update_employee(
    employee_id: int, 
    update_data: EmployeeUpdate, 
    db: AsyncSession = Depends(get_sqlite_db)
):
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    worker = result.scalars().first()
    if not worker:
        raise HTTPException(status_code=404, detail="Pracownik nie istnieje")

    # variables to update
    if update_data.first_name:
        worker.first_name = update_data.first_name
    if update_data.last_name:
        worker.last_name = update_data.last_name
    if update_data.email:
        worker.email = update_data.email
    if update_data.dismissal_date is not None:
        worker.dismissal_date = update_data.dismissal_date
    if update_data.dismissed is not None:    
        worker.dismissed = update_data.dismissed  
    if update_data.dismissal_date is not None:
        worker.dismissal_date = update_data.dismissal_date
    

    await db.commit()
    await db.refresh(worker)
    return worker





@router.post("/reports/display_raports")
def generate_report(
    query_data: ReportRequest,
    db: AsyncSession = Depends(get_postgres_db)
):
    """
    Pobiera raporty wejść/wyjść.
    Naprawiono: Uwzględnia pełny zakres godzin (od początku do końca dnia).
    """
    
    # 1. datatime conversion
    start_datetime = datetime.combine(query_data.date_from, time.min)
    
    # end   -> 2025-11-25 23:59:59.999999
    end_datetime = datetime.combine(query_data.date_to, time.max)

    # 2. using full datatime in query
    query = db.query(Reports).filter(
        Reports.created_at >= start_datetime,
        Reports.created_at <= end_datetime
    )

    # 3. filter for chosen employee
    if query_data.employee_id:
        query = query.filter(Reports.employee_id == query_data.employee_id)

    # 4. data sort - new is up
    query = query.order_by(Reports.created_at.desc())

    logs = query.all()
    
    return logs





@router.post("/create_employee", response_model=EmployeeDisplay, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee: EmployeeCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_sqlite_db)
):
    """
    we create new employee or old emplayee (change dissmised - true on false) and send new qr
    """
    # 1. check if email exist
    result = await db.execute(select(Employees).where(Employees.email == employee.email))
    existing_employee = result.scalars().first()

    target_employee = None
    #check if is reactivation is need
    is_reactivation = False

    # employee exist
    if existing_employee:
        # exist and still working  -- error
        if not existing_employee.dismissed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Pracownik z tym adresem email już istnieje i jest aktywny."
            )
        
        # exist and dissmised
        target_employee = existing_employee
        is_reactivation = True
        
        # data actualization for email
        target_employee.first_name = employee.first_name
        target_employee.last_name = employee.last_name
        
        # change dissmisal parameters
        target_employee.dismissed = False
        target_employee.dismissal_date = None

    # another case -- new employee
    else:
        target_employee = Employees(
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            dismissed=False
        )
        db.add(target_employee)

    # 2. new qr code generation
    new_qr_value = str(uuid.uuid4())
    target_employee.qr_value = new_qr_value

    # 3.commit changes to database
    await db.commit()
    await db.refresh(target_employee)

    # 4. send emial with qr code
    background_tasks.add_task(
        send_qr_code_email, 
        email_to=target_employee.email, 
        qr_data=new_qr_value,
        first_name=target_employee.first_name
    )

    return target_employee



# --- 7) POST: Dismiss Employee
@router.post("/employees/{employee_id}/dismiss", response_model=EmployeeDisplay)
async def dismiss_employee(
    employee_id: int,
    dismissal_date: date = None, 
    db: AsyncSession = Depends(get_sqlite_db)
):
    """
    dissmiss employee
    """
    # 1. Pobierz pracownika
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    worker = result.scalars().first()
    
    if not worker:
        raise HTTPException(status_code=404, detail="Pracownik nie istnieje")

    # 2. dissmisal parametrs set
    worker.dismissed = True
    worker.qr_value = None
    
    # if frontend hevent send data set current date
    if dismissal_date:
        worker.dismissal_date = dismissal_date
    else:
        worker.dismissal_date = date.today()

    # 3. commit changes
    await db.commit()
    await db.refresh(worker)

    return worker




# --- 8) DELETE: Destroy Employee 
@router.delete("/delete_employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_sqlite_db)
):
    """
    delete employee -- can't control z
    """
    # 1. Szukamy pracownika
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    employee = result.scalars().first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Pracownik nie został znaleziony"
        )

    # 2. delete employee from database
    await db.delete(employee)
    await db.commit()
    

    return None