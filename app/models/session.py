"""
Session model for authentication
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Session(Base):
    """
    Session model for session-based authentication
    """
    __tablename__ = "sessions"
    
    id = Column(String(64), primary_key=True)  # Session ID
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship
    user = relationship("User", backref="sessions")
    
    def __repr__(self):
        return f"<Session {self.id} for user {self.user_id}>"
