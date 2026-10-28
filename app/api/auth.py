from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.db import UserDatabase

router = APIRouter(prefix="/api", tags=["Authentication"])
db = UserDatabase()

class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "member"

@router.post("/login")
def login(creds: LoginRequest):
    identifier = creds.email or creds.username
    if not identifier:
        raise HTTPException(status_code=400, detail="Email or username is required.")

    user = db.verify_login(identifier, creds.password)
    if not user:
        # Fallback for standard admin demo check
        if (identifier == "admin@123" or identifier == "admin") and creds.password == "gym123":
            return {
                "status": "success",
                "message": "Login successful!",
                "user": {"username": "admin", "role": "admin", "full_name": "Rajesh Singhania"},
                "redirect_url": "/admin-dashboard.html"
            }
        raise HTTPException(status_code=401, detail="Invalid username/email or password.")

    # Determine redirect based on role
    role = user.get("role", "member").lower()
    if role in ["admin", "owner"]:
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

@router.post("/signup")
def signup(data: SignupRequest):
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

@router.get("/me")
def get_current_user():
    return {
        "username": "rohan",
        "role": "member",
        "full_name": "Rohan Sharma",
        "member_code": "#TITAN-9204"
    }
