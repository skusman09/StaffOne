import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def check_workflows():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM onboarding_workflows")
        workflows = cursor.fetchall()
        print("Workflows in PostgreSQL:")
        for wf in workflows:
            print(f"- ID: {wf[0]}, Title: {wf[1]}")
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    check_workflows()
