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
```
2. Create and activate a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the FastAPI backend:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
5. On Raspberry Pi, run the image capture & upload script:
```bash
python3 capture_and_send.py
```
---
## Usage 

- Visit http://<backend-ip>:8000/dashboard to view attendance and headcount.
- Raspberry Pi continuously captures images and sends headcount data to the backend.
- ESP32 RFID scans are verified against the processed headcount.
---
## Hackathon 

- Winner of **TECHNOVATE 2025** at **Alva's Institute of Engineering and Technology**.
- Project demonstrates real-time IoT + AI integration for classroom automation.



