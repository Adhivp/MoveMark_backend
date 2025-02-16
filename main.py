from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict

# Local imports
from database import engine, get_db
from models import Base, Employee, Attendance
from routers import employee, attendance , leave_request , analytics
# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MoveMark API",
    description="Attendance Management System API with Anomaly Detection",
    version="1.0.0"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="MoveMark API",
        version="1.0.0",
        description="Attendance Management System API with Anomaly Detection",
        routes=app.routes,
    )
    
    # Customize the schema for better Swagger UI display
    for path in openapi_schema["paths"]:
        if "/anomalies" in path:
            openapi_schema["paths"][path]["get"]["parameters"][0]["x-slider"] = True
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(employee.router)
app.include_router(attendance.router)
app.include_router(leave_request.router)
app.include_router(analytics.router) 

@app.get("/")
def read_root():
    return {"message": "Welcome to Employee Attendance System"}

@app.get("/attendance-stats")
def get_attendance_stats(
    target_date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    if target_date:
        start_date = target_date
        end_date = target_date
    
    if not start_date:
        start_date = date(2024, 1, 1)
    if not end_date:
        end_date = date(2024, 12, 31)

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date")

    base_query = db.query(Attendance).filter(
        Attendance.date.between(start_date, end_date),
        func.extract('dow', Attendance.date).notin_([0, 6])
    )

    total_records = base_query.count()
    present_records = base_query.filter(Attendance.status == "present").count()
    absent_records = total_records - present_records

    dept_stats = db.query(
        Employee.department,
        func.count(Attendance.id).label('total'),
        func.sum(
            case(
                (Attendance.status == 'present', 1),
                else_=0
            )
        ).label('present')
    ).join(Employee).filter(
        Attendance.date.between(start_date, end_date),
        func.extract('dow', Attendance.date).notin_([0, 6])
    ).group_by(Employee.department).all()

    date_diff = (end_date - start_date).days
    if target_date:  # Single date - show minute-wise trend for check-ins
        trend_query = db.query(
            func.strftime('%H:%M', Attendance.checkin_time).label('minute'),
            func.count().label('total'),
            func.sum(
                case(
                    (Attendance.status == 'present', 1),
                    else_=0
                )
            ).label('present')
        ).filter(
            Attendance.date == target_date,
            func.extract('dow', Attendance.date).notin_([0, 6]),
            func.strftime('%H:%M', Attendance.checkin_time).between('08:00', '10:00')
        ).group_by('minute')
        
        # Create a dictionary with 5-minute intervals
        intervals = {}
        current_time = datetime.strptime('08:00', '%H:%M')
        end_time = datetime.strptime('10:00', '%H:%M')
        
        while current_time <= end_time:
            intervals[current_time.strftime('%H:%M')] = 0
            current_time += timedelta(minutes=5)

        # Fill in the actual data with check-in times
        raw_data = {
            minute: total
            for minute, total, _ in trend_query.all()
        }

        # Aggregate into 5-minute intervals
        trend_data = {}
        for interval_start in intervals.keys():
            interval_end = (datetime.strptime(interval_start, '%H:%M') + timedelta(minutes=5)).strftime('%H:%M')
            count = sum(
                count
                for time, count in raw_data.items()
                if interval_start <= time < interval_end
            )
            trend_data[interval_start] = count

    elif date_diff > 30:  # Monthly trend - existing code
        trend_query = db.query(
            func.strftime('%Y-%m', Attendance.date).label('month'),
            func.count().label('total'),
            func.sum(
                case(
                    (Attendance.status == 'present', 1),
                    else_=0
                )
            ).label('present')
        ).filter(
            Attendance.date.between(start_date, end_date),
            func.extract('dow', Attendance.date).notin_([0, 6])
        ).group_by('month')
        trend_data = {
            month: round((present / total * 100), 2) if total > 0 else 0
            for month, total, present in trend_query.all()
        }
    else: 
        trend_query = db.query(
            Attendance.date,
            func.count().label('total'),
            func.sum(
                case(
                    (Attendance.status == 'present', 1),
                    else_=0
                )
            ).label('present')
        ).filter(
            Attendance.date.between(start_date, end_date),
            func.extract('dow', Attendance.date).notin_([0, 6])
        ).group_by(Attendance.date)
        trend_data = {
            date.strftime("%Y-%m-%d"): round((present / total * 100), 2) if total > 0 else 0
            for date, total, present in trend_query.all()
        }

    # Replace the top performers section with early comers for single date
    early_comers_data = []
    if target_date:
        early_comers = db.query(
            Employee.employee_name,
            Attendance.checkin_time
        ).join(Employee).filter(
            Attendance.date == target_date,
            Attendance.status == 'present',
            Attendance.checkin_time.isnot(None)  # Only include records with valid check-in times
        ).order_by(
            Attendance.checkin_time  # Sort by check-in time ascending
        ).limit(5).all()

        early_comers_data = [
            {
                "name": name,
                "check_in_time": checkin_time.strftime('%H:%M') if checkin_time else None
            }
            for name, checkin_time in early_comers
        ]
    else:
        # Existing top performers code for date ranges
        top_performers = db.query(
            Employee.employee_name,
            func.count().label('total_days'),
            func.sum(
                case(
                    (Attendance.status == 'present', 1),
                    else_=0
                )
            ).label('present_days')
        ).join(Attendance).filter(
            Attendance.date.between(start_date, end_date),
            func.extract('dow', Attendance.date).notin_([0, 6])
        ).group_by(
            Employee.employee_id
        ).having(
            func.count() > 0
        ).order_by(
            (func.sum(
                case(
                    (Attendance.status == 'present', 1),
                    else_=0
                )
            ) * 100 / func.count()).desc()
        ).limit(5).all()

        top_performers_data = [
            {
                "name": name,
                "percentage": round((present_days / total_days * 100), 2) if total_days > 0 else 0
            }
            for name, total_days, present_days in top_performers
        ]

    return {
        "overall_stats": {
            "percentage": round((present_records / total_records * 100), 2) if total_records > 0 else 0,
            "present": f"{present_records}/{total_records}",
            "absent": f"{absent_records}/{total_records}"
        },
        "department_stats": {
            dept: round((present / total * 100), 2) if total > 0 else 0
            for dept, total, present in dept_stats
        },
        "attendance_trend": trend_data,
        "early_comers": early_comers_data if target_date else [],  # Return early comers for single date
        "top_performers": [] if target_date else top_performers_data,  # Return top performers for date range
        "date_info": {
            "start_date": str(start_date),
            "end_date": str(end_date),
            "is_single_date": target_date is not None
        }
    }