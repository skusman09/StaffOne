import os
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.services import onboarding_service
from app.models.user import User

def test_remind():
    db = SessionLocal()
    try:
        # Try to find an assignment and an admin
        assignment_id = 1
        admin_id = 1 # Assuming user 1 exists and is admin
        
        print(f"Testing send_reminder(db, assignment_id={assignment_id}, admin_id={admin_id})")
        onboarding_service.send_reminder(db, assignment_id, admin_id)
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_remind()
