"""Check all tables in Neon database."""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check all schemas
    result = conn.execute(text("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name
    """))
    tables = [(row[0], row[1]) for row in result]
    
    if tables:
        print(f"Found {len(tables)} table(s) in Neon database:")
        for schema, table in tables:
            print(f"  - {schema}.{table}")
    else:
        print("No tables found!")
    
    # Also check if users table exists directly
    try:
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"\nUsers table exists with {count} rows")
    except Exception as e:
        print(f"\nUsers table check: {e}")

