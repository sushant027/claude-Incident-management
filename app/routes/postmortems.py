"""
Postmortem routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import get_db
from app.models import IncidentStatus
from app.models.incident import Incident
from app.models.postmortem import Postmortem
from app.utils.auth import get_current_user
from app.utils.rbac import can_edit_postmortem
from app.utils.audit_log import log_audit, AuditAction

router = APIRouter(prefix="/postmortems", tags=["postmortems"])

class CreatePostmortemRequest(BaseModel):
    incident_id: int
    root_cause: str = Field(..., min_length=1)
    resolution_summary: str = Field(..., min_length=1)
    preventive_summary: str = Field(..., min_length=1)

class UpdatePostmortemRequest(BaseModel):
    root_cause: Optional[str] = Field(None, min_length=1)
    resolution_summary: Optional[str] = Field(None, min_length=1)
    preventive_summary: Optional[str] = Field(None, min_length=1)

@router.post("")
async def create_postmortem(
    request: Request,
    postmortem_data: CreatePostmortemRequest,
    db: Session = Depends(get_db)
):
    """
    Create postmortem for incident (only after RESOLVED/CLOSED)
    """
    user = get_current_user(request, db)
    
    # Check permissions
    if not can_edit_postmortem(user):
        raise HTTPException(
            status_code=403,
            detail="Only INCIDENT_MANAGER or ADMIN can create postmortems"
        )
    
    # Validate incident exists and is resolved/closed
    incident = db.query(Incident).filter(Incident.id == postmortem_data.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
        raise HTTPException(
            status_code=400,
            detail="Postmortem can only be created for RESOLVED or CLOSED incidents"
        )
    
    # Check if postmortem already exists
    existing = db.query(Postmortem).filter(Postmortem.incident_id == postmortem_data.incident_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Postmortem already exists for this incident")
    
    # Create postmortem
    postmortem = Postmortem(
        incident_id=postmortem_data.incident_id,
        root_cause=postmortem_data.root_cause,
        resolution_summary=postmortem_data.resolution_summary,
        preventive_summary=postmortem_data.preventive_summary,
        created_by_id=user.id
    )
    
    db.add(postmortem)
    db.commit()
    db.refresh(postmortem)
    
    # Log audit
    log_audit(db, "POSTMORTEM", postmortem.id, AuditAction.CREATE, "Postmortem created", user.id)
    
    return postmortem.to_dict()

@router.get("/incident/{incident_id}")
async def get_postmortem_by_incident(
    request: Request,
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Get postmortem for incident
    """
    user = get_current_user(request, db)
    
    postmortem = db.query(Postmortem).filter(Postmortem.incident_id == incident_id).first()
    if not postmortem:
        raise HTTPException(status_code=404, detail="Postmortem not found")
    
    return postmortem.to_dict()

@router.put("/{postmortem_id}")
async def update_postmortem(
    request: Request,
    postmortem_id: int,
    update_data: UpdatePostmortemRequest,
    db: Session = Depends(get_db)
):
    """
    Update postmortem
    """
    user = get_current_user(request, db)
    
    # Check permissions
    if not can_edit_postmortem(user):
        raise HTTPException(
            status_code=403,
            detail="Only INCIDENT_MANAGER or ADMIN can edit postmortems"
        )
    
    postmortem = db.query(Postmortem).filter(Postmortem.id == postmortem_id).first()
    if not postmortem:
        raise HTTPException(status_code=404, detail="Postmortem not found")
    
    # Update fields
    if update_data.root_cause is not None:
        postmortem.root_cause = update_data.root_cause
    if update_data.resolution_summary is not None:
        postmortem.resolution_summary = update_data.resolution_summary
    if update_data.preventive_summary is not None:
        postmortem.preventive_summary = update_data.preventive_summary
    
    db.commit()
    db.refresh(postmortem)
    
    # Log audit
    log_audit(db, "POSTMORTEM", postmortem.id, AuditAction.UPDATE, "Postmortem updated", user.id)
    
    return postmortem.to_dict()
