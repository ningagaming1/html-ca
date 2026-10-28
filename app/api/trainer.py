from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.db import UserDatabase

router = APIRouter(prefix="/api/trainer", tags=["Trainer Operations"])
db = UserDatabase()

class RoutineAssignment(BaseModel):
    client_name: str
    template_name: str
    notes: Optional[str] = ""
    trainer_id: Optional[int] = 1

class SessionAction(BaseModel):
    session_id: int
    action: str = "start"

@router.get("/data")
def get_trainer_overview():
    return db.get_trainer_data()

@router.post("/assign-routine")
def assign_routine(payload: RoutineAssignment):
    return db.assign_routine(
        trainer_id=payload.trainer_id or 1,
        client_name=payload.client_name,
        template_name=payload.template_name,
        notes=payload.notes or ""
    )

@router.post("/start-session")
def start_session(payload: SessionAction):
    return {
        "status": "success",
        "message": f"Session #{payload.session_id} is now LIVE on floor!"
    }
