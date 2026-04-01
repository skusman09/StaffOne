import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def update_notification_enum():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        new_values = [
            'onboarding_assigned',
            'onboarding_reminder',
            'onboarding_note_added',
            'onboarding_completed'
        ]
        
        for val in new_values:
            try:
                # Need to use lower case in SQL if it was created as lower case or without quotes
                # PostgreSQL enums are case sensitive.
                # In the previously checked list, they were shown as upper case? 
                # Let's check the previous output again.
                # Values in notificationtype enum:
                # - FORGOT_CHECKIN
                # - FORGOT_CHECKOUT
                # ...
                
                # Wait, in the code (notification.py) they are lower case:
                # ONBOARDING_REMINDER = "onboarding_reminder"
                
                # Let's check the case in the script.
                cursor.execute(f"ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS '{val}'")
                print(f"Added value '{val}' to notificationtype enum")
            except Exception as e:
                print(f"Could not add value '{val}': {e}")
                
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    update_notification_enum()
