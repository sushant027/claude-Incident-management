"""
Incident model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from app.models import IncidentSeverity, IncidentStatus

class Incident(Base):
    """
    Incident model - core entity for incident management
    """
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    exception_text = Column(Text, nullable=True)
    
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(Enum(IncidentSeverity), nullable=False, index=True)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    
    # Assignment
    incident_manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    current_owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    source = Column(String(100), nullable=True)  # e.g., "Manual", "Monitoring", "Email"
    impact_summary = Column(Text, nullable=True)
    
    # Impact fields (only INCIDENT_MANAGER/ADMIN can update)
    downtime = Column(Boolean, nullable=True)
    financial_impact = Column(Boolean, nullable=True)
    technical_decline_pct = Column(Float, nullable=True)  # 0-100
    
    # Relationships
    bank = relationship("Bank", backref="incidents")
    incident_manager = relationship("User", foreign_keys=[incident_manager_id])
    current_owner = relationship("User", foreign_keys=[current_owner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    def __repr__(self):
        return f"<Incident {self.id}: {self.title[:50]}>"
    
    def to_dict(self, include_relationships=True):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "exception_text": self.exception_text,
            "bank_id": self.bank_id,
            "severity": self.severity.value,
            "status": self.status.value,
            "service_name": self.service_name,
            "incident_manager_id": self.incident_manager_id,
            "current_owner_id": self.current_owner_id,
            "created_by_id": self.created_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "source": self.source,
            "impact_summary": self.impact_summary,
            "downtime": self.downtime,
            "financial_impact": self.financial_impact,
            "technical_decline_pct": self.technical_decline_pct
        }
        
        if include_relationships:
            data["bank_name"] = self.bank.name if self.bank else None
            data["incident_manager_name"] = self.incident_manager.name if self.incident_manager else None
            data["current_owner_name"] = self.current_owner.name if self.current_owner else None
            data["created_by_name"] = self.created_by.name if self.created_by else None
        
        return data
