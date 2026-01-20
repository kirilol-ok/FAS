# backend/routers/admin.py
import uuid
from datetime import date, datetime, time
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, File, UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.image_files import ImageFiles
from backend.databases.db import get_postgres_db, get_sqlite_db
from backend.services.email_service import send_qr_code_email
from backend.services.image_storage_service import ImageStorageService
from backend.models.admins import Admins
from backend.models.employees import Employees
from backend.models.reports import Reports
from backend.schemas import (
    AdminDisplay,
    EmployeeCreate,
    EmployeeDisplay,
    EmployeeUpdate,
    LoginRequest,
    ReportRequest,
    TokenResponse,
)

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
    

    await db.commit()
    await db.refresh(worker)
    return worker





@router.post("/reports/display_raports")
async def generate_report(
    query_data: ReportRequest,
    db: AsyncSession = Depends(get_postgres_db),
):

    # 1. datetime conversion
    start_datetime = datetime.combine(query_data.date_from, time.min)
    end_datetime = datetime.combine(query_data.date_to, time.max)

    # 2. base stmt
    stmt = select(Reports).where(
        Reports.created_at >= start_datetime,
        Reports.created_at <= end_datetime,
    )

    # 3. filter for chosen employee
    if query_data.employee_id:
        stmt = stmt.where(Reports.employee_id == query_data.employee_id)

    # 4. data sort - new is up
    stmt = stmt.order_by(Reports.created_at.desc())

    result = await db.execute(stmt)
    logs = result.scalars().all()

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




@router.delete("/delete_employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_sqlite_db)
):
    # 1) find employee
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    employee = result.scalars().first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pracownik nie został znaleziony"
        )

    image_id = employee.image_id

    # 2) check if someone else references this image (before we delete the employee)
    other_refs = 0
    if image_id is not None:
        cnt_res = await db.execute(
            select(func.count()).select_from(Employees).where(
                Employees.image_id == image_id,
                Employees.id != employee_id,
            )
        )
        other_refs = cnt_res.scalar_one()

    # 3) delete employee
    await db.delete(employee)

    # 4) delete image record only if it is not referenced by anyone else
    if image_id is not None and other_refs == 0:
        img_res = await db.execute(select(ImageFiles).where(ImageFiles.id == image_id))
        img = img_res.scalars().first()
        if img:
            await db.delete(img)

    await db.commit()
    return None


@router.patch("/employees/{employee_id}", response_model=EmployeeDisplay)
async def update_employee_alias(
    employee_id: int,
    update_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_sqlite_db)
):
    return await update_employee(employee_id, update_data, db)

@router.post("/reports/generate")
async def generate_report_alias(
    query_data: ReportRequest,
    db: AsyncSession = Depends(get_postgres_db),
):
    return await generate_report(query_data, db)

@router.post("/employees/{employee_id}/upload_photo")
async def upload_employee_photo(
    employee_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_sqlite_db),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Pusty plik")

    service = ImageStorageService(db)

    try:
        # 1) Find employee
        emp_res = await db.execute(select(Employees).where(Employees.id == employee_id))
        employee = emp_res.scalar_one_or_none()
        if not employee:
            raise HTTPException(status_code=404, detail="Pracownik nie istnieje")

        old_image_id = employee.image_id

        # 2) Save new embedding (dedup by hash)
        new_image = await service.save_image(content, file.filename)

        # 3) Assign new image to employee
        employee.image_id = new_image.id
        await db.flush()  # важно: чтобы обновление employee.image_id попало в транзакцию до подсчетов

        # 4) Cleanup old image if it is no longer referenced and not the same as new one
        if old_image_id is not None and old_image_id != new_image.id:
            cnt_res = await db.execute(
                select(func.count()).select_from(Employees).where(Employees.image_id == old_image_id)
            )
            refs = cnt_res.scalar_one()

            if refs == 0:
                old_img_res = await db.execute(select(ImageFiles).where(ImageFiles.id == old_image_id))
                old_img = old_img_res.scalar_one_or_none()
                if old_img:
                    await db.delete(old_img)

        await db.commit()
        return {"status": "success", "employee_id": employee_id, "image_id": new_image.id}

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Błąd: {e}")
