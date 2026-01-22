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
    expiration_date: Optional[date] = None
    hire_date: datetime
    

class EmployeeCreate(EmployeeBase):
    first_name: str
    last_name: str
    email: EmailStr
    hire_date: datetime     # <--- DODANE (Wymagane)
    expiration_date: Optional[datetime]

class EmployeeDisplay(EmployeeBase):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    dismissed: bool
    hire_date: date      # <--- DODANE
    expiration_date: Optional[date]

    model_config = ConfigDict(from_attributes=True) 
# --- 4. EDIT WORKER  ---
class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    dismissed: Optional[bool] = None
    dismissal_date: Optional[date] = None
    expiration_date: Optional[date] = None
    

# --- 5. REPORTS QUERY  ---
class ReportRequest(BaseModel):
    employee_ids: Optional[List[str]] = None  
    statuses: Optional[List[str]] = None      
    date_from: date
    date_to: date