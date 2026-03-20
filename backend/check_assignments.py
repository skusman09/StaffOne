import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def check_assignments():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, workflow_id FROM employee_onboardings")
        assignments = cursor.fetchall()
        print("Assignments in PostgreSQL:")
        for ass in assignments:
            print(f"- ID: {ass[0]}, User ID: {ass[1]}, Workflow ID: {ass[2]}")
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    check_assignments()
