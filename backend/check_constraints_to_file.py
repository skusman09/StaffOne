import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def check_constraints_to_file():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        log_file = "d:/projects/StaffOne/backend/constraints_log.txt"
        with open(log_file, "w") as f:
            tables = ['onboarding_notes', 'employee_onboardings']
            for table in tables:
                f.write(f"\n--- Constraints for {table} ---\n")
                cursor.execute(f"""
                    SELECT conname, pg_get_constraintdef(oid)
                    FROM pg_constraint
                    WHERE conrelid = '{table}'::regclass
                """)
                constraints = cursor.fetchall()
                for con in constraints:
                    f.write(f"[{con[0]}]\n{con[1]}\n\n")

        print(f"Constraints written to {log_file}")
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    check_constraints_to_file()
