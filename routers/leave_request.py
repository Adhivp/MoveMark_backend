from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import LeaveRequest
from schemas import schemas
from datetime import date

router = APIRouter(
    prefix="/leave_requests",
    tags=["leave_requests"]
)

@router.post("/", response_model=schemas.LeaveRequest)
def create_leave_request(leave_request: schemas.LeaveRequestCreate, db: Session = Depends(get_db)):
    db_leave_request = LeaveRequest(**leave_request.dict())
    db.add(db_leave_request)
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

@router.get("/get", response_model=List[schemas.LeaveRequest])
def get_leave_requests(employee_id: Optional[int] = None, db: Session = Depends(get_db)):
    if employee_id is not None:
        leave_requests = db.query(LeaveRequest).filter(LeaveRequest.employee_id == employee_id).all()
        if not leave_requests:
            raise HTTPException(status_code=404, detail="No leave requests found for this employee")
        return leave_requests
    else:
        leave_requests = db.query(LeaveRequest).all()
        return leave_requests