import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('d:/projects/StaffOne/backend/.env')
database_url = os.getenv('DATABASE_URL')

def check_notifications_structure():
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Get table definition
        cursor.execute("""
            SELECT column_name, data_type, udt_name
            FROM information_schema.columns 
            WHERE table_name = 'notifications'
        """)
        columns = cursor.fetchall()
        print("Columns in notifications table:")
        for col in columns:
            print(f"- {col[0]}: {col[1]} ({col[2]})")
            
        # Check if it's an enum type in PostgreSQL
        cursor.execute("""
            SELECT t.typname, e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid  
            WHERE t.typname = 'notificationtype'
        """)
        enum_values = cursor.fetchall()
        if enum_values:
            print("\nValues in notificationtype enum:")
            for val in enum_values:
                print(f"- {val[1]}")
        else:
            print("\nNo custom enum found for notificationtype (might be VARCHAR)")

        conn.close()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")

if __name__ == "__main__":
    check_notifications_structure()
