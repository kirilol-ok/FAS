from datetime import datetime, timedelta

from sqlalchemy import (Column, DateTime, Enum, ForeignKey, Integer, String,
                        func)
from sqlalchemy.orm import relationship

from backend.models.base import LogBase


def now_local() -> datetime:
    return datetime.now()


def deletion_date() -> datetime:
    return datetime.now()


class Reports(LogBase):
    __tablename__ = "Reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, index=True, default=now_local, nullable=False)
    retention_until = Column(DateTime, default=deletion_date, nullable=False)
    employee_id = Column(Integer, index=True)
    status = Column(Enum("OK", "Error", name="report_status"), index=True)
    denial_reason = Column(String)
