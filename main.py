from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

app = FastAPI(title="xyx gym Management API")


# ------------------------------------------------------------------
# 1. DATA MODELS (FOR RECEIVING DATA FROM JS)
# ------------------------------------------------------------------
class LoginData(BaseModel):
    username: str
    password: str


# ------------------------------------------------------------------
# 2. API ENDPOINTS
# ------------------------------------------------------------------

# GET Endpoint: Serves client feedback data to script.js for rotating cards
@app.get("/api/feedback")
def get_feedback():
    with open("feedback.json","r",encoding="utf-8") as file:
        content = json.load(file)
    return content

# POST Endpoint: Receives login details submitted from JavaScript
@app.post("/api/login")
def login(credentials: LoginData):
    print(f"Received login attempt for user: {credentials.username}")

    # Temporary hardcoded check (In the future, query PostgreSQL here!)
    if credentials.username == "admin" and credentials.password == "gym123":
        return {
            "status": "success",
            "message": "Login successful! Welcome to xyx gym.",
        }
    else:
        raise HTTPException(
            status_code=401, detail="Invalid username or password."
        )


# ------------------------------------------------------------------
# 3. HTML & STATIC FILES SERVING
# ------------------------------------------------------------------

#Serves your main HTML webpage at http://127.0.0.1:8000/
@app.get("/", response_class=HTMLResponse)
def read_root():
    # REPLACE 'gym.html' WITH YOUR ACTUAL HTML FILENAME IF DIFFERENT
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


# Mounts directory so script.js, CSS, and images can be downloaded by Opera
app.mount("/", StaticFiles(directory="."), name="static")