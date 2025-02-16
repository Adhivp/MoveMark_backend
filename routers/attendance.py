from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Attendance
from schemas import schemas
from datetime import date

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"]
)

@router.post("/", response_model=schemas.Attendance)
def create_attendance(attendance: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    db_attendance = Attendance(**attendance.dict())
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance

@router.get("/", response_model=List[schemas.Attendance])
def get_attendance(employee_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all attendance records for a specific employee.
    """
    if employee_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid employee ID")

    attendance_records = db.query(Attendance).filter(Attendance.employee_id == employee_id).all()

    if not attendance_records:
        raise HTTPException(status_code=404, detail="No attendance records found for this employee")

    return attendance_records

@router.get("/employee/{employee_id}", response_model=List[schemas.Attendance])
def get_employee_attendance(
    employee_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    if employee_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid employee ID")

    query = db.query(Attendance).filter(Attendance.employee_id == employee_id)
    
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)
        
    result = query.order_by(Attendance.date.desc()).all()
    if not result:
        raise HTTPException(status_code=404, detail="No attendance records found")
        
    return result

@router.get("/predict/{employee_id}",  description="Predicts future attendance percentage for an employee.")
def predict_employee_attendance(
    employee_id: Optional[int] = None,
    prediction_date: date = Query(..., description="Date to predict attendance for (YYYY-MM-DD)."),
    db: Session = Depends(get_db)
):
    """
    Predicts the attendance percentage for a given employee and date.
    If no employee_id is provided, predicts the average attendance.
    """
    try:
        model = create_prophet_model(employee_id=employee_id, db=db)
        attendance_probability = predict_attendance(model, prediction_date)
        return {"employee_id": employee_id, "date": prediction_date, "predicted_attendance_percentage": round(attendance_probability, 2)}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")