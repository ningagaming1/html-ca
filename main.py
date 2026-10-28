"""
main.py — Titans Fitness Studio
────────────────────────────────
This is the entry point of the web app.
It starts a FastAPI server, wires up all the API routes,
and serves the HTML frontend from the /static folder.

HOW TO RUN:
    uvicorn main:app --reload
    Then open http://localhost:8000 in your browser.
"""

import os
import json
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# Load .env file so os.getenv() works for DEMO, OLLAMA_MODEL, etc.
# python-dotenv must be installed: pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()

# Import all the route modules from app/api/
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.member import router as member_router
from app.api.trainer import router as trainer_router
from app.api.admin import router as admin_router

# ──────────────────────────────────────────────────────────────
# Create the FastAPI app
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Titans Fitness Studio API",
    description="Backend API for Titans Fitness Studio dashboards and the FitBuddy AI assistant."
)

# Resolve the absolute path to the project root and static folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ──────────────────────────────────────────────────────────────
# 1. Register API routes
#    All API endpoints start with /api/...
# ──────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(member_router)
app.include_router(trainer_router)
app.include_router(admin_router)

# ──────────────────────────────────────────────────────────────
# 2. Feedback endpoint
#    Reads and returns the feedback.json dataset as-is.
# ──────────────────────────────────────────────────────────────
@app.get("/api/feedback", tags=["Feedback"])
def get_feedback():
    feedback_path = os.path.join(BASE_DIR, "feedback.json")
    if not os.path.exists(feedback_path):
        return []
    with open(feedback_path, "r", encoding="utf-8") as file:
        return json.load(file)

# ──────────────────────────────────────────────────────────────
# 3. Legacy redirect (keeps old links from breaking)
# ──────────────────────────────────────────────────────────────
@app.get("/ca.login.html")
def redirect_old_login():
    return RedirectResponse(url="/login.html", status_code=307)

# ──────────────────────────────────────────────────────────────
# 4. Serve the frontend HTML/CSS/JS files
#    This MUST come last so that API routes are matched first.
# ──────────────────────────────────────────────────────────────
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# ──────────────────────────────────────────────────────────────
# Only runs when you execute: python main.py directly
# (not when using uvicorn main:app)
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)