from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel
from database import User
from sqlalchemy import func


from database import SessionLocal, Student, Attendance, Headcount
from auth import authenticate_user, create_access_token, get_current_user

# ------------------------
# BASE DIR & app setup
# ------------------------
BASE_DIR = Path(__file__).resolve().parent
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

# ------------------------
# Database dependency
# ------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------
# Auth & Pages
# ------------------------

# ------------------------
# Auth & Pages
# ------------------------

# Root -> redirect to login
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/login")

# Public login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Protected dashboard page

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



# Token endpoint
@app.post("/token", name="token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------------
# Student endpoints
# ------------------------
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

# ------------------------
# Attendance endpoints
# ------------------------
class AttendanceCreate(BaseModel):
    rfid_tag: str
    class_id: str

@app.post("/attendance")
def create_attendance(scan: AttendanceCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    student = db.query(Student).filter(Student.rfid_tag == scan.rfid_tag).first()
    if not student:
        return {"error": "Student with this RFID not found."}

    attendance_record = Attendance(
        student_id=student.id,
        class_id=scan.class_id,
        timestamp=datetime.utcnow()
    )
    db.add(attendance_record)
    db.commit()
    db.refresh(attendance_record)
    return {
        "id": attendance_record.id,
        "student_id": student.id,
        "class_id": scan.class_id,
        "timestamp": attendance_record.timestamp
    }

# ------------------------
# Headcount endpoints
# ------------------------
class HeadcountCreate(BaseModel):
    class_id: str
    count: int

@app.post("/headcount")
def create_headcount(data: HeadcountCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    headcount_record = Headcount(
        class_id=data.class_id,
        count=data.count,
        timestamp=datetime.utcnow()
    )
    db.add(headcount_record)
    db.commit()
    db.refresh(headcount_record)
    return {
        "id": headcount_record.id,
        "class_id": headcount_record.class_id,
        "count": headcount_record.count,
        "timestamp": headcount_record.timestamp
    }

# ------------------------
# Verification endpoints
# ------------------------
@app.get("/verify/{class_id}")
def verify_attendance(class_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    rfid_count = db.query(Attendance).filter(Attendance.class_id == class_id).count()
    headcount_record = db.query(Headcount).filter(
        Headcount.class_id == class_id
    ).order_by(Headcount.timestamp.desc()).first()

    if not headcount_record:
        return {"status": "No headcount recorded for this class yet."}

    headcount = headcount_record.count
    status = "green" if rfid_count == headcount else "red"

    return {
        "class_id": class_id,
        "rfid_count": rfid_count,
        "headcount": headcount,
        "status": status
    }

@app.get("/headcounts/{class_id}")
def get_headcounts(class_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Headcount).filter(
        Headcount.class_id == class_id
    ).order_by(Headcount.timestamp.asc()).all()
    return [
        {"id": r.id, "class_id": r.class_id, "count": r.count, "timestamp": r.timestamp}
        for r in records
    ]

# In main.py

# GET all attendance
@app.get("/attendance")
def get_attendance(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Attendance).all()
    return [
        {
            "id": r.id,
            "student_id": r.student_id,
            "class_id": r.class_id,
            "timestamp": r.timestamp
        } for r in records
    ]

# GET all headcounts
@app.get("/headcount")
def get_headcounts(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Headcount).all()
    return [
        {
            "id": r.id,
            "class_id": r.class_id,
            "count": r.count,
            "timestamp": r.timestamp
        } for r in records
    ]


from fastapi import Path

@app.get("/student/{student_id}/attendance")
def student_attendance(student_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    
    # Group by class_id
    class_count = {}
    for r in records:
        if r.class_id in class_count:
            class_count[r.class_id] += 1
        else:
            class_count[r.class_id] = 1
    
    return class_count  # Example: {"BEC405A": 5, "BEC406B": 3}

@app.get("/student/{student_id}/attendance-summary")
def student_attendance_summary(student_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Count attendance per class
    records = db.query(Attendance.class_id, func.count(Attendance.id).label("attended")) \
                .filter(Attendance.student_id == student_id) \
                .group_by(Attendance.class_id).all()

    summary = []
    for r in records:
        # Get latest headcount for the class
        headcount_record = db.query(Headcount) \
                             .filter(Headcount.class_id == r.class_id) \
                             .order_by(Headcount.timestamp.desc()).first()
        total = headcount_record.count if headcount_record else 0
        percent = round((r.attended / total) * 100, 2) if total else 0
        summary.append({
            "class_id": r.class_id,
            "attended": r.attended,
            "attendance_percentage": percent
        })

    return {"classes": summary}

