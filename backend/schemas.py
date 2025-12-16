# backend/schemas.py
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# --- 1. LOGIN  ---
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    admin_name: str  # 

# --- 2. ADMIN INFO  ---
class AdminDisplay(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True) # 

# --- 3. WORKERS TABLE  ---
class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    dismissed: bool = False
    dismissal_date: Optional[date] = None  

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeDisplay(EmployeeBase):
    id: int
    qr_value: Optional[str] = None

    model_config = ConfigDict(from_attributes=True) 
# --- 4. EDIT WORKER  ---
class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    dismissed: Optional[bool] = None
    dismissal_date: Optional[date] = None
    

# --- 5. REPORTS QUERY  ---
class ReportRequest(BaseModel):
    employee_id: Optional[int] = None
    date_from: date
    date_to: date