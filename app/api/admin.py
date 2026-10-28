from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.db import UserDatabase

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])
db = UserDatabase()

class MaintenanceRequest(BaseModel):
    equipment_name: str
    description: str
    status: Optional[str] = "Service Due"
    status_pill: Optional[str] = "pill-expiring"

class OccupancyUpdate(BaseModel):
    delta: int

@router.get("/data")
def get_admin_overview():
    return db.get_admin_data()

@router.post("/maintenance")
def add_ticket(payload: MaintenanceRequest):
    return db.add_maintenance_ticket(
        equipment_name=payload.equipment_name,
        description=payload.description,
        status=payload.status,
        status_pill=payload.status_pill
    )
