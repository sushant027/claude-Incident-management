"""
Authentication routes - login, logout
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from app.models.user import User
from app.utils.auth import (
    verify_password,
    create_session,
    delete_session,
    get_current_user
)
from app.utils.audit_log import log_audit, AuditAction
from config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: dict = None


@router.post("/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint - validates credentials and creates session"""
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )

    # Create session
    session_id = create_session(db, user.id)

    # Log audit
    log_audit(db, "USER", user.id, AuditAction.LOGIN, f"User {user.username} logged in", user.id)

    # Create response with session cookie
    response = JSONResponse(content={
        "success": True,
        "message": "Login successful",
        "user": user.to_dict()
    })

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        samesite="lax"
    )

    return response


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """Logout endpoint - destroys session"""
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if session_id:
        # Try to get user for audit logging
        try:
            user = get_current_user(request, db)
            log_audit(db, "USER", user.id, AuditAction.LOGOUT, f"User {user.username} logged out", user.id)
        except HTTPException:
            pass

        delete_session(db, session_id)

    response = JSONResponse(content={
        "success": True,
        "message": "Logged out successfully"
    })

    response.delete_cookie(key=settings.SESSION_COOKIE_NAME)

    return response


@router.get("/me")
async def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user info"""
    user = get_current_user(request, db)
    return user.to_dict()
