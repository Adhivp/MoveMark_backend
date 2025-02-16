from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Employee, Attendance
from datetime import datetime, date, timedelta
import random
from typing import List
import holidays
from tqdm import tqdm

def generate_random_time(start_hour: int, end_hour: int) -> datetime:
    hour = random.randint(start_hour, end_hour)
    minute = random.randint(0, 59)
    return datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time()

def is_holiday(date: date, holiday_dates: List[date]) -> bool:
    return date in holiday_dates

def generate_attendance_data():
    db = SessionLocal()
    try:
        # Get all employees
        employees = db.query(Employee).all()
        
        # Generate random holidays (excluding weekends)
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        # Get Indian holidays
        in_holidays = holidays.India(years=2024)
        
        # Select 11 random holidays from working days
        potential_holidays = [
            day for day in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1))
            if day.weekday() < 5 and day not in in_holidays
        ]
        custom_holidays = set(random.sample(potential_holidays, 11))
        all_holidays = custom_holidays.union(set(in_holidays))

        # Calculate total number of days for progress bar
        total_days = (end_date - start_date).days + 1

        # Generate attendance records with progress bar
        for current_date in tqdm(
            (start_date + timedelta(n) for n in range(total_days)),
            total=total_days,
            desc="Generating attendance records"
        ):
            # Skip weekends
            if current_date.weekday() >= 5:
                continue

            for employee in employees:
                # Randomly decide if employee is on leave (5% chance)
                is_leave = random.random() < 0.05

                if current_date not in all_holidays and not is_leave:
                    # Generate random check-in time (8 AM to 9 AM)
                    checkin_time = datetime.combine(
                        current_date,
                        generate_random_time(8, 9)
                    )

                    # Generate random check-out time (1 PM to 8 PM)
                    checkout_time = datetime.combine(
                        current_date,
                        generate_random_time(13, 20)
                    )

                    status = "present"
                else:
                    checkin_time = None
                    checkout_time = None
                    status = "leave" if is_leave else "holiday"

                # Create attendance record
                attendance = Attendance(
                    employee_id=employee.employee_id,
                    date=current_date,
                    checkin_time=checkin_time,
                    checkout_time=checkout_time,
                    status=status
                )
                db.add(attendance)

            # Commit every day's records
            db.commit()

        print("Successfully generated attendance records for the year!")

    except Exception as e:
        print(f"Error generating attendance data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_attendance_data()