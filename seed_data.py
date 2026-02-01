"""
Seed initial data
"""
import bcrypt
from sqlalchemy.orm import Session
from app.models import UserRole
from app.models.user import User
from app.models.bank import Bank
from app.models.bank_option import BankOption

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
    
    # Create initial banks
    demo_bank = Bank(name="Demo Bank", active=True)
    db.add(demo_bank)
    print(f"Created bank: {demo_bank.name}")

    alpha_bank = Bank(name="Alpha Bank", active=True)
    db.add(alpha_bank)
    print(f"Created bank: {alpha_bank.name}")

    beta_bank = Bank(name="Beta Bank", active=True)
    db.add(beta_bank)
    print(f"Created bank: {beta_bank.name}")

    db.flush()  # Flush to get IDs

    # Get admin user for updated_by
    admin_user = db.query(User).filter(User.username == "admin").first()

    # Create sample bank options for Demo Bank
    demo_option = BankOption(
        bank_id=demo_bank.id,
        transaction_volume_per_day=1500000,
        transaction_volume_per_month=45000000,
        architecture_diagram_url="https://example.com/diagrams/demo-bank-arch.png",
        number_of_app_servers=8,
        app_server_type="Tomcat 9.0",
        db_type="Oracle 19c",
        number_of_db_instances=3,
        implementation_developer_name="John Smith",
        db_developer_name="Sarah Johnson",
        db_developer_contact="sarah.johnson@demobank.com",
        aerospike_enabled=True,
        aerospike_version="6.2.0",
        aerospike_description="Used for session caching and real-time transaction lookups",
        redis_enabled=True,
        redis_description="Redis cluster for API rate limiting and temporary data storage",
        recon_enabled=True,
        recon_technology="redis",
        updated_by_id=admin_user.id if admin_user else None
    )
    db.add(demo_option)
    print(f"Created bank option for: {demo_bank.name}")

    # Create sample bank options for Alpha Bank
    alpha_option = BankOption(
        bank_id=alpha_bank.id,
        transaction_volume_per_day=800000,
        transaction_volume_per_month=24000000,
        architecture_diagram_url="https://example.com/diagrams/alpha-bank-arch.png",
        number_of_app_servers=4,
        app_server_type="JBoss EAP 7.4",
        db_type="PostgreSQL 14",
        number_of_db_instances=2,
        implementation_developer_name="Mike Chen",
        db_developer_name="Lisa Wang",
        db_developer_contact="lisa.wang@alphabank.com",
        aerospike_enabled=False,
        redis_enabled=True,
        redis_description="Redis for caching and pub/sub messaging",
        recon_enabled=True,
        recon_technology="pandas",
        updated_by_id=admin_user.id if admin_user else None
    )
    db.add(alpha_option)
    print(f"Created bank option for: {alpha_bank.name}")

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
