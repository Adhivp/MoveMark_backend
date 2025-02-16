from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class EmployeeBase(BaseModel):
    employee_name: str
    email: str
    department: str

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    employee_id: int
    created_at: datetime
    total_working_days_after_joining: Optional[int] = None
    present_days: Optional[int] = None
    attendance_percentage: Optional[float] = None

    class Config:
        from_attributes = True

class AttendanceBase(BaseModel):
    employee_id: int
    date: date
    checkin_time: Optional[datetime] = None
    checkout_time: Optional[datetime] = None
    status: str

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int

    class Config:
        orm_mode = True

class LeaveRequestBase(BaseModel):
    employee_id: int
    date_to_be_on_leave: date
    is_half_day: bool = False
    leave_period: Optional[str] = None
    reason: str

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequest(LeaveRequestBase):
    id: int

    class Config:
        orm_mode = True