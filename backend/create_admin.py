"""Create an admin user in the database."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, Role
from app.core.security import get_password_hash


def create_admin_user(username: str, email: str, password: str, full_name: str = None):
    """Create an admin user."""
    db: Session = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            print(f"❌ User with email '{email}' or username '{username}' already exists!")
            print(f"   Current role: {existing_user.role}")
            
            # Ask if user wants to promote existing user to admin
            if existing_user.role != Role.ADMIN:
                response = input(f"   Do you want to promote '{username}' to admin? (y/n): ").strip().lower()
                if response == 'y':
                    existing_user.role = Role.ADMIN
                    db.commit()
                    db.refresh(existing_user)
                    print(f"✅ User '{username}' promoted to admin successfully!")
                    return True
            return False
        
        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=Role.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Role: {admin_user.role}")
        print(f"   ID: {admin_user.id}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Create Admin User")
    print("=" * 60)
    print()
    
    # Get input from command line arguments or prompt
    if len(sys.argv) >= 4:
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
        full_name = sys.argv[4] if len(sys.argv) > 4 else None
    else:
        username = input("Username: ").strip()
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        full_name = input("Full Name (optional): ").strip() or None
    
    if not username or not email or not password:
        print("❌ Error: Username, email, and password are required!")
        sys.exit(1)
    
    success = create_admin_user(username, email, password, full_name)
    sys.exit(0 if success else 1)

