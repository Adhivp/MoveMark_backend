from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Employee, Attendance, LeaveRequest
from datetime import datetime

def print_database_contents():
    db = SessionLocal()
    try:
        # Add debug counts
        employee_count = db.query(Employee).count()
        attendance_count = db.query(Attendance).count()
        leave_count = db.query(LeaveRequest).count()
        
        print(f"\nDatabase Summary:")
        print(f"Total Employees: {employee_count}")
        print(f"Total Attendance Records: {attendance_count}")
        print(f"Total Leave Requests: {leave_count}")

        # Print each employee's details
        print("\n=== DETAILED EMPLOYEE INFORMATION ===")
        employees = db.query(Employee).all()
        for emp in employees:
            print(f"\nEmployee ID: {emp.employee_id}")
            print(f"Name: {emp.employee_name}")
            print(f"Email: {emp.email}")
            print(f"Department: {emp.department}")
            
            # Get attendance records for this employee
            attendance = db.query(Attendance).filter(
                Attendance.employee_id == emp.employee_id
            ).all()
            
            if attendance:
                print("Attendance Records:")
                for record in attendance:
                    print(f"  Date: {record.date}")
                    print(f"  Check-in: {record.checkin_time}")
                    print(f"  Check-out: {record.checkout_time}")
                    print(f"  Status: {record.status}")
                    print("  ---")
            else:
                print("No attendance records found")

            # Update leave request query with better error handling
            try:
                leave_requests = db.query(LeaveRequest).filter(
                    LeaveRequest.employee_id == emp.employee_id
                ).all()

                if leave_requests:
                    print(f"Leave Request Records (Total: {len(leave_requests)}):")
                    for leave in leave_requests:
                        print(f"  Request ID: {leave.id}")
                        print(f"  Employee ID: {leave.employee_id}")
                        print(f"  Date: {leave.date_to_be_on_leave}")
                        print(f"  Half Day: {'Yes' if leave.is_half_day else 'No'}")
                        if leave.leave_period:
                            print(f"  Period: {leave.leave_period}")
                        print(f"  Reason: {leave.reason}")
                        print("  ---")
                else:
                    print(f"No leave request records found for employee {emp.employee_id}")
            except Exception as e:
                print(f"Error querying leave requests: {e}")

            print("-" * 50)

    except Exception as e:
        print(f"Error reading database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print_database_contents()