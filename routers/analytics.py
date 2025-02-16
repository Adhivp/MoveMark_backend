from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from typing import List, Dict
from database import get_db
from models import Employee, Attendance, LeaveRequest
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

class AnomalyLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AnomalyType:
    LATE_CHECKIN = "Late Check-in"
    EARLY_CHECKOUT = "Early Check-out"
    LOW_ATTENDANCE = "Low Attendance"
    IRREGULAR_PATTERN = "Irregular Pattern"

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

class AttendanceFeatures(BaseModel):
    checkin_times: List[float]  # Minutes since midnight
    checkout_times: List[float]
    attendance_rate: float

def extract_features(employee_data, db: Session):
    # Convert times to minutes since midnight for numerical analysis
    checkins = [t.hour * 60 + t.minute if t else 0 for t in employee_data['checkin_time']]
    checkouts = [t.hour * 60 + t.minute if t else 0 for t in employee_data['checkout_time']]
    
    # Calculate attendance rate
    attendance_rate = len([s for s in employee_data['status'] if s == 'present']) / len(employee_data['status'])
    
    return AttendanceFeatures(
        checkin_times=checkins,
        checkout_times=checkouts,
        attendance_rate=attendance_rate
    )

@router.get("/anomalies", response_model=List[AttendanceAnomaly])
def detect_anomalies(
    anomaly_threshold: float = Query(
        default=0.5,
        ge=0.0,  # least strict (more anomalies)
        le=1.0,  # most strict (fewer anomalies)
        description="Anomaly detection threshold (0.0 to 1.0). Higher values are more strict (fewer anomalies), lower values detect more anomalies.",
    ),
    db: Session = Depends(get_db)
):
    anomalies = []
    
    # Get all attendance data
    attendance_data = pd.read_sql(
        db.query(Attendance).statement,
        db.bind
    )
    
    for employee_id, emp_data in attendance_data.groupby('employee_id'):
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        
        features = extract_features(emp_data, db)
        
        # Prepare data for Isolation Forest
        X = np.array([
            features.checkin_times,
            features.checkout_times,
            [features.attendance_rate] * len(features.checkin_times)
        ]).T
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        clf = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        clf.fit(X_scaled)
        anomaly_scores = clf.score_samples(X_scaled)
        
        # Convert the threshold from 0-1 range to isolation forest score range
        # Isolation Forest scores are typically between -0.5 and 0.5
        adjusted_threshold = -1 * (1 - anomaly_threshold)  # Convert 0-1 to 0 to -1
        
        # Use adjusted threshold for detection
        for idx, score in enumerate(anomaly_scores):
            if score < adjusted_threshold:
                date = emp_data.iloc[idx]['date']
                checkin = emp_data.iloc[idx]['checkin_time']
                checkout = emp_data.iloc[idx]['checkout_time']
                
                # Determine anomaly type based on patterns
                if checkin and checkin.hour >= 9:
                    anomaly_type = AnomalyType.LATE_CHECKIN
                elif checkout and checkout.hour <= 16:
                    anomaly_type = AnomalyType.EARLY_CHECKOUT
                elif features.attendance_rate < 0.8:
                    anomaly_type = AnomalyType.LOW_ATTENDANCE
                else:
                    anomaly_type = AnomalyType.IRREGULAR_PATTERN
                
                # Dynamic severity based on normalized score difference
                score_diff = (adjusted_threshold - score) / 2  # Normalize to 0-1 range
                severity = (
                    AnomalyLevel.HIGH if score_diff > 0.5 else
                    AnomalyLevel.MEDIUM if score_diff > 0.25 else
                    AnomalyLevel.LOW
                )
                
                description = f"Unusual attendance pattern detected on {date} "
                description += f"(Anomaly Score: {score:.3f}). "
                if checkin and checkin.hour >= 9:
                    description += "Late check-in. "
                if checkout and checkout.hour <= 16:
                    description += "Early checkout. "
                if features.attendance_rate < 0.8:
                    description += "Low attendance rate. "
                
                anomalies.append(AttendanceAnomaly(
                    employee_id=employee_id,
                    employee_name=employee.employee_name,
                    anomaly_type=anomaly_type,
                    description=description,
                    severity=severity,
                    detected_date=datetime.now(),
                    anomaly_score=abs(score)
                ))
    
    return sorted(anomalies, key=lambda x: x.anomaly_score, reverse=True)