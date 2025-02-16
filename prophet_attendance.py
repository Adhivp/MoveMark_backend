import pandas as pd
from prophet import Prophet
from datetime import date, timedelta
import holidays
from sqlalchemy.orm import Session
from database import get_db
from models import Attendance, Employee
from typing import Optional
from fastapi import Depends

def create_prophet_model(employee_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Creates and trains a Prophet model for attendance prediction.

    Args:
        employee_id (Optional[int]): Employee ID to filter attendance data.
                                      If None, uses all employee data.
        db (Session): Database session.

    Returns:
        Prophet: Trained Prophet model.
    """

    # 1. Fetch Attendance Data
    query = db.query(Attendance.date, Attendance.status)
    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    attendance_records = query.all()

    if not attendance_records:
        raise ValueError("No attendance records found for the given employee ID.")

    df = pd.DataFrame([(record.date, record.status) for record in attendance_records], columns=['ds', 'status'])

    # Convert 'ds' to datetime and filter for present days
    df['ds'] = pd.to_datetime(df['ds'])
    df = df[df['status'] == 'present']  # Only model 'present' days
    df['y'] = 1  # Prophet needs a numeric target variable

    # 2. Handle Holidays
    # Fetch all holidays for the year
    start_date = df['ds'].min().to_pydatetime().date()
    end_date = df['ds'].max().to_pydatetime().date()
    years = list(range(start_date.year, end_date.year + 1))
    all_holidays = holidays.country_holidays('US', years=years)  # Or your country code

    holidays_df = pd.DataFrame([(date, all_holidays.get(date)) for date in sorted(all_holidays.keys())], columns=['ds', 'holiday'])
    holidays_df['ds'] = pd.to_datetime(holidays_df['ds'])

    # 3. Create and Fit the Prophet Model
    model = Prophet(holidays=holidays_df)
    model.fit(df)

    return model


def predict_attendance(model: Prophet, future_date: date) -> float:
    """
    Predicts attendance probability for a given date.

    Args:
        model (Prophet): Trained Prophet model.
        future_date (date): Date for which to predict attendance.

    Returns:
        float: Predicted attendance probability (0 to 100).
    """
    future = pd.DataFrame([future_date], columns=['ds'])
    future['ds'] = pd.to_datetime(future['ds'])
    forecast = model.predict(future)
    # The 'yhat' column contains the prediction
    predicted_value = forecast['yhat'][0]

    # Convert to probability (0-100) - assuming y values are 0 or 1
    probability = min(max(predicted_value, 0), 1) * 100  # Clamp values

    return probability