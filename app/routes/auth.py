"""
Authentication utilities
"""
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.session import Session as DBSession
from config import settings

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_session(db: Session, user_id: int) -> str:
    """Create new session for user"""
    session_id = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_EXPIRE_HOURS)
    
    db_session = DBSession(
        id=session_id,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(db_session)
    db.commit()
    
    return session_id

def get_session(db: Session, session_id: str) -> Optional[DBSession]:
    """Get session by ID"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    
    if not session:
        return None
    
    # Check if expired
    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        return None
    
    return session

def delete_session(db: Session, session_id: str):
    """Delete session (logout)"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()

def get_current_user(request: Request, db: Session) -> User:
    """
    Get current user from session
    Raises HTTPException if not authenticated
    """
    # Try cookie first, then header
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not session_id:
        session_id = request.headers.get("X-Session-ID")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

def get_optional_user(request: Request, db: Session) -> Optional[User]:
    """
    Get current user from session, return None if not authenticated
    """
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None
