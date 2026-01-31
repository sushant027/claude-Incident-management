"""
AI Similar Incidents model
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class AISimilarIncident(Base):
    """
    AI-generated similar incidents and recommendations
    """
    __tablename__ = "ai_similar_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    similar_incident_ids = Column(Text, nullable=True)  # JSON array of IDs
    similarity_reasons = Column(Text, nullable=True)  # JSON object mapping ID to reason
    recommendation_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    incident = relationship("Incident", backref="ai_similar_incidents")
    
    def __repr__(self):
        return f"<AISimilarIncident for incident {self.incident_id}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "similar_incident_ids": json.loads(self.similar_incident_ids) if self.similar_incident_ids else [],
            "similarity_reasons": json.loads(self.similarity_reasons) if self.similarity_reasons else {},
            "recommendation_text": self.recommendation_text,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
