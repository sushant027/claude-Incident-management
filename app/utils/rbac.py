"""
Role-Based Access Control (RBAC)
"""
from typing import List
from fastapi import HTTPException, status
from app.models import UserRole, IncidentStatus
from app.models.user import User

def check_roles(user: User, allowed_roles: List[UserRole]):
    """
    Check if user has one of the allowed roles
    Raises HTTPException if not authorized
    """
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
        )

def can_acknowledge_incident(user: User) -> bool:
    """Check if user can acknowledge incidents"""
    return user.role in [UserRole.SUPPORT_L2, UserRole.SUPPORT_EXPERT, UserRole.INCIDENT_MANAGER, UserRole.ADMIN]

def can_resolve_incident(user: User) -> bool:
    """Check if user can resolve/close incidents"""
    return user.role in [UserRole.INCIDENT_MANAGER, UserRole.ADMIN]

def can_update_impact_fields(user: User) -> bool:
    """Check if user can update impact fields"""
    return user.role in [UserRole.INCIDENT_MANAGER, UserRole.ADMIN]

def can_manage_architecture(user: User) -> bool:
    """Check if user can create/update/delete architecture"""
    return user.role == UserRole.ADMIN

def can_edit_postmortem(user: User) -> bool:
    """Check if user can edit postmortem"""
    return user.role in [UserRole.INCIDENT_MANAGER, UserRole.ADMIN]

def validate_status_transition(current_status: IncidentStatus, new_status: IncidentStatus, user: User):
    """
    Validate if status transition is allowed
    Raises HTTPException if invalid
    """
    # Define valid transitions
    valid_transitions = {
        IncidentStatus.OPEN: [IncidentStatus.ACKNOWLEDGED],
        IncidentStatus.ACKNOWLEDGED: [IncidentStatus.IN_PROGRESS],
        IncidentStatus.IN_PROGRESS: [IncidentStatus.RESOLVED],
        IncidentStatus.RESOLVED: [IncidentStatus.CLOSED],
        IncidentStatus.CLOSED: []  # Terminal state
    }
    
    # Check if transition is valid
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {current_status.value} to {new_status.value}"
        )
    
    # Check role permissions for status changes
    if new_status == IncidentStatus.ACKNOWLEDGED:
        if not can_acknowledge_incident(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SUPPORT_L2, SUPPORT_EXPERT, INCIDENT_MANAGER, or ADMIN can acknowledge incidents"
            )
    
    elif new_status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
        if not can_resolve_incident(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only INCIDENT_MANAGER or ADMIN can resolve/close incidents"
            )
