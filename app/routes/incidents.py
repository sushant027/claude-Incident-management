"""
Incident routes - CRUD and workflow management
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel, Field
from database import get_db
from app.models import IncidentStatus, IncidentSeverity, UserRole
from app.models.incident import Incident
from app.models.incident_timeline import IncidentTimeline
from app.models.bank import Bank
from app.models.user import User
from app.models.ai_similar_incident import AISimilarIncident
from app.utils.auth import get_current_user
from app.utils.rbac import validate_status_transition, can_update_impact_fields, check_roles
from app.utils.audit_log import log_incident_create, log_incident_update, log_status_change, log_audit
from app.services.ai_service import ai_service
from config import settings
import json

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Request/Response Models
class CreateIncidentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    exception_text: Optional[str] = None
    bank_id: int
    severity: IncidentSeverity
    service_name: str = Field(..., min_length=1, max_length=100)
    incident_manager_id: Optional[int] = None
    source: Optional[str] = None
    impact_summary: Optional[str] = None

class UpdateIncidentRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    exception_text: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    service_name: Optional[str] = Field(None, min_length=1, max_length=100)
    incident_manager_id: Optional[int] = None
    current_owner_id: Optional[int] = None
    impact_summary: Optional[str] = None
    downtime: Optional[bool] = None
    financial_impact: Optional[bool] = None
    technical_decline_pct: Optional[float] = Field(None, ge=0, le=100)

class UpdateStatusRequest(BaseModel):
    status: IncidentStatus
    comment: Optional[str] = None

class AddCommentRequest(BaseModel):
    comment: str = Field(..., min_length=1)

@router.post("")
async def create_incident(
    request: Request,
    incident_data: CreateIncidentRequest,
    db: Session = Depends(get_db)
):
    """
    Create new incident
    """
    user = get_current_user(request, db)
    
    # Validate bank exists
    bank = db.query(Bank).filter(Bank.id == incident_data.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    # Validate incident manager if provided
    if incident_data.incident_manager_id:
        manager = db.query(User).filter(User.id == incident_data.incident_manager_id).first()
        if not manager or manager.role not in [UserRole.INCIDENT_MANAGER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=400,
                detail="Invalid incident manager (must be INCIDENT_MANAGER or ADMIN)"
            )
    
    # Create incident
    incident = Incident(
        title=incident_data.title,
        description=incident_data.description,
        exception_text=incident_data.exception_text,
        bank_id=incident_data.bank_id,
        severity=incident_data.severity,
        status=IncidentStatus.OPEN,
        service_name=incident_data.service_name,
        incident_manager_id=incident_data.incident_manager_id,
        created_by_id=user.id,
        source=incident_data.source or "Manual",
        impact_summary=incident_data.impact_summary
    )
    
    db.add(incident)
    db.flush()
    
    # Add timeline entry
    timeline = IncidentTimeline(
        incident_id=incident.id,
        event_type="CREATE",
        event_description=f"Incident created by {user.name}",
        performed_by_id=user.id
    )
    db.add(timeline)
    
    db.commit()
    db.refresh(incident)
    
    # Log audit
    log_incident_create(db, incident.id, user.id)
    
    # Trigger AI similar incident search (async in background)
    try:
        _run_ai_similar_search(db, incident)
    except Exception as e:
        print(f"AI search error: {str(e)}")
    
    return incident.to_dict()

@router.get("")
async def list_incidents(
    request: Request,
    bank_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List incidents with filtering
    """
    user = get_current_user(request, db)
    
    # Build query
    query = db.query(Incident)
    
    if bank_id:
        query = query.filter(Incident.bank_id == bank_id)
    
    if status:
        try:
            query = query.filter(Incident.status == IncidentStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if severity:
        try:
            query = query.filter(Incident.severity == IncidentSeverity(severity))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid severity")
    
    # Get total count
    total = query.count()
    
    # Paginate
    query = query.order_by(Incident.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    incidents = query.all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "incidents": [inc.to_dict() for inc in incidents]
    }

@router.get("/{incident_id}")
async def get_incident(
    request: Request,
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Get incident details including timeline
    """
    user = get_current_user(request, db)
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get timeline
    timeline = db.query(IncidentTimeline).filter(
        IncidentTimeline.incident_id == incident_id
    ).order_by(IncidentTimeline.created_at.asc()).all()
    
    # Get AI similar incidents
    ai_similar = db.query(AISimilarIncident).filter(
        AISimilarIncident.incident_id == incident_id
    ).first()
    
    result = incident.to_dict()
    result["timeline"] = [t.to_dict() for t in timeline]
    result["ai_similar"] = ai_similar.to_dict() if ai_similar else None
    
    return result

@router.put("/{incident_id}")
async def update_incident(
    request: Request,
    incident_id: int,
    update_data: UpdateIncidentRequest,
    db: Session = Depends(get_db)
):
    """
    Update incident details
    """
    user = get_current_user(request, db)
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Track changes
    changes = {}
    
    # Update basic fields
    if update_data.title is not None:
        changes["title"] = {"old": incident.title, "new": update_data.title}
        incident.title = update_data.title
    
    if update_data.description is not None:
        changes["description"] = {"old": incident.description[:50], "new": update_data.description[:50]}
        incident.description = update_data.description
    
    if update_data.exception_text is not None:
        incident.exception_text = update_data.exception_text
    
    if update_data.severity is not None:
        changes["severity"] = {"old": incident.severity.value, "new": update_data.severity.value}
        incident.severity = update_data.severity
    
    if update_data.service_name is not None:
        changes["service_name"] = {"old": incident.service_name, "new": update_data.service_name}
        incident.service_name = update_data.service_name
    
    if update_data.impact_summary is not None:
        incident.impact_summary = update_data.impact_summary
    
    # Update impact fields (restricted to INCIDENT_MANAGER/ADMIN)
    impact_fields = ["downtime", "financial_impact", "technical_decline_pct"]
    impact_updated = any([getattr(update_data, f) is not None for f in impact_fields])
    
    if impact_updated:
        if not can_update_impact_fields(user):
            raise HTTPException(
                status_code=403,
                detail="Only INCIDENT_MANAGER or ADMIN can update impact fields"
            )
        
        if update_data.downtime is not None:
            incident.downtime = update_data.downtime
        if update_data.financial_impact is not None:
            incident.financial_impact = update_data.financial_impact
        if update_data.technical_decline_pct is not None:
            incident.technical_decline_pct = update_data.technical_decline_pct
    
    # Update assignments
    if update_data.incident_manager_id is not None:
        old_manager = incident.incident_manager.name if incident.incident_manager else "None"
        manager = db.query(User).filter(User.id == update_data.incident_manager_id).first()
        if manager and manager.role in [UserRole.INCIDENT_MANAGER, UserRole.ADMIN]:
            incident.incident_manager_id = update_data.incident_manager_id
            changes["incident_manager"] = {"old": old_manager, "new": manager.name}
            
            # Timeline
            timeline = IncidentTimeline(
                incident_id=incident_id,
                event_type="ASSIGNMENT",
                event_description=f"Incident manager changed to {manager.name}",
                performed_by_id=user.id
            )
            db.add(timeline)
    
    if update_data.current_owner_id is not None:
        old_owner = incident.current_owner.name if incident.current_owner else "None"
        owner = db.query(User).filter(User.id == update_data.current_owner_id).first()
        if owner:
            incident.current_owner_id = update_data.current_owner_id
            changes["current_owner"] = {"old": old_owner, "new": owner.name}
            
            # Timeline
            timeline = IncidentTimeline(
                incident_id=incident_id,
                event_type="ASSIGNMENT",
                event_description=f"Current owner changed to {owner.name}",
                performed_by_id=user.id
            )
            db.add(timeline)
    
    db.commit()
    db.refresh(incident)
    
    # Log audit
    if changes:
        log_incident_update(db, incident.id, user.id, changes)
    
    return incident.to_dict()

def _run_ai_similar_search(db: Session, incident: Incident):
    """
    Run AI similar incident search
    """
    if not ai_service.enabled:
        return
    
    # Get historical resolved/closed incidents from same bank
    historical = db.query(Incident).filter(
        and_(
            Incident.bank_id == incident.bank_id,
            Incident.status.in_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED]),
            Incident.id != incident.id
        )
    ).order_by(Incident.created_at.desc()).limit(50).all()
    
    if not historical:
        return
    
    # Run AI search
    result = ai_service.find_similar_incidents(
        title=incident.title,
        description=incident.description,
        exception_text=incident.exception_text,
        service_name=incident.service_name,
        historical_incidents=[h.to_dict(include_relationships=False) for h in historical]
    )
    
    # Store results
    ai_similar = AISimilarIncident(
        incident_id=incident.id,
        similar_incident_ids=json.dumps(result.get("similar_incidents", [])),
        similarity_reasons=json.dumps(result.get("similarity_reasons", {})),
        recommendation_text=result.get("recommendation_text", "")
    )
    db.add(ai_similar)
    
    # Add timeline entry
    if result.get("similar_incidents"):
        timeline = IncidentTimeline(
            incident_id=incident.id,
            event_type="AI_RECOMMENDATION",
            event_description=f"AI found {len(result['similar_incidents'])} similar incidents",
            performed_by_id=None  # System
        )
        db.add(timeline)
    
    db.commit()

@router.post("/{incident_id}/status")
async def update_incident_status(
    request: Request,
    incident_id: int,
    status_data: UpdateStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Update incident status (enforces workflow)
    """
    user = get_current_user(request, db)
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    old_status = incident.status
    new_status = status_data.status
    
    # Validate transition
    validate_status_transition(old_status, new_status, user)
    
    # Update status
    incident.status = new_status
    
    # Update timestamps
    if new_status == IncidentStatus.ACKNOWLEDGED:
        incident.acknowledged_at = datetime.utcnow()
    elif new_status == IncidentStatus.RESOLVED:
        incident.resolved_at = datetime.utcnow()
    elif new_status == IncidentStatus.CLOSED:
        incident.closed_at = datetime.utcnow()
    
    # Add timeline entry
    description = f"Status changed from {old_status.value} to {new_status.value}"
    if status_data.comment:
        description += f": {status_data.comment}"
    
    timeline = IncidentTimeline(
        incident_id=incident_id,
        event_type="STATUS_CHANGE",
        event_description=description,
        performed_by_id=user.id,
        old_value=old_status.value,
        new_value=new_status.value
    )
    db.add(timeline)
    
    db.commit()
    db.refresh(incident)
    
    # Log audit
    log_status_change(db, incident.id, user.id, old_status.value, new_status.value)
    
    return incident.to_dict()

@router.post("/{incident_id}/comments")
async def add_comment(
    request: Request,
    incident_id: int,
    comment_data: AddCommentRequest,
    db: Session = Depends(get_db)
):
    """
    Add comment to incident timeline
    """
    user = get_current_user(request, db)
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Add timeline entry
    timeline = IncidentTimeline(
        incident_id=incident_id,
        event_type="COMMENT",
        event_description=comment_data.comment,
        performed_by_id=user.id
    )
    db.add(timeline)
    db.commit()
    
    from app.utils.audit_log import AuditAction
    log_audit(db, "INCIDENT", incident_id, AuditAction.COMMENT, "Comment added", user.id)
    
    return {"success": True, "message": "Comment added"}

@router.get("/search/advanced")
async def search_incidents(
    request: Request,
    title: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    exception_text: Optional[str] = Query(None),
    service_name: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    bank_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    downtime: Optional[bool] = Query(None),
    financial_impact: Optional[bool] = Query(None),
    tech_decline_min: Optional[float] = Query(None),
    tech_decline_max: Optional[float] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Advanced SQL-based incident search
    """
    user = get_current_user(request, db)
    
    # Build query
    query = db.query(Incident)
    
    # Text filters (case-insensitive LIKE)
    if title:
        query = query.filter(Incident.title.ilike(f"%{title}%"))
    if description:
        query = query.filter(Incident.description.ilike(f"%{description}%"))
    if exception_text:
        query = query.filter(Incident.exception_text.ilike(f"%{exception_text}%"))
    if service_name:
        query = query.filter(Incident.service_name.ilike(f"%{service_name}%"))
    
    # Enum filters
    if severity:
        try:
            query = query.filter(Incident.severity == IncidentSeverity(severity))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid severity")
    
    if status:
        try:
            query = query.filter(Incident.status == IncidentStatus(status))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    # Boolean filters
    if downtime is not None:
        query = query.filter(Incident.downtime == downtime)
    if financial_impact is not None:
        query = query.filter(Incident.financial_impact == financial_impact)
    
    # Numeric range
    if tech_decline_min is not None:
        query = query.filter(Incident.technical_decline_pct >= tech_decline_min)
    if tech_decline_max is not None:
        query = query.filter(Incident.technical_decline_pct <= tech_decline_max)
    
    # Bank filter
    if bank_id:
        query = query.filter(Incident.bank_id == bank_id)
    
    # Date range
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.filter(Incident.created_at >= date_from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            query = query.filter(Incident.created_at <= date_to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")
    
    # Count total
    total = query.count()
    
    # Paginate
    query = query.order_by(Incident.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    incidents = query.all()
    
    # Log search
    from app.utils.audit_log import log_search
    search_params = {
        "title": title, "description": description, "service_name": service_name,
        "severity": severity, "status": status, "bank_id": bank_id
    }
    log_search(db, user.id, search_params, is_ai=False)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "incidents": [inc.to_dict() for inc in incidents]
    }

@router.post("/{incident_id}/ai-search")
async def trigger_ai_search(
    request: Request,
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger AI similar incident search
    """
    user = get_current_user(request, db)
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if not ai_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI service not available. Please configure GEMINI_API_KEY"
        )
    
    try:
        _run_ai_similar_search(db, incident)
        
        # Log search
        from app.utils.audit_log import log_search
        log_search(db, user.id, {"incident_id": incident_id}, is_ai=True)
        
        return {"success": True, "message": "AI search completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI search failed: {str(e)}")
