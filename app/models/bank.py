"""
Bank model
"""
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Bank(Base):
    """
    Bank model
    """
    __tablename__ = "banks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<Bank {self.name}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "active": self.active
        }
