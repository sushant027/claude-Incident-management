"""
Bank architecture model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class BankArchitecture(Base):
    """
    Bank architecture information
    """
    __tablename__ = "bank_architectures"
    
    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    diagram_reference = Column(String(500), nullable=True)  # URL or file path
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    bank = relationship("Bank", backref="architectures")
    updated_by = relationship("User")
    
    def __repr__(self):
        return f"<Architecture {self.title} for {self.bank.name if self.bank else 'Unknown'}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "bank_id": self.bank_id,
            "bank_name": self.bank.name if self.bank else None,
            "title": self.title,
            "description": self.description,
            "diagram_reference": self.diagram_reference,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by.name if self.updated_by else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
