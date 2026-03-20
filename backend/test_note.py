import os
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.services import onboarding_service
from app.models.user import User
import traceback

def test_note():
    db = SessionLocal()
    error_file = "d:/projects/StaffOne/backend/error_log.txt"
    try:
        # Try to find an assignment and an admin
        assignment_id = 1
        admin_id = 1 # Assuming user 1 exists and is admin
        note_text = "Test note from simulation script"
        
        print(f"Testing add_note(db, assignment_id={assignment_id}, admin_id={admin_id}, note_text='{note_text}')")
        onboarding_service.add_note(db, assignment_id, admin_id, note_text)
        print("Success!")
        with open(error_file, "w") as f:
            f.write("Success!")
    except Exception as e:
        with open(error_file, "w") as f:
            f.write(traceback.format_exc())
        print("Caught exception! See error_log.txt")
    finally:
        db.close()

if __name__ == "__main__":
    test_note()
