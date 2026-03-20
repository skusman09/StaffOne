from app.database import SessionLocal
from app.models.pulse import PulseSurvey

def seed():
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(PulseSurvey).filter(PulseSurvey.question == 'How satisfied are you with the new StaffOne interface?').first()
        if existing:
            print("Survey already seeded.")
            return

        survey = PulseSurvey(
            question='How satisfied are you with the new StaffOne interface?',
            is_active=True
        )
        db.add(survey)
        db.commit()
        print("Survey seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding survey: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
