"""
Audit log model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from app.models import AuditAction

class Audit(Base):
    """
    Audit log - tracks all important actions
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # USER, INCIDENT, CORRECTIVE_ACTION, etc.
    entity_id = Column(Integer, nullable=True, index=True)
    action = Column(Enum(AuditAction), nullable=False, index=True)
    description = Column(Text, nullable=True)
    performed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Optional extra data (JSON-serialized)
    extra_data = Column(Text, nullable=True)
    
    # Relationships
    performed_by = relationship("User")
    
    def __repr__(self):
        return f"<Audit {self.id}: {self.action} on {self.entity_type}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action.value,
            "description": self.description,
            "performed_by_id": self.performed_by_id,
            "performed_by_name": self.performed_by.name if self.performed_by else "System",
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "extra_data": json.loads(self.extra_data) if self.extra_data else None
        }
