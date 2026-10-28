from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import json
import os

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.member import router as member_router
from app.api.trainer import router as trainer_router
from app.api.admin import router as admin_router

app = FastAPI(
    title="Titans Fitness Studio Management API",
    description="Backend API powering Titans Fitness Studio Dashboards & FitBuddy AI Copilot"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ------------------------------------------------------------------
# 1. API ROUTERS
# ------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(member_router)
app.include_router(trainer_router)
app.include_router(admin_router)

# ------------------------------------------------------------------
# 2. FEEDBACK ENDPOINT (Preserving existing JSON dataset)
# ------------------------------------------------------------------
@app.get("/api/feedback", tags=["Feedback"])
def get_feedback():
    feedback_path = os.path.join(BASE_DIR, "feedback.json")
    if not os.path.exists(feedback_path):
        return []
    with open(feedback_path, "r", encoding="utf-8") as file:
        return json.load(file)

# ------------------------------------------------------------------
# 3. COMPATIBILITY & REDIRECT ROUTES
# ------------------------------------------------------------------
@app.get("/ca.login.html")
def redirect_ca_login():
    return RedirectResponse(url="/login.html", status_code=307)

# ------------------------------------------------------------------
# 4. UNIVERSAL STATIC FILE SERVING
# ------------------------------------------------------------------
# Must be mounted last so API endpoints take priority
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)