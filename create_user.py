from database import SessionLocal, User
from auth import get_password_hash

db = SessionLocal()

username = "teacher1"

# Check if user already exists
existing_user = db.query(User).filter(User.username == username).first()
if existing_user:
    print(f"User '{username}' already exists!")
else:
    new_user = User(
        username=username,
        hashed_password=get_password_hash("mypassword123")
    )
    db.add(new_user)
    db.commit()
    print("User created successfully!")

db.close()
