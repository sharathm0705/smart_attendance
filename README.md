# Smart Attendance System 

An automated attendance system designed to streamline classroom and organizational attendance tracking using IoT and computer vision.

This project uses a **Raspberry Pi** with a **Pi Camera** and **ESP32** for RFID scanning. The backend is built with **FastAPI** and performs real-time headcount verification.

---

# Features 

- Capture student photos via Pi Camera and ESP32 RFID scans.
- Process images in the backend using YOLOv8 for real-time headcount.
- Compare headcount with RFID scans for accuracy verification.
- Provides a secure and scalable API with FastAPI.
- Stores attendance and headcount in a database for future analysis.

---

## Tech Stack 

- **Hardware:** Raspberry Pi, Pi Camera, ESP32  
- **Backend:** FastAPI, SQLAlchemy, SQLite/PostgreSQL  
- **Computer Vision:** YOLOv8 (Ultralytics)  
- **Python Libraries:** OpenCV, pandas, requests, picamera2  

---

## Installation & Setup 

1. Clone the repository:
```bash
git clone https://github.com/sharathm0705/smart_attendance.git
cd smart_attendance
