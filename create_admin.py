# create_admin.py
from database import SessionLocal
from auth import get_password_hash
from database import User

def create_admin(username="admin", password="adminpass"):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print("Admin already exists")
            return
        u = User(username=username, hashed_password=get_password_hash(password), role="admin")
        db.add(u)
        db.commit()
        print("Admin user created:", username)
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
