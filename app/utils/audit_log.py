"""
Audit logging utility
"""
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditAction
from app.models.audit import Audit

def log_audit(
    db: Session,
    entity_type: str,
    entity_id: Optional[int],
    action: AuditAction,
    description: Optional[str] = None,
    performed_by_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an audit entry
    """
    audit = Audit(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        description=description,
        performed_by_id=performed_by_id,
        extra_data=json.dumps(metadata) if metadata else None
    )
    db.add(audit)
    db.commit()

def log_login(db: Session, user_id: int, success: bool = True):
    """Log user login"""
    log_audit(
        db=db,
        entity_type="USER",
        entity_id=user_id,
        action=AuditAction.LOGIN,
        description="User logged in" if success else "Failed login attempt",
        performed_by_id=user_id
    )

def log_logout(db: Session, user_id: int):
    """Log user logout"""
    log_audit(
        db=db,
        entity_type="USER",
        entity_id=user_id,
        action=AuditAction.LOGOUT,
        description="User logged out",
        performed_by_id=user_id
    )

def log_incident_create(db: Session, incident_id: int, user_id: int):
    """Log incident creation"""
    log_audit(
        db=db,
        entity_type="INCIDENT",
        entity_id=incident_id,
        action=AuditAction.CREATE,
        description="Incident created",
        performed_by_id=user_id
    )

def log_incident_update(db: Session, incident_id: int, user_id: int, changes: Dict[str, Any]):
    """Log incident update"""
    log_audit(
        db=db,
        entity_type="INCIDENT",
        entity_id=incident_id,
        action=AuditAction.UPDATE,
        description="Incident updated",
        performed_by_id=user_id,
        metadata={"changes": changes}
    )

def log_status_change(db: Session, incident_id: int, user_id: int, old_status: str, new_status: str):
    """Log incident status change"""
    log_audit(
        db=db,
        entity_type="INCIDENT",
        entity_id=incident_id,
        action=AuditAction.STATUS_CHANGE,
        description=f"Status changed from {old_status} to {new_status}",
        performed_by_id=user_id,
        metadata={"old_status": old_status, "new_status": new_status}
    )

def log_search(db: Session, user_id: int, search_params: Dict[str, Any], is_ai: bool = False):
    """Log search"""
    action = AuditAction.AI_SEARCH if is_ai else AuditAction.SEARCH
    log_audit(
        db=db,
        entity_type="SEARCH",
        entity_id=None,
        action=action,
        description="AI search performed" if is_ai else "Search performed",
        performed_by_id=user_id,
        metadata=search_params
    )

def log_report_generation(db: Session, user_id: int, report_type: str, params: Dict[str, Any]):
    """Log report generation"""
    log_audit(
        db=db,
        entity_type="REPORT",
        entity_id=None,
        action=AuditAction.GENERATE_REPORT,
        description=f"Generated {report_type} report",
        performed_by_id=user_id,
        metadata=params
    )
