from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base  
from models import Employee
from schemas import schemas

def seed_employees():
    db = SessionLocal()
    try:
        employees = [
            {"employee_id": 1, "employee_name": "Aiswarya", "email": "aiswarya@movemark.com", "department": "Engineering"},
            {"employee_id": 2, "employee_name": "Anirudh", "email": "anirudh@movemark.com", "department": "Marketing"},
            {"employee_id": 3, "employee_name": "Arun", "email": "arun@movemark.com", "department": "HR"},
            {"employee_id": 4, "employee_name": "Aswathy", "email": "aswathy@movemark.com", "department": "Finance"},
            {"employee_id": 5, "employee_name": "George", "email": "george@movemark.com", "department": "Engineering"},
            {"employee_id": 6, "employee_name": "Keerthana", "email": "keerthana@movemark.com", "department": "Marketing"},
            {"employee_id": 7, "employee_name": "Rehan", "email": "rehan@movemark.com", "department": "HR"},
            {"employee_id": 8, "employee_name": "Sajisha", "email": "sajisha@movemark.com", "department": "Finance"},
            {"employee_id": 9, "employee_name": "Sreesh", "email": "sreesh@movemark.com", "department": "Engineering"},
            {"employee_id": 10, "employee_name": "Sreevidya", "email": "sreevidya@movemark.com", "department": "Marketing"},
            {"employee_id": 11, "employee_name": "Vincy", "email": "vincy@movemark.com", "department": "Engineering"}
        ]

        # Check if employees already exist
        for employee_data in employees:
            existing_employee = db.query(Employee).filter(
                Employee.email == employee_data["email"]
            ).first()
            
            if not existing_employee:
                db_employee = Employee(**employee_data)
                db.add(db_employee)
        
        db.commit()
        print("Employees added successfully!")

    except Exception as e:
        print(f"Error seeding employees: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_employees()