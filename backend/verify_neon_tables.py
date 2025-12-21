"""Verify tables are ready in Neon PostgreSQL."""
from app.database import engine
from sqlalchemy import text, inspect

print("=" * 60)
print("Verifying Tables in Neon PostgreSQL")
print("=" * 60)

with engine.connect() as conn:
    # 1. List all tables
    print("\n1. Checking Tables...")
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    print(f"   Found {len(tables)} table(s):")
    for table in tables:
        print(f"   - {table}")
    
    # 2. Check Users table structure
    print("\n2. Users Table Structure:")
    if 'users' in tables:
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        print("   Columns:")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            default = f" DEFAULT {row[3]}" if row[3] else ""
            print(f"     - {row[0]}: {row[1]} {nullable}{default}")
        
        # Check indexes
        result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'users'
        """))
        indexes = list(result)
        if indexes:
            print("   Indexes:")
            for idx in indexes:
                print(f"     - {idx[0]}")
        
        # Check constraints
        result = conn.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'users'
        """))
        constraints = list(result)
        if constraints:
            print("   Constraints:")
            for con in constraints:
                print(f"     - {con[0]}: {con[1]}")
    
    # 3. Check CheckInOuts table structure
    print("\n3. CheckInOuts Table Structure:")
    if 'checkinouts' in tables:
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'checkinouts'
            ORDER BY ordinal_position
        """))
        print("   Columns:")
        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            default = f" DEFAULT {row[3]}" if row[3] else ""
            print(f"     - {row[0]}: {row[1]} {nullable}{default}")
        
        # Check indexes
        result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'checkinouts'
        """))
        indexes = list(result)
        if indexes:
            print("   Indexes:")
            for idx in indexes:
                print(f"     - {idx[0]}")
        
        # Check foreign keys
        result = conn.execute(text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'checkinouts'
        """))
        fks = list(result)
        if fks:
            print("   Foreign Keys:")
            for fk in fks:
                print(f"     - {fk[1]} -> {fk[2]}.{fk[3]}")
    
    # 4. Check row counts
    print("\n4. Table Row Counts:")
    for table in ['users', 'checkinouts']:
        if table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   {table}: {count} row(s)")
            except Exception as e:
                print(f"   {table}: Error - {e}")
    
    # 5. Test connection
    print("\n5. Connection Test:")
    result = conn.execute(text("SELECT version()"))
    version = result.scalar()
    print(f"   PostgreSQL Version: {version.split(',')[0]}")
    
    result = conn.execute(text("SELECT current_database()"))
    db_name = result.scalar()
    print(f"   Database: {db_name}")

print("\n" + "=" * 60)
if 'users' in tables and 'checkinouts' in tables:
    print("All tables are ready in Neon PostgreSQL!")
    print("Your application is ready for CRUD operations!")
else:
    print("Some tables are missing. Run migrations:")
    print("  alembic upgrade head")
print("=" * 60)

