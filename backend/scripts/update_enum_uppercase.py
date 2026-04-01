import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def update_notification_enum_uppercase():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # New values matching the Python enum member names (uppercase)
        new_values = [
            'ONBOARDING_ASSIGNED',
            'ONBOARDING_REMINDER',
            'ONBOARDING_NOTE_ADDED',
            'ONBOARDING_COMPLETED'
        ]
        
        for val in new_values:
            try:
                cursor.execute(f"ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{val}'")
                print(f"Added value '{val}' to notificationtype enum")
            except Exception as e:
                print(f"Could not add value '{val}': {e}")
                
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    update_notification_enum_uppercase()
