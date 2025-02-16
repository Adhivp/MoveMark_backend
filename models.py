from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    employee_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    department = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    attendances = relationship("Attendance", back_populates="employee")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"))
    date = Column(Date, nullable=False)
    checkin_time = Column(DateTime)
    checkout_time = Column(DateTime)
    status = Column(String(20))
    
    employee = relationship("Employee", back_populates="attendances")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"))
    date_to_be_on_leave = Column(Date, nullable=False)
    is_half_day = Column(Boolean, default=False)
    leave_period = Column(String(20), nullable=True)  # "forenoon" or "afternoon" if is_half_day is True
    reason = Column(String(200))

    employee = relationship("Employee")