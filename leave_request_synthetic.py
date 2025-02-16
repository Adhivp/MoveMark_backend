import os
import sys
import random
from datetime import date, timedelta, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Employee, Attendance, LeaveRequest 
from config import settings

# Database URL
DATABASE_URL = settings.DATABASE_URL

# Create engine and session
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_random_reason():
    reasons = [
        "Personal appointment",
        "Feeling unwell",
        "Family responsibility",
        "Home maintenance",
        "Car maintenance",
        "Unexpected circumstance",
        "Medical checkup",
        "Dental appointment",
        "Child's school event",
        "Parent-teacher meeting",
        "Moving to new residence",
        "Religious observance",
        "Family wedding",
        "Funeral attendance",
        "Emergency home repairs",
        "Visa appointment",
        "Legal proceedings",
        "Professional development course",
        "Certification exam",
        "Family medical emergency",
        "Mental health day",
        "Household emergency",
        "Vehicle breakdown",
        "Pet emergency",
        "Plumbing issues at home",
        "Electrical repairs",
        "Internet installation",
        "Appliance repair service",
        "Bank appointment",
        "Insurance claim process",
        "Court appearance",
        "Immigration matters",
        "Family reunion",
        "Child care emergency",
        "Elder care responsibility",
        "Home inspection",
        "Property closing",
        "Tax consultation",
        "Medical procedure",
        "Physical therapy",
        "Specialist consultation",
        "Eye examination",
        "Passport renewal",
        "Driver's license renewal",
        "Professional certification",
        "Training workshop",
        "Family medical care",
        "Community service",
        "Volunteer work",
        "Blood donation",
        "Jury duty",
        "Military service",
        "Weather emergency",
        "Travel delay",
        "Public transport disruption",
        "Home delivery wait",
        "Security system installation",
        "HVAC maintenance",
        "Roof repairs",
        "Window replacement",
        "Pest control service",
        "Carpet cleaning",
        "Moving assistance",
        "Professional development",
        "Career counseling",
        "Job interview",
        "Family counseling",
        "Marriage counseling",
        "Grief counseling",
        "Physical examination",
        "Laboratory tests",
        "X-ray/imaging",
        "Dental surgery",
        "Orthodontist visit",
        "Chiropractor appointment",
        "Physiotherapy session",
        "Mental health counseling",
        "Vaccination appointment",
        "Health screening",
        "Wellness checkup",
        "Family emergency",
        "Personal emergency",
        "Vehicle servicing",
        "House painting",
        "Furniture delivery",
        "Appliance delivery",
        "Cable/internet setup",
        "Security inspection",
        "Fire alarm installation",
        "Tree removal service",
        "Landscaping work",
        "Pool maintenance",
        "Fence repair",
        "Driveway maintenance",
        "Garage door repair",
        "Lock replacement",
        "Window cleaning",
        "Gutter cleaning",
        "Solar panel installation",
        "Home office setup",
        "Computer repairs",
        "Phone repairs",
        "Appliance maintenance",
        "Garden maintenance",
        "Family illness",
        "Personal illness",
        "Stress management",
        "Emergency dental work",
        "School emergency",
        "Child's medical appointment",
        "Parent's medical care",
        "Spouse's medical care"
    ]
    return random.choice(reasons)

def generate_synthetic_leave_requests(db):
    absent_attendances = db.query(Attendance).filter(Attendance.status == "leave").all()
    print(f"Found {len(absent_attendances)} absent attendances")

    created_count = 0
    for attendance in absent_attendances:
        # Check if leave request already exists for this date and employee
        existing_request = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == attendance.employee_id,
            LeaveRequest.date_to_be_on_leave == attendance.date
        ).first()
        
        if existing_request:
            continue

        is_half_day = random.choice([True, False])
        leave_period = random.choice(["forenoon", "afternoon"]) if is_half_day else None
        
        leave_request = LeaveRequest(
            employee_id=attendance.employee_id,
            date_to_be_on_leave=attendance.date,
            is_half_day=is_half_day,
            leave_period=leave_period,
            reason=get_random_reason()
        )
        db.add(leave_request)
        created_count += 1

        # Commit in smaller batches to prevent memory issues
        if created_count % 100 == 0:
            db.commit()

    db.commit()
    print(f"Created {created_count} new leave requests")

def main():
    db = SessionLocal()
    try:
        # Verify database connection
        try:
            db.query(Employee).first()
            print("Database connection successful")
        except Exception as e:
            print(f"Database connection failed: {e}")
            return

        generate_synthetic_leave_requests(db)
        print("Synthetic leave requests generation completed")
        
        # Verify the data was inserted
        count = db.query(LeaveRequest).count()
        print(f"Total leave requests in database: {count}")
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()