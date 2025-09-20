from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from passlib.context import CryptContext
from zoneinfo import ZoneInfo
from database import SessionLocal, Student, Attendance, Headcount, User
from auth import authenticate_user, create_access_token, get_current_user

import cv2
import numpy as np
import shutil
import os

# =========================
# APP SETUP
# =========================
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()

# Mount static folder
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# SECURITY
# =========================
API_KEY = "my_secret_pi_key"  # Must match ESP32
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =========================
# TIMEZONE HELPER
# =========================
IST = ZoneInfo("Asia/Kolkata")

def now_ist():
    """Return current IST datetime"""
    return datetime.now(IST)

# =========================
# AUTH & PAGES
# =========================
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# =========================
# STUDENT ENDPOINTS (JWT)
# =========================
class StudentCreate(BaseModel):
    name: str
    rfid_tag: str

@app.post("/students")
def create_student(student: StudentCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_student = Student(name=student.name, rfid_tag=student.rfid_tag)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return {"id": db_student.id, "name": db_student.name, "rfid_tag": db_student.rfid_tag}

@app.get("/students")
def get_students(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    students = db.query(Student).all()
    return {"students": [{"id": s.id, "name": s.name, "rfid_tag": s.rfid_tag} for s in students]}

# =========================
# ATTENDANCE ENDPOINTS
# =========================
class AttendanceCreate(BaseModel):
    rfid_tag: str
    class_id: str

@app.post("/attendance")
def create_attendance(scan: AttendanceCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    student = db.query(Student).filter(Student.rfid_tag == scan.rfid_tag).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student with this RFID not found.")

    record = Attendance(
        student_id=student.id,
        class_id=scan.class_id,
        timestamp=now_ist()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "student_id": student.id, "class_id": scan.class_id, "timestamp": record.timestamp}

# ESP32 endpoint (API key)
@app.post("/attendence")
async def mark_attendance(request: Request, db: Session = Depends(get_db)):
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized device")

    data = await request.json()
    rfid_tag = data.get("rfid_tag")
    class_id = data.get("class_id")
    if not rfid_tag or not class_id:
        raise HTTPException(status_code=400, detail="Missing RFID or class ID")

    student = db.query(Student).filter(Student.rfid_tag == rfid_tag).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    record = Attendance(student_id=student.id, class_id=class_id, timestamp=now_ist())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"message": "Attendance marked", "student": student.name, "class": class_id}

# =========================
# HEADCOUNT ENDPOINTS
# =========================
class HeadcountCreate(BaseModel):
    class_id: str
    count: int

@app.post("/headcount")
def create_headcount(data: HeadcountCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    record = Headcount(class_id=data.class_id, count=data.count, timestamp=now_ist())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "class_id": record.class_id, "count": record.count, "timestamp": record.timestamp}

@app.get("/verify/{class_id}")
def verify_attendance(class_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    rfid_count = db.query(Attendance).filter(Attendance.class_id == class_id).count()
    headcount_record = db.query(Headcount).filter(Headcount.class_id == class_id).order_by(Headcount.timestamp.desc()).first()

    if not headcount_record:
        return {"status": "No headcount recorded for this class yet."}

    headcount = headcount_record.count
    status = "green" if rfid_count == headcount else "red"
    return {"class_id": class_id, "rfid_count": rfid_count, "headcount": headcount, "status": status}

@app.get("/headcounts/{class_id}")
def get_headcounts_for_class(class_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Headcount).filter(Headcount.class_id == class_id).order_by(Headcount.timestamp.asc()).all()
    return [{"id": r.id, "class_id": r.class_id, "count": r.count, "timestamp": r.timestamp} for r in records]

# =========================
# ESP32-SAFE ENDPOINT
# =========================
@app.get("/esp32/status/{class_id}")
def esp32_status(class_id: str, request: Request, db: Session = Depends(get_db)):
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized device")

    rfid_count = db.query(Attendance).filter(Attendance.class_id == class_id).count()
    headcount_record = (
        db.query(Headcount)
        .filter(Headcount.class_id == class_id)
        .order_by(Headcount.timestamp.desc())
        .first()
    )

    if not headcount_record:
        return {"class_id": class_id, "rfid_count": rfid_count, "headcount": None}

    return {
        "class_id": class_id,
        "rfid_count": rfid_count,
        "headcount": headcount_record.count,
        "timestamp": headcount_record.timestamp
    }

# =========================
# ALL RECORDS (JWT)
# =========================
@app.get("/attendance")
def get_all_attendance(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Attendance).all()
    return [{"id": r.id, "student_id": r.student_id, "class_id": r.class_id, "timestamp": r.timestamp} for r in records]

@app.get("/headcount")
def get_all_headcounts(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Headcount).all()
    return [{"id": r.id, "class_id": r.class_id, "count": r.count, "timestamp": r.timestamp} for r in records]

# =========================
# STUDENT ATTENDANCE SUMMARY (JWT)
# =========================
@app.get("/student/{student_id}/attendance")
def student_attendance(student_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    summary = {}
    for r in records:
        summary[r.class_id] = summary.get(r.class_id, 0) + 1
    return summary

@app.get("/student/{student_id}/attendance-summary")
def student_attendance_summary(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(Attendance.class_id, func.count(Attendance.id).label("attended")) \
                .filter(Attendance.student_id == student_id) \
                .group_by(Attendance.class_id).all()
    summary = []
    for r in records:
        headcount_record = db.query(Headcount).filter(Headcount.class_id == r.class_id).order_by(Headcount.timestamp.desc()).first()
        total = headcount_record.count if headcount_record else 0
        percent = round((r.attended / total) * 100, 2) if total else 0
        summary.append({"class_id": r.class_id, "attended": r.attended, "attendance_percentage": percent})
    return {"classes": summary}

# =========================
# USER REGISTRATION
# =========================
@app.post("/register")
def register_user(username: str, password: str, db: Session = Depends(get_db)):
    hashed_pw = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User registered successfully", "id": user.id}

# =========================
# NEW: RASPBERRY PI PHOTO UPLOAD
# =========================
@app.post("/upload-photo")
async def upload_photo(class_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Pi sends a classroom photo, backend detects faces, stores headcount"""
    save_path = UPLOAD_DIR / file.filename
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load image with OpenCV
    image = cv2.imread(str(save_path))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Use Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

    headcount = len(faces)

    # Save to DB
    record = Headcount(class_id=class_id, count=headcount, timestamp=now_ist())
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "class_id": class_id,
        "headcount": headcount,
        "timestamp": record.timestamp,
        "file_saved": str(save_path)
    }
