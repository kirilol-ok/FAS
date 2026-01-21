"""
Employee lifecycle management utilities.

This module introduces a helper function to automatically dismiss
employees whose contracts have expired.  The function respects
unlimited (open‑ended) contracts by ignoring employees with a
``None`` value in their ``dismissal_date`` field.  It updates the
``dismissed`` flag to ``True`` for employees whose dismissal date is
in the past relative to the provided time.

The function can be called periodically (e.g., via a cron job or
background task) to keep the active employee roster up to date.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.employees import Employees


def dismiss_expired_employees(
    session: Session, current_time: Optional[datetime] = None
) -> int:
    """
    Mark employees whose dismissal date has passed as dismissed.

    Employees with a ``None`` dismissal date (i.e., unlimited contracts)
    remain unaffected.  The function commits all changes within the
    session and returns the number of employees updated.

    Parameters
    ----------
    session : Session
        An active SQLAlchemy session bound to the appropriate database.
    current_time : datetime, optional
        The reference time for determining whether a contract has
        expired.  Defaults to the current UTC time.

    Returns
    -------
    int
        The count of employees that were marked as dismissed.
    """
    if current_time is None:
        current_time = datetime.now()
    # Select employees whose dismissal_date is set and not yet marked dismissed
    result = session.execute(
        select(Employees).where(
            Employees.dismissal_date != None,  # noqa: E711
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