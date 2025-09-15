from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# ------------------------
# Database URL (with psycopg2 driver)
# ------------------------
DATABASE_URL = "postgresql+psycopg2://neondb_owner:npg_K4TYGbC9wNZy@ep-solitary-cake-ad0w467k-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

# ------------------------
# Engine & Session
# ------------------------
engine = create_engine(DATABASE_URL, echo=True)  # echo=True shows SQL logs in terminal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------------
# Models
# ------------------------
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rfid_tag = Column(String, unique=True, nullable=False)

    attendance_records = relationship("Attendance", back_populates="student")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    class_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="attendance_records")


class Headcount(Base):
    __tablename__ = "headcounts"
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    count = Column(Integer, nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="teacher")


# ------------------------
# DB Initializer
# ------------------------
def init_db():
    Base.metadata.create_all(bind=engine)
