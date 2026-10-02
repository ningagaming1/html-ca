from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os

app = FastAPI(title="xyx gym Management API")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ------------------------------------------------------------------
# 1. DATA MODELS
# ------------------------------------------------------------------
class LoginData(BaseModel):
    username: str
    password: str

# ------------------------------------------------------------------
# 2. API ENDPOINTS (Must be defined BEFORE the static mount below)
# ------------------------------------------------------------------
@app.get("/api/feedback")
def get_feedback():
    feedback_path = os.path.join(BASE_DIR, "feedback.json")
    if not os.path.exists(feedback_path):
        return []
    with open(feedback_path, "r", encoding="utf-8") as file:
        return json.load(file)

@app.post("/api/login")
def login(credentials: LoginData):
    print(f"Received login attempt for user: {credentials.email}")
    if credentials.email == "admin@123" and credentials.password == "gym123":
        return {"status": "success", "message": "Login successful!"}
    raise HTTPException(status_code=401, detail="Invalid username or password.")

# ------------------------------------------------------------------
# 3. UNIVERSAL UI SERVING
# ------------------------------------------------------------------
# Mounts the static directory to the root. 
# html=True automatically resolves "/" to index.html and "/login" to login.html
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")