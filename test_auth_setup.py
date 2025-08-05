"""
Test script to initialize database and test authentication
"""
from database import Base, engine, SessionLocal
from auth import create_user, authenticate_user, UserRegister
import uuid

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def test_auth():
    """Test authentication functions"""
    db = SessionLocal()
    
    try:
        # Test user data
        test_user = UserRegister(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        
        print("Testing user creation...")
        user = create_user(db, test_user)
        print(f"User created: {user.username} ({user.email})")
        
        print("Testing authentication...")
        auth_result = authenticate_user(db, "testuser", "testpassword123")
        if auth_result:
            print("Authentication successful!")
        else:
            print("Authentication failed!")
            
        # Test wrong password
        auth_result = authenticate_user(db, "testuser", "wrongpassword")
        if not auth_result:
            print("Wrong password correctly rejected!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    test_auth()
