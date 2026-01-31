"""
User model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from database import Base
from app.models import UserRole

class User(Base):
    """
    User model - global users mapped to all banks
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
