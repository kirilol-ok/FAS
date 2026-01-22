from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.employees import Employees


def dismiss_expired_employees(
    session: Session, current_time: Optional[datetime] = None
) -> int:
    if current_time is None:
        current_time = datetime.now()
    result = session.execute(
        select(Employees).where(
            Employees.dismissal_date != None,
            Employees.dismissal_date <= current_time,
            Employees.dismissed == False,
        )
    )
    employees_to_update = result.scalars().all()
    for employee in employees_to_update:
        employee.dismissed = True
    if employees_to_update:
        session.commit()
    return len(employees_to_update)
