"""Create tables in Neon database."""
from app.database import Base, engine
from app.models import User, CheckInOut

print("Creating tables in Neon PostgreSQL...")
print(f"Database URL: {str(engine.url).split('@')[0]}@***")

try:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("\nTables created successfully!")
    
    # Verify tables were created
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        print(f"\nFound {len(tables)} table(s):")
        for table in tables:
            print(f"  - {table}")
            
except Exception as e:
    print(f"\nError creating tables: {e}")
    import traceback
    traceback.print_exc()

