from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Dict
from database import get_db
from models import Employee, Attendance, LeaveRequest
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

class AnomalyLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AttendanceAnomaly(BaseModel):
    employee_id: int
    employee_name: str
    anomaly_type: str
    description: str
    severity: str
    detected_date: Optional[datetime]
    anomaly_score: float

    class Config:
        orm_mode = True

@router.get("/anomalies", response_model=List[AttendanceAnomaly])
def detect_anomalies(db: Session = Depends(get_db)):
    anomalies = []
    
    # Get all employees
    employees = db.query(Employee).all()
    
    for employee in employees:
        # 1. Late Check-in Pattern Analysis
        late_checkins = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == employee.employee_id,
                Attendance.checkin_time > datetime.strptime('09:30:00', '%H:%M:%S').time()
            )
        ).count()
        
        if late_checkins > 5:
            severity = AnomalyLevel.HIGH if late_checkins > 10 else AnomalyLevel.MEDIUM
            anomalies.append(AttendanceAnomaly(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                anomaly_type="Frequent Late Check-ins",
                description=f"Employee has {late_checkins} late check-ins",
                severity=severity,
                detected_date=datetime.now(),
                anomaly_score=min(late_checkins / 20, 1.0)
            ))

        # 2. Absence Without Leave Request
        absences = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == employee.employee_id,
                Attendance.status == "absent"
            )
        ).all()
        
        for absence in absences:
            leave_request = db.query(LeaveRequest).filter(
                and_(
                    LeaveRequest.employee_id == employee.employee_id,
                    LeaveRequest.date_to_be_on_leave == absence.date
                )
            ).first()
            
            if not leave_request:
                anomalies.append(AttendanceAnomaly(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    anomaly_type="Unauthorized Absence",
                    description=f"Absence without leave request on {absence.date}",
                    severity=AnomalyLevel.HIGH,
                    detected_date=datetime.now(),
                    anomaly_score=1.0
                ))

        # 3. Early Checkout Pattern
        early_checkouts = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == employee.employee_id,
                Attendance.checkout_time < datetime.strptime('17:00:00', '%H:%M:%S').time()
            )
        ).count()
        
        if early_checkouts > 5:
            severity = AnomalyLevel.MEDIUM if early_checkouts > 8 else AnomalyLevel.LOW
            anomalies.append(AttendanceAnomaly(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                anomaly_type="Frequent Early Checkouts",
                description=f"Employee has {early_checkouts} early checkouts",
                severity=severity,
                detected_date=datetime.now(),
                anomaly_score=early_checkouts / 15
            ))

        # 4. Attendance Pattern Changes
        last_month = datetime.now() - timedelta(days=30)
        attendance_pattern = db.query(
            func.avg(case((Attendance.status == 'present', 1), else_=0))
        ).filter(
            and_(
                Attendance.employee_id == employee.employee_id,
                Attendance.date >= last_month
            )
        ).scalar()

        if attendance_pattern and attendance_pattern < 0.8: 
            anomalies.append(AttendanceAnomaly(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                anomaly_type="Low Attendance Pattern",
                description=f"Attendance rate of {attendance_pattern*100:.1f}% in last 30 days",
                severity=AnomalyLevel.MEDIUM,
                detected_date=datetime.now(),
                anomaly_score=1 - attendance_pattern
            ))

    return sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)