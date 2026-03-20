from app.database import engine, Base
from app.models import * # This should now include OnboardingNote

def create_missing_tables():
    print("Creating missing tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    create_missing_tables()
