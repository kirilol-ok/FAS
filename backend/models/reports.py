from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum, func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from backend.models.base import LogBase

def now_utc() -> datetime:
    return datetime.utcnow()


def deletion_date() -> datetime:
    return datetime.utcnow() + timedelta(days=180)

class Reports(LogBase):
    __tablename__ = "Reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, index=True, default=now_utc, nullable=False)
    retention_until = Column(DateTime, default=deletion_date, nullable=False)
    employee_id = Column(Integer, index=True)
    status = Column(Enum('OK', 'Error'), index=True)
    denial_reason = Column(String)
