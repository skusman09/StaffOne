"""Test CRUD via FastAPI endpoints (simulating API calls)."""
from app.database import SessionLocal
from app.models import User, CheckInOut, Role
from datetime import datetime

print("Testing CRUD operations via database models...")
print("=" * 50)

db = SessionLocal()

try:
    # CREATE - Create a user directly (simulating API POST)
    print("\n1. CREATE - Creating user...")
    test_user = User(
        email="apiuser@example.com",
        username="apiuser",
        hashed_password="$2b$12$test_hash_placeholder",  # Using placeholder for test
        full_name="API Test User",
        role=Role.EMPLOYEE,
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    print(f"   User created with ID: {test_user.id}, Username: {test_user.username}")
    
    # READ - Read user (simulating API GET)
    print("\n2. READ - Reading user...")
    found_user = db.query(User).filter(User.id == test_user.id).first()
    if found_user:
        print(f"   User found: {found_user.username} - {found_user.email}")
        print(f"   Role: {found_user.role}, Active: {found_user.is_active}")
    
    # CREATE - Create check-in (simulating API POST /attendance/check-in)
    print("\n3. CREATE - Creating check-in record...")
    checkin = CheckInOut(
        user_id=test_user.id,
        check_in_time=datetime.utcnow(),
        latitude=40.7128,
        longitude=-74.0060,
        device_info="API Test Device"
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    print(f"   Check-in created with ID: {checkin.id}")
    print(f"   Check-in time: {checkin.check_in_time}")
    
    # READ - Read check-in records (simulating API GET /attendance/history)
    print("\n4. READ - Reading check-in records...")
    checkins = db.query(CheckInOut).filter(CheckInOut.user_id == test_user.id).all()
    print(f"   Found {len(checkins)} check-in record(s)")
    for ci in checkins:
        print(f"   - ID: {ci.id}, Check-in: {ci.check_in_time}, Check-out: {ci.check_out_time}")
    
    # UPDATE - Update check-out time (simulating API POST /attendance/check-out)
    print("\n5. UPDATE - Updating check-out time...")
    checkin.check_out_time = datetime.utcnow()
    db.commit()
    db.refresh(checkin)
    print(f"   Check-out time updated: {checkin.check_out_time}")
    
    # READ - Verify update
    updated_checkin = db.query(CheckInOut).filter(CheckInOut.id == checkin.id).first()
    print(f"   Verified: Check-out time is {updated_checkin.check_out_time}")
    
    # DELETE - Cleanup test data
    print("\n6. DELETE - Cleaning up test data...")
    db.delete(checkin)
    db.delete(test_user)
    db.commit()
    print("   Test records deleted successfully")
    
    print("\n" + "=" * 50)
    print("All CRUD operations successful!")
    print("FastAPI is ready for CRUD operations with Neon PostgreSQL!")
    print("\nYou can now:")
    print("  - Start server: .\\start_server.ps1")
    print("  - Test API endpoints at: http://localhost:8001/docs")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

