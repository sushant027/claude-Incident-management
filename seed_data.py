"""
Seed initial data
"""
import bcrypt
from sqlalchemy.orm import Session
from app.models import UserRole
from app.models.user import User
from app.models.bank import Bank

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def seed_database(db: Session):
    """
    Seed database with initial users and bank
    """
    # Check if already seeded
    if db.query(User).count() > 0:
        print("Database already seeded. Skipping...")
        return
    
    print("Seeding database...")
    
    # Create initial users
    users_data = [
        {"username": "admin", "password": "admin123", "name": "Admin User", "email": "admin@demobank.com", "role": UserRole.ADMIN},
        {"username": "manager", "password": "manager123", "name": "Incident Manager", "email": "manager@demobank.com", "role": UserRole.INCIDENT_MANAGER},
        {"username": "sme", "password": "sme123", "name": "SME User", "email": "sme@demobank.com", "role": UserRole.SME},
        {"username": "l2", "password": "l2123", "name": "L2 Support", "email": "l2@demobank.com", "role": UserRole.SUPPORT_L2},
        {"username": "expert", "password": "expert123", "name": "Expert Support", "email": "expert@demobank.com", "role": UserRole.SUPPORT_EXPERT},
    ]
    
    for user_data in users_data:
        user = User(
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            name=user_data["name"],
            email=user_data["email"],
            role=user_data["role"],
            active=True
        )
        db.add(user)
        print(f"Created user: {user.username} ({user.role.value})")
    
    # Create initial bank
    bank = Bank(name="Demo Bank", active=True)
    db.add(bank)
    print(f"Created bank: {bank.name}")
    
    db.commit()
    print("Database seeding completed!")

if __name__ == "__main__":
    from database import SessionLocal, init_db
    
    # Initialize tables
    init_db()
    
    # Seed data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
