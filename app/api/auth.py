import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.db import UserDatabase

# ──────────────────────────────────────────────────────────────
# Load .env BEFORE reading any environment variables.
# This guarantees that os.getenv("DEMO") sees the value from
# the .env file even when auth.py is imported early.
# ──────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/api", tags=["Authentication"])
db = UserDatabase()

# ──────────────────────────────────────────────────────────────
# DEMO MODE
# Read the DEMO variable from the .env file.
# When DEMO=on  → demo admin shortcut is active.
# When DEMO=off → only real database users can log in.
# ──────────────────────────────────────────────────────────────
DEMO_MODE = os.getenv("DEMO", "off").strip().lower() == "on"


# ──────────────────────────────────────────────────────────────
# Request Models
# These describe what data the frontend must send us.
# ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    # A user can log in with either email OR username
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "member"   # default role is "member"


# ──────────────────────────────────────────────────────────────
# POST /api/login
# ──────────────────────────────────────────────────────────────

@router.post("/login")
def login(creds: LoginRequest):
    # Use whichever identifier was provided (email or username)
    identifier = creds.email or creds.username
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username is required.")

    # Try to verify against the database first
    user = db.verify_login(identifier, creds.password)

    if not user:
        # If DEMO mode is on, allow the hardcoded admin shortcut
        if DEMO_MODE and (identifier in ("admin@123", "admin")) and creds.password == "gym123":
            return {
                "status": "success",
                "message": "Login successful!",
                "user": {"username": "admin", "role": "admin", "full_name": "Rajesh Singhania"},
                "redirect_url": "/admin-dashboard.html"
            }
        # Otherwise, reject the login
        raise HTTPException(status_code=401, detail="Invalid username/email or password.")

    # Decide which dashboard to send the user to based on their role
    role = user.get("role", "member").lower()
    if role in ("admin", "owner"):
        redirect_url = "/admin-dashboard.html"
    elif role == "trainer":
        redirect_url = "/trainer-dashboard.html"
    else:
        redirect_url = "/member-dashboard.html"

    return {
        "status": "success",
        "message": f"Welcome back, {user['full_name']}!",
        "user": user,
        "redirect_url": redirect_url
    }


# ──────────────────────────────────────────────────────────────
# POST /api/signup
# ──────────────────────────────────────────────────────────────

@router.post("/signup")
def signup(data: SignupRequest):
    # Try to add the user; returns False if username/email already exists
    success = db.add_user(
        username=data.username,
        email=data.email,
        password=data.password,
        role=data.role or "member",
        full_name=data.full_name or data.username.capitalize()
    )

    if not success:
        raise HTTPException(status_code=400, detail="Username or email already registered.")

    return {
        "status": "success",
        "message": "Account created successfully! Please log in.",
        "redirect_url": "/login.html"
    }


# ──────────────────────────────────────────────────────────────
# GET /api/demo-mode
# Frontend calls this on page load to know whether to show
# the demo quick-fill buttons.
# ──────────────────────────────────────────────────────────────

@router.get("/demo-mode")
def get_demo_mode():
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={"demo": DEMO_MODE},
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
    )
