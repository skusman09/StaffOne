import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def check_users():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        print("Users in PostgreSQL:")
        for user in users:
            print(f"- ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    check_users()
