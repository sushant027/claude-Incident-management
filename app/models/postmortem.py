"""
Postmortem model
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Postmortem(Base):
    """
    Postmortem - created after incident is resolved/closed
    """
    __tablename__ = "postmortems"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    root_cause = Column(Text, nullable=False)
    resolution_summary = Column(Text, nullable=False)
    preventive_summary = Column(Text, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    incident = relationship("Incident", backref="postmortem")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<Postmortem for incident {self.incident_id}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "root_cause": self.root_cause,
            "resolution_summary": self.resolution_summary,
            "preventive_summary": self.preventive_summary,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.name if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
