import sqlite3
import os

db_path = 'd:/projects/StaffOne/backend/staffone.db'

def check_tables():
    if not os.path.exists(db_path):
        print(f"Error: {db_path} does not exist")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in staffone.db:")
    for table in tables:
        print(f"- {table[0]}")
    conn.close()

if __name__ == "__main__":
    check_tables()
