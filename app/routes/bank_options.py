"""
Bank options routes - CRUD operations for bank technical configuration
"""
from typing import Optional, List, Any
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

router = APIRouter(prefix="/api", tags=["bank-options"])


class CreateBankOptionRequest(BaseModel):
    bank_id: int
    # Transaction volume
    transaction_volume_per_day: Optional[int] = None
    transaction_volume_per_month: Optional[int] = None
    peak_tps: Optional[int] = None
    # Architecture
    architecture_diagram_url: Optional[str] = None
    # App server
    number_of_app_servers: Optional[int] = None
    app_server_type: Optional[str] = None
    app_server_cpu: Optional[str] = None
    app_server_memory: Optional[str] = None
    app_server_os: Optional[str] = None
    # Database
    db_type: Optional[str] = None
    number_of_db_instances: Optional[int] = None
    db_server_cpu: Optional[str] = None
    db_server_memory: Optional[str] = None
    db_server_storage: Optional[str] = None
    db_server_os: Optional[str] = None
    # Aerospike
    aerospike_enabled: bool = False
    aerospike_version: Optional[str] = None
    number_of_aerospike_servers: Optional[int] = None
    aerospike_server_cpu: Optional[str] = None
    aerospike_server_memory: Optional[str] = None
    aerospike_server_storage: Optional[str] = None
    aerospike_server_os: Optional[str] = None
    aerospike_description: Optional[str] = None
    # Redis
    redis_enabled: bool = False
    redis_version: Optional[str] = None
    number_of_redis_servers: Optional[int] = None
    redis_server_memory: Optional[str] = None
    redis_description: Optional[str] = None
    # Load Balancer
    load_balancer_type: Optional[str] = None
    number_of_load_balancers: Optional[int] = None
    # Monitoring & Logging
    monitoring_tool: Optional[str] = None
    logging_tool: Optional[str] = None
    # Network & Security
    network_zone: Optional[str] = None
    ssl_certificate_expiry: Optional[str] = None
    waf_enabled: bool = False
    # Environment & DR
    deployment_region: Optional[str] = None
    data_center: Optional[str] = None
    dr_enabled: bool = False
    dr_location: Optional[str] = None
    # SLA
    uptime_sla: Optional[str] = None
    rto: Optional[str] = None
    rpo: Optional[str] = None
    # Recon
    recon_enabled: bool = False
    recon_technology: Optional[str] = None
    # Contacts
    implementation_developer_name: Optional[str] = None
    implementation_developer_contact: Optional[str] = None
    db_developer_name: Optional[str] = None
    db_developer_contact: Optional[str] = None
    ops_team_contact: Optional[str] = None
    # Kubernetes
    kubernetes_enabled: bool = False
    kubernetes_deployments: Optional[List[Any]] = None


