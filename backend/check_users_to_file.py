import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def check_users_to_file():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        log_file = "d:/projects/StaffOne/backend/users_log.txt"
        with open(log_file, "w") as f:
            cursor.execute("SELECT id, username, email, role FROM users ORDER BY id")
            users = cursor.fetchall()
            f.write(f"Total users: {len(users)}\n\n")
            for user in users:
                f.write(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}\n")

        print(f"Users written to {log_file}")
        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    check_users_to_file()
