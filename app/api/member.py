from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.db import UserDatabase

router = APIRouter(prefix="/api/member", tags=["Member Operations"])
db = UserDatabase()

class WaterUpdate(BaseModel):
    amount: Optional[int] = 0
    reset: Optional[bool] = False

class WorkoutToggle(BaseModel):
    workout_id: int

class BookClassRequest(BaseModel):
    class_id: int
    member_name: Optional[str] = "Rohan Sharma"

@router.get("/data")
def get_member_overview():
    return db.get_member_data()

@router.post("/water")
def update_water(payload: WaterUpdate):
    return db.update_water(amount=payload.amount, reset=payload.reset)

@router.post("/workout/toggle")
def toggle_workout(payload: WorkoutToggle):
    res = db.toggle_workout(payload.workout_id)
    if not res:
        raise HTTPException(status_code=404, detail="Workout item not found.")
    return res

@router.post("/book-class")
def book_class(payload: BookClassRequest):
    return {
        "status": "success",
        "message": f"Class booked successfully for {payload.member_name}! A confirmation SMS has been sent."
    }
