from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
from database import get_db
from models import Employee, Attendance
from schemas import schemas

router = APIRouter(
    prefix="/employees",
    tags=["employees"]
)

@router.post("/", response_model=schemas.Employee)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = Employee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.get("/", response_model=List[schemas.Employee])
def get_employees(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Query employees with attendance statistics
    employees = db.query(
        Employee,
        func.count(Attendance.id).label('total_attendance'),
        func.sum(case((Attendance.status == 'present', 1), else_=0)).label('present_days')
    ).outerjoin(
        Attendance, 
        Employee.employee_id == Attendance.employee_id
    ).group_by(
        Employee.employee_id
    ).offset(skip).limit(limit).all()
    
    # Format the response
    result = []
    for emp, total_attendance, present_days in employees:
        emp_dict = emp.__dict__
        emp_dict['total_working_days_after_joining'] = total_attendance
        emp_dict['present_days'] = present_days
        emp_dict['attendance_percentage'] = round((present_days / total_attendance * 100), 2) if total_attendance > 0 else 0
        result.append(emp_dict)
    return result

@router.get("/{employee_id}", response_model=schemas.Employee) 
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee