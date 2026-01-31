"""
Incident timeline model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class IncidentTimeline(Base):
    """
    Incident timeline - tracks all changes and activities
    """
    __tablename__ = "incident_timeline"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # STATUS_CHANGE, ASSIGNMENT, ESCALATION, COMMENT, AI_RECOMMENDATION
    event_description = Column(Text, nullable=False)
    performed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Optional metadata
    old_value = Column(String(100), nullable=True)
    new_value = Column(String(100), nullable=True)
    
    # Relationships
    incident = relationship("Incident", backref="timeline")
    performed_by = relationship("User")
    
    def __repr__(self):
        return f"<Timeline {self.id}: {self.event_type} for incident {self.incident_id}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "event_type": self.event_type,
            "event_description": self.event_description,
            "performed_by_id": self.performed_by_id,
            "performed_by_name": self.performed_by.name if self.performed_by else "System",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "old_value": self.old_value,
            "new_value": self.new_value
        }
