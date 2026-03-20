import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def check_constraints():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check constraints for onboarding_notes
        print("Constraints for onboarding_notes:")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'onboarding_notes'::regclass
        """)
        constraints = cursor.fetchall()
        for con in constraints:
            print(f"- {con[0]}: {con[1]}")
            
        # Check constraints for employee_onboardings
        print("\nConstraints for employee_onboardings:")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'employee_onboardings'::regclass
        """)
        constraints = cursor.fetchall()
        for con in constraints:
            print(f"- {con[0]}: {con[1]}")

        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    check_constraints()
