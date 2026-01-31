"""
Models package - contains all SQLAlchemy models and enums
"""
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "ADMIN"
    INCIDENT_MANAGER = "INCIDENT_MANAGER"
    SME = "SME"
    SUPPORT_L2 = "SUPPORT_L2"
    SUPPORT_EXPERT = "SUPPORT_EXPERT"


class IncidentStatus(str, Enum):
    """Incident workflow status"""
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class CorrectiveActionStatus(str, Enum):
    """Corrective action status"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class AuditAction(str, Enum):
    """Audit log action types"""
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    STATUS_CHANGE = "STATUS_CHANGE"
    SEARCH = "SEARCH"
    AI_SEARCH = "AI_SEARCH"
    GENERATE_REPORT = "GENERATE_REPORT"
    COMMENT = "COMMENT"
