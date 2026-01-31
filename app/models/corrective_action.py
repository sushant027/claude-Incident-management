"""
Corrective action model
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from app.models import CorrectiveActionStatus

class CorrectiveAction(Base):
    """
    Corrective action - single owner, continuous email reminders
    """
    __tablename__ = "corrective_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(CorrectiveActionStatus), nullable=False, default=CorrectiveActionStatus.OPEN)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    incident = relationship("Incident", backref="corrective_actions")
    owner = relationship("User")
    
    def __repr__(self):
        return f"<CorrectiveAction {self.id}: {self.title[:50]}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "title": self.title,
            "description": self.description,
            "owner_user_id": self.owner_user_id,
            "owner_name": self.owner.name if self.owner else None,
            "owner_email": self.owner.email if self.owner else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
