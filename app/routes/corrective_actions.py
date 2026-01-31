"""
Corrective actions routes
"""
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import get_db
from app.models import IncidentStatus, CorrectiveActionStatus
from app.models.incident import Incident
from app.models.corrective_action import CorrectiveAction
from app.utils.auth import get_current_user
from app.utils.audit_log import log_audit, AuditAction

router = APIRouter(prefix="/corrective-actions", tags=["corrective_actions"])

class CreateCorrectiveActionRequest(BaseModel):
    incident_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    owner_user_id: int
    due_date: str  # ISO date format

class UpdateCorrectiveActionRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    owner_user_id: Optional[int] = None
    due_date: Optional[str] = None  # ISO date format
    status: Optional[CorrectiveActionStatus] = None

@router.post("")
async def create_corrective_action(
    request: Request,
    action_data: CreateCorrectiveActionRequest,
    db: Session = Depends(get_db)
):
    """
    Create corrective action (only after RESOLVED/CLOSED)
    """
    user = get_current_user(request, db)
    
    # Validate incident
    incident = db.query(Incident).filter(Incident.id == action_data.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
        raise HTTPException(
            status_code=400,
            detail="Corrective actions can only be created for RESOLVED or CLOSED incidents"
        )
    
    # Parse date
    try:
        due_date_obj = date.fromisoformat(action_data.due_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid due_date format (use YYYY-MM-DD)")
    
    # Create action
    action = CorrectiveAction(
        incident_id=action_data.incident_id,
        title=action_data.title,
        description=action_data.description,
        owner_user_id=action_data.owner_user_id,
        due_date=due_date_obj,
        status=CorrectiveActionStatus.OPEN
    )
    
    db.add(action)
    db.commit()
    db.refresh(action)
    
    # Log audit
    log_audit(db, "CORRECTIVE_ACTION", action.id, AuditAction.CREATE, "Corrective action created", user.id)
    
    return action.to_dict()

@router.get("/incident/{incident_id}")
async def get_corrective_actions_by_incident(
    request: Request,
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all corrective actions for incident
    """
    user = get_current_user(request, db)
    
    actions = db.query(CorrectiveAction).filter(
        CorrectiveAction.incident_id == incident_id
    ).all()
    
    return [action.to_dict() for action in actions]

@router.put("/{action_id}")
async def update_corrective_action(
    request: Request,
    action_id: int,
    update_data: UpdateCorrectiveActionRequest,
    db: Session = Depends(get_db)
):
    """
    Update corrective action
    """
    user = get_current_user(request, db)
    
    action = db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    
    # Update fields
    if update_data.title is not None:
        action.title = update_data.title
    if update_data.description is not None:
        action.description = update_data.description
    if update_data.owner_user_id is not None:
        action.owner_user_id = update_data.owner_user_id
    if update_data.due_date is not None:
        try:
            action.due_date = date.fromisoformat(update_data.due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due_date format")
    
    if update_data.status is not None:
        old_status = action.status
        action.status = update_data.status
        
        # Set completed_at if marked as completed
        if update_data.status == CorrectiveActionStatus.COMPLETED and not action.completed_at:
            action.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(action)
    
    # Log audit
    log_audit(db, "CORRECTIVE_ACTION", action.id, AuditAction.UPDATE, "Corrective action updated", user.id)
    
    return action.to_dict()
