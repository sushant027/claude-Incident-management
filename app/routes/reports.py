"""
Reports routes - AI-generated HTML reports
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from app.models import IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.models.bank import Bank
from app.utils.auth import get_current_user
from app.utils.audit_log import log_report_generation
from app.services.ai_service import ai_service

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/bank/{bank_id}", response_class=HTMLResponse)
async def generate_bank_report(
    request: Request,
    bank_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered HTML report for a bank
    """
    user = get_current_user(request, db)
    
    # Validate bank
    bank = db.query(Bank).filter(Bank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    # Get incidents
    incidents = db.query(Incident).filter(Incident.bank_id == bank_id).all()
    
    # Calculate summary stats
    stats = {
        "total": len(incidents),
        "open": sum(1 for i in incidents if i.status == IncidentStatus.OPEN),
        "acknowledged": sum(1 for i in incidents if i.status == IncidentStatus.ACKNOWLEDGED),
        "in_progress": sum(1 for i in incidents if i.status == IncidentStatus.IN_PROGRESS),
        "resolved": sum(1 for i in incidents if i.status == IncidentStatus.RESOLVED),
        "closed": sum(1 for i in incidents if i.status == IncidentStatus.CLOSED),
        "p1": sum(1 for i in incidents if i.severity == IncidentSeverity.P1),
        "p2": sum(1 for i in incidents if i.severity == IncidentSeverity.P2),
        "p3": sum(1 for i in incidents if i.severity == IncidentSeverity.P3),
        "p4": sum(1 for i in incidents if i.severity == IncidentSeverity.P4),
    }
    
    # Generate HTML report using AI
    html = ai_service.generate_bank_report(
        bank_name=bank.name,
        incidents=[i.to_dict() for i in incidents],
        summary_stats=stats
    )
    
    # Log report generation
    log_report_generation(db, user.id, "bank_report", {"bank_id": bank_id})
    
    return HTMLResponse(content=html)

@router.get("/incident/{incident_id}", response_class=HTMLResponse)
async def generate_incident_report(
    request: Request,
    incident_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered HTML report for an incident
    """
    user = get_current_user(request, db)
    
    # Get incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Generate HTML report using AI
    html = ai_service.generate_incident_report(incident.to_dict())
    
    # Log report generation
    log_report_generation(db, user.id, "incident_report", {"incident_id": incident_id})
    
    return HTMLResponse(content=html)