class UpdateBankOptionRequest(BaseModel):
    # Transaction volume
    transaction_volume_per_day: Optional[int] = None
    transaction_volume_per_month: Optional[int] = None
    peak_tps: Optional[int] = None
    # Architecture
    architecture_diagram_url: Optional[str] = None
    # App server
    number_of_app_servers: Optional[int] = None
    app_server_type: Optional[str] = None
    app_server_cpu: Optional[str] = None
    app_server_memory: Optional[str] = None
    app_server_os: Optional[str] = None
    # Database
    db_type: Optional[str] = None
    number_of_db_instances: Optional[int] = None
    db_server_cpu: Optional[str] = None
    db_server_memory: Optional[str] = None
    db_server_storage: Optional[str] = None
    db_server_os: Optional[str] = None
    # Aerospike
    aerospike_enabled: Optional[bool] = None
    aerospike_version: Optional[str] = None
    number_of_aerospike_servers: Optional[int] = None
    aerospike_server_cpu: Optional[str] = None
    aerospike_server_memory: Optional[str] = None
    aerospike_server_storage: Optional[str] = None
    aerospike_server_os: Optional[str] = None
    aerospike_description: Optional[str] = None
    # Redis
    redis_enabled: Optional[bool] = None
    redis_version: Optional[str] = None
    number_of_redis_servers: Optional[int] = None
    redis_server_memory: Optional[str] = None
    redis_description: Optional[str] = None
    # Load Balancer
    load_balancer_type: Optional[str] = None
    number_of_load_balancers: Optional[int] = None
    # Monitoring & Logging
    monitoring_tool: Optional[str] = None
    logging_tool: Optional[str] = None
    # Network & Security
    network_zone: Optional[str] = None
    ssl_certificate_expiry: Optional[str] = None
    waf_enabled: Optional[bool] = None
    # Environment & DR
    deployment_region: Optional[str] = None
    data_center: Optional[str] = None
    dr_enabled: Optional[bool] = None
    dr_location: Optional[str] = None
    # SLA
    uptime_sla: Optional[str] = None
    rto: Optional[str] = None
    rpo: Optional[str] = None
    # Recon
    recon_enabled: Optional[bool] = None
    recon_technology: Optional[str] = None
    # Contacts
    implementation_developer_name: Optional[str] = None
    implementation_developer_contact: Optional[str] = None
    db_developer_name: Optional[str] = None
    db_developer_contact: Optional[str] = None
    ops_team_contact: Optional[str] = None
    # Kubernetes
    kubernetes_enabled: Optional[bool] = None
    kubernetes_deployments: Optional[List[Any]] = None


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
        # Transaction volume
        transaction_volume_per_day=option_data.transaction_volume_per_day,
        transaction_volume_per_month=option_data.transaction_volume_per_month,
        peak_tps=option_data.peak_tps,
        # Architecture
        architecture_diagram_url=option_data.architecture_diagram_url,
        # App server
        number_of_app_servers=option_data.number_of_app_servers,
        app_server_type=option_data.app_server_type,
        app_server_cpu=option_data.app_server_cpu,
        app_server_memory=option_data.app_server_memory,
        app_server_os=option_data.app_server_os,
        # Database
        db_type=option_data.db_type,
        number_of_db_instances=option_data.number_of_db_instances,
        db_server_cpu=option_data.db_server_cpu,
        db_server_memory=option_data.db_server_memory,
        db_server_storage=option_data.db_server_storage,
        db_server_os=option_data.db_server_os,
        # Aerospike
        aerospike_enabled=option_data.aerospike_enabled,
        aerospike_version=option_data.aerospike_version,
        number_of_aerospike_servers=option_data.number_of_aerospike_servers,
        aerospike_server_cpu=option_data.aerospike_server_cpu,
        aerospike_server_memory=option_data.aerospike_server_memory,
        aerospike_server_storage=option_data.aerospike_server_storage,
        aerospike_server_os=option_data.aerospike_server_os,
        aerospike_description=option_data.aerospike_description,
        # Redis
        redis_enabled=option_data.redis_enabled,
        redis_version=option_data.redis_version,
        number_of_redis_servers=option_data.number_of_redis_servers,
        redis_server_memory=option_data.redis_server_memory,
        redis_description=option_data.redis_description,
        # Load Balancer
        load_balancer_type=option_data.load_balancer_type,
        number_of_load_balancers=option_data.number_of_load_balancers,
        # Monitoring & Logging
        monitoring_tool=option_data.monitoring_tool,
        logging_tool=option_data.logging_tool,
        # Network & Security
        network_zone=option_data.network_zone,
        ssl_certificate_expiry=option_data.ssl_certificate_expiry,
        waf_enabled=option_data.waf_enabled,
        # Environment & DR
        deployment_region=option_data.deployment_region,
        data_center=option_data.data_center,
        dr_enabled=option_data.dr_enabled,
        dr_location=option_data.dr_location,
        # SLA
        uptime_sla=option_data.uptime_sla,
        rto=option_data.rto,
        rpo=option_data.rpo,
        # Recon
        recon_enabled=option_data.recon_enabled,
        recon_technology=option_data.recon_technology,
        # Contacts
        implementation_developer_name=option_data.implementation_developer_name,
        implementation_developer_contact=option_data.implementation_developer_contact,
        db_developer_name=option_data.db_developer_name,
        db_developer_contact=option_data.db_developer_contact,
        ops_team_contact=option_data.ops_team_contact,
        # Kubernetes
        kubernetes_enabled=option_data.kubernetes_enabled,
        kubernetes_deployments=option_data.kubernetes_deployments,
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
