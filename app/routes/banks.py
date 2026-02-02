"""
Bank and architecture routes
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import get_db
from app.models.bank import Bank
from app.models.bank_architecture import BankArchitecture
from app.models import UserRole
from app.utils.auth import get_current_user
from app.utils.rbac import can_manage_architecture
from app.utils.audit_log import log_audit, AuditAction

router = APIRouter(tags=["banks"])


# Bank request models
class CreateBankRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


# Bank routes
@router.get("/banks")
async def list_banks(request: Request, db: Session = Depends(get_db)):
    """List all banks"""
    user = get_current_user(request, db)
    banks = db.query(Bank).filter(Bank.active == True).all()
    return [bank.to_dict() for bank in banks]


@router.post("/banks")
async def create_bank(
    request: Request,
    bank_data: CreateBankRequest,
    db: Session = Depends(get_db)
):
    """Create a new bank (ADMIN only)"""
    user = get_current_user(request, db)

    if not can_manage_architecture(user):
        raise HTTPException(status_code=403, detail="Only ADMIN can create banks")

    # Check if bank with same name exists
    existing = db.query(Bank).filter(Bank.name == bank_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bank with this name already exists")

    bank = Bank(name=bank_data.name, active=True)
    db.add(bank)
    db.commit()
    db.refresh(bank)

    log_audit(db, "BANK", bank.id, AuditAction.CREATE, f"Bank '{bank.name}' created", user.id)

    return bank.to_dict()

# Architecture routes
class CreateArchitectureRequest(BaseModel):
    bank_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    diagram_reference: Optional[str] = None

class UpdateArchitectureRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    diagram_reference: Optional[str] = None

@router.post("/architectures")
async def create_architecture(
    request: Request,
    arch_data: CreateArchitectureRequest,
    db: Session = Depends(get_db)
):
    """Create bank architecture (ADMIN only)"""
    user = get_current_user(request, db)
    
    if not can_manage_architecture(user):
        raise HTTPException(status_code=403, detail="Only ADMIN can create architecture")
    
    # Validate bank
    bank = db.query(Bank).filter(Bank.id == arch_data.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    architecture = BankArchitecture(
        bank_id=arch_data.bank_id,
        title=arch_data.title,
        description=arch_data.description,
        diagram_reference=arch_data.diagram_reference,
        updated_by_id=user.id
    )
    
    db.add(architecture)
    db.commit()
    db.refresh(architecture)
    
    log_audit(db, "ARCHITECTURE", architecture.id, AuditAction.CREATE, "Architecture created", user.id)
    
    return architecture.to_dict()

@router.get("/banks/{bank_id}/architectures")
async def get_bank_architectures(
    request: Request,
    bank_id: int,
    db: Session = Depends(get_db)
):
    """Get all architectures for a bank"""
    user = get_current_user(request, db)
    
    architectures = db.query(BankArchitecture).filter(
        BankArchitecture.bank_id == bank_id
    ).all()
    
    return [arch.to_dict() for arch in architectures]

@router.put("/architectures/{arch_id}")
async def update_architecture(
    request: Request,
    arch_id: int,
    update_data: UpdateArchitectureRequest,
    db: Session = Depends(get_db)
):
    """Update architecture (ADMIN only)"""
    user = get_current_user(request, db)
    
    if not can_manage_architecture(user):
        raise HTTPException(status_code=403, detail="Only ADMIN can update architecture")
    
    architecture = db.query(BankArchitecture).filter(BankArchitecture.id == arch_id).first()
    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")
    
    if update_data.title is not None:
        architecture.title = update_data.title
    if update_data.description is not None:
        architecture.description = update_data.description
    if update_data.diagram_reference is not None:
        architecture.diagram_reference = update_data.diagram_reference
    
    architecture.updated_by_id = user.id
    
    db.commit()
    db.refresh(architecture)
    
    log_audit(db, "ARCHITECTURE", architecture.id, AuditAction.UPDATE, "Architecture updated", user.id)
    
    return architecture.to_dict()

@router.delete("/architectures/{arch_id}")
async def delete_architecture(
    request: Request,
    arch_id: int,
    db: Session = Depends(get_db)
):
    """Delete architecture (ADMIN only)"""
    user = get_current_user(request, db)
    
    if not can_manage_architecture(user):
        raise HTTPException(status_code=403, detail="Only ADMIN can delete architecture")
    
    architecture = db.query(BankArchitecture).filter(BankArchitecture.id == arch_id).first()
    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")
    
    db.delete(architecture)
    db.commit()
    
    log_audit(db, "ARCHITECTURE", arch_id, AuditAction.DELETE, "Architecture deleted", user.id)
    
    return {"success": True, "message": "Architecture deleted"}
