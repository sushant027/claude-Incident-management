"""
Bank options routes - CRUD operations for bank technical configuration
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import get_db
from app.models.bank import Bank
from app.models.bank_option import BankOption
from app.models import UserRole, ReconTechnology
from app.utils.auth import get_current_user
from app.utils.rbac import can_manage_architecture
from app.utils.audit_log import log_audit, AuditAction

router = APIRouter(tags=["bank-options"])


class CreateBankOptionRequest(BaseModel):
    bank_id: int
    transaction_volume_per_day: Optional[int] = None
    transaction_volume_per_month: Optional[int] = None
    architecture_diagram_url: Optional[str] = None
    number_of_app_servers: Optional[int] = None
    app_server_type: Optional[str] = None
    db_type: Optional[str] = None
    number_of_db_instances: Optional[int] = None
    implementation_developer_name: Optional[str] = None
    db_developer_name: Optional[str] = None
    db_developer_contact: Optional[str] = None
    aerospike_enabled: bool = False
    aerospike_version: Optional[str] = None
    aerospike_description: Optional[str] = None
    redis_enabled: bool = False
    redis_description: Optional[str] = None
    recon_enabled: bool = False
    recon_technology: Optional[str] = None


class UpdateBankOptionRequest(BaseModel):
    transaction_volume_per_day: Optional[int] = None
    transaction_volume_per_month: Optional[int] = None
    architecture_diagram_url: Optional[str] = None
    number_of_app_servers: Optional[int] = None
    app_server_type: Optional[str] = None
    db_type: Optional[str] = None
    number_of_db_instances: Optional[int] = None
    implementation_developer_name: Optional[str] = None
    db_developer_name: Optional[str] = None
    db_developer_contact: Optional[str] = None
    aerospike_enabled: Optional[bool] = None
    aerospike_version: Optional[str] = None
    aerospike_description: Optional[str] = None
    redis_enabled: Optional[bool] = None
    redis_description: Optional[str] = None
    recon_enabled: Optional[bool] = None
    recon_technology: Optional[str] = None


@router.get("/bank-options")
async def list_bank_options(request: Request, db: Session = Depends(get_db)):
    """List all bank options"""
    user = get_current_user(request, db)
    bank_options = db.query(BankOption).all()
    return [opt.to_dict() for opt in bank_options]


@router.get("/bank-options/{bank_id}")
async def get_bank_option(
    request: Request,
    bank_id: int,
    db: Session = Depends(get_db)
):
    """Get bank option by bank ID"""
    user = get_current_user(request, db)

    bank_option = db.query(BankOption).filter(BankOption.bank_id == bank_id).first()
    if not bank_option:
        # Return empty structure if not exists
        bank = db.query(Bank).filter(Bank.id == bank_id).first()
        if not bank:
            raise HTTPException(status_code=404, detail="Bank not found")
        return {
            "bank_id": bank_id,
            "bank_name": bank.name,
            "exists": False
        }

    result = bank_option.to_dict()
    result["exists"] = True
    return result


@router.post("/bank-options")
async def create_bank_option(
    request: Request,
    option_data: CreateBankOptionRequest,
    db: Session = Depends(get_db)
):
    """Create bank option (ADMIN only)"""
    user = get_current_user(request, db)

    if not can_manage_architecture(user):
        raise HTTPException(status_code=403, detail="Only ADMIN can create bank options")

    # Validate bank
    bank = db.query(Bank).filter(Bank.id == option_data.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    # Check if option already exists for this bank
    existing = db.query(BankOption).filter(BankOption.bank_id == option_data.bank_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bank option already exists for this bank")

    # Validate recon_technology if provided
    if option_data.recon_technology and option_data.recon_technology not in [e.value for e in ReconTechnology]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid recon_technology. Must be one of: {[e.value for e in ReconTechnology]}"
        )

    bank_option = BankOption(
        bank_id=option_data.bank_id,
        transaction_volume_per_day=option_data.transaction_volume_per_day,
        transaction_volume_per_month=option_data.transaction_volume_per_month,
        architecture_diagram_url=option_data.architecture_diagram_url,
        number_of_app_servers=option_data.number_of_app_servers,
        app_server_type=option_data.app_server_type,
        db_type=option_data.db_type,
        number_of_db_instances=option_data.number_of_db_instances,
        implementation_developer_name=option_data.implementation_developer_name,
        db_developer_name=option_data.db_developer_name,
        db_developer_contact=option_data.db_developer_contact,
        aerospike_enabled=option_data.aerospike_enabled,
        aerospike_version=option_data.aerospike_version,
        aerospike_description=option_data.aerospike_description,
        redis_enabled=option_data.redis_enabled,
        redis_description=option_data.redis_description,
        recon_enabled=option_data.recon_enabled,
        recon_technology=option_data.recon_technology,
        updated_by_id=user.id
    )

    db.add(bank_option)
    db.commit()
    db.refresh(bank_option)

    log_audit(db, "BANK_OPTION", bank_option.id, AuditAction.CREATE, "Bank option created", user.id)

    return bank_option.to_dict()


@router.put("/bank-options/{bank_id}")
async def update_bank_option(
    request: Request,
    bank_id: int,
    update_data: UpdateBankOptionRequest,
    db: Session = Depends(get_db)
):
    """Update bank option (ADMIN only)"""
    user = get_current_user(request, db)

    if not can_manage_architecture(user):
        raise HTTPException(status_code=403, detail="Only ADMIN can update bank options")

    bank_option = db.query(BankOption).filter(BankOption.bank_id == bank_id).first()
    if not bank_option:
        raise HTTPException(status_code=404, detail="Bank option not found")

    # Validate recon_technology if provided
    if update_data.recon_technology is not None and update_data.recon_technology not in [e.value for e in ReconTechnology]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid recon_technology. Must be one of: {[e.value for e in ReconTechnology]}"
        )

    # Update fields
    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(bank_option, field, value)

    bank_option.updated_by_id = user.id

    db.commit()
    db.refresh(bank_option)

    log_audit(db, "BANK_OPTION", bank_option.id, AuditAction.UPDATE, "Bank option updated", user.id)

    return bank_option.to_dict()


@router.delete("/bank-options/{bank_id}")
async def delete_bank_option(
    request: Request,
    bank_id: int,
    db: Session = Depends(get_db)
):
    """Delete bank option (ADMIN only)"""
    user = get_current_user(request, db)

    if not can_manage_architecture(user):
        raise HTTPException(status_code=403, detail="Only ADMIN can delete bank options")

    bank_option = db.query(BankOption).filter(BankOption.bank_id == bank_id).first()
    if not bank_option:
        raise HTTPException(status_code=404, detail="Bank option not found")

    option_id = bank_option.id
    db.delete(bank_option)
    db.commit()

    log_audit(db, "BANK_OPTION", option_id, AuditAction.DELETE, "Bank option deleted", user.id)

    return {"success": True, "message": "Bank option deleted"}
