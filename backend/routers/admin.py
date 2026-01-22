import uuid
from datetime import date, datetime, time, timedelta
from typing import List

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     UploadFile, status)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.databases.db import get_postgres_db, get_sqlite_db
from backend.models.admins import Admins
from backend.models.employees import Employees
from backend.models.image_files import ImageFiles
from backend.models.reports import Reports
from backend.schemas import (AdminDisplay, EmployeeCreate, EmployeeDisplay,
                             EmployeeUpdate, LoginRequest, ReportRequest,
                             TokenResponse)
from backend.services.email_service import send_qr_code_email
from backend.services.image_storage_service import ImageStorageService
from backend.services.security import verify_password

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


@router.post("/login", response_model=TokenResponse)
async def login(form_data: LoginRequest, db: AsyncSession = Depends(get_sqlite_db)):
    # Check admin in database
    result = await db.execute(select(Admins).where(Admins.email == form_data.email))
    admin = result.scalars().first()

    # Domain verification
    if not admin or not verify_password(form_data.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "access_token": f"fake-jwt-token-for-{admin.id}",
        "token_type": "bearer",
        "admin_name": admin.first_name,
    }


@router.get("/me", response_model=AdminDisplay)
async def get_current_admin_info(email: str, db: AsyncSession = Depends(get_sqlite_db)):
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
async def get_employee_details(
    employee_id: int, db: AsyncSession = Depends(get_sqlite_db)
):
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    worker = result.scalars().first()
    if not worker:
        raise HTTPException(status_code=404, detail="Employee does not exist")
    return worker


@router.patch("/update_employees/{employee_id}")
async def update_employee(
    employee_id: int,
    update_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_sqlite_db),
):
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    worker = result.scalars().first()
    if not worker:
        raise HTTPException(status_code=404, detail="Employee does not exist")

    # variables to update
    if update_data.first_name:
        worker.first_name = update_data.first_name
    if update_data.last_name:
        worker.last_name = update_data.last_name
    if update_data.email:
        worker.email = update_data.email

    if update_data.expiration_date is not None:
        worker.expiration_date = update_data.expiration_date

    if update_data.dismissed is not None:
        worker.dismissed = update_data.dismissed

        if update_data.dismissed is False:
            worker.dismissal_date = None

    if update_data.dismissal_date is not None:
        worker.dismissal_date = update_data.dismissal_date
        worker.dismissed = True

    await db.commit()
    await db.refresh(worker)
    return worker


from datetime import datetime, time


@router.post("/reports/display_raports")
async def generate_report(
    query_data: ReportRequest,
    db: AsyncSession = Depends(get_postgres_db),
):
    if isinstance(query_data.date_from, datetime):
        start_datetime = query_data.date_from
    else:
        start_datetime = datetime.combine(query_data.date_from, time.min)

    if isinstance(query_data.date_to, datetime):
        end_datetime = query_data.date_to
    else:
        end_datetime = datetime.combine(query_data.date_to, time.max)

    stmt = select(Reports).where(
        Reports.created_at >= start_datetime,
        Reports.created_at <= end_datetime,
    )

    if query_data.employee_ids:
        stmt = stmt.where(Reports.employee_id.in_(query_data.employee_ids))

    elif hasattr(query_data, "employee_id") and query_data.employee_id:
        stmt = stmt.where(Reports.employee_id == query_data.employee_id)

    if hasattr(query_data, "statuses") and query_data.statuses:
        stmt = stmt.where(Reports.status.in_(query_data.statuses))

    elif hasattr(query_data, "status") and query_data.status:
        stmt = stmt.where(Reports.status == query_data.status)

    stmt = stmt.order_by(Reports.created_at.desc())

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return logs


@router.post(
    "/create_employee",
    response_model=EmployeeDisplay,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    employee: EmployeeCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_sqlite_db),
):

    result = await db.execute(
        select(Employees).where(Employees.email == employee.email)
    )
    existing_employee = result.scalars().first()

    final_hire_date = employee.hire_date
    if final_hire_date is None:
        final_hire_date = date.today()

    final_expiration_date = employee.expiration_date
    if final_expiration_date is None:
        final_expiration_date = final_hire_date + timedelta(days=180)

    target_employee = None

    if existing_employee:
        if not existing_employee.dismissed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An employee with this email address already exists and is active.",
            )

        target_employee = existing_employee
        target_employee.hire_date = final_hire_date
        target_employee.expiration_date = final_expiration_date
        target_employee.first_name = employee.first_name
        target_employee.last_name = employee.last_name

        target_employee.dismissed = False
        target_employee.dismissal_date = None

    else:
        target_employee = Employees(
            first_name=employee.first_name,
            last_name=employee.last_name,
            email=employee.email,
            dismissed=False,
            hire_date=final_hire_date,
            expiration_date=final_expiration_date,
        )
        db.add(target_employee)

    new_qr_value = str(uuid.uuid4())
    target_employee.qr_value = new_qr_value

    await db.commit()
    await db.refresh(target_employee)

    background_tasks.add_task(
        send_qr_code_email,
        email_to=target_employee.email,
        qr_data=new_qr_value,
        first_name=target_employee.first_name,
    )

    return target_employee


@router.post("/employees/{employee_id}/dismiss", response_model=EmployeeDisplay)
async def dismiss_employee(
    employee_id: int,
    dismissal_date: date = None,
    db: AsyncSession = Depends(get_sqlite_db),
):
    """
    Dismiss employee
    """
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    worker = result.scalars().first()

    if not worker:
        raise HTTPException(status_code=404, detail="Employee does not exist")

    worker.dismissed = True
    worker.qr_value = None

    if dismissal_date:
        worker.dismissal_date = datetime.combine(dismissal_date, time.min)
    else:
        worker.dismissal_date = datetime.now()

    await db.commit()
    await db.refresh(worker)

    return worker


@router.delete(
    "/delete_employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_sqlite_db)):
    result = await db.execute(select(Employees).where(Employees.id == employee_id))
    employee = result.scalars().first()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee was not found"
        )

    image_id = employee.image_id

    other_refs = 0
    if image_id is not None:
        cnt_res = await db.execute(
            select(func.count())
            .select_from(Employees)
            .where(
                Employees.image_id == image_id,
                Employees.id != employee_id,
            )
        )
        other_refs = cnt_res.scalar_one()

    await db.delete(employee)

    if image_id is not None and other_refs == 0:
        img_res = await db.execute(select(ImageFiles).where(ImageFiles.id == image_id))
        img = img_res.scalars().first()
        if img:
            await db.delete(img)

    await db.commit()
    return None


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
        raise HTTPException(status_code=400, detail="Empty file")

    service = ImageStorageService(db)

    try:
        emp_res = await db.execute(select(Employees).where(Employees.id == employee_id))
        employee = emp_res.scalar_one_or_none()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee does not exist")

        old_image_id = employee.image_id

        new_image = await service.save_image(content, file.filename)

        employee.image_id = new_image.id
        await db.flush()

        if old_image_id is not None and old_image_id != new_image.id:
            cnt_res = await db.execute(
                select(func.count())
                .select_from(Employees)
                .where(Employees.image_id == old_image_id)
            )
            refs = cnt_res.scalar_one()

            if refs == 0:
                old_img_res = await db.execute(
                    select(ImageFiles).where(ImageFiles.id == old_image_id)
                )
                old_img = old_img_res.scalar_one_or_none()
                if old_img:
                    await db.delete(old_img)

        await db.commit()
        return {
            "status": "success",
            "employee_id": employee_id,
            "image_id": new_image.id,
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {e}")
