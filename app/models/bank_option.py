"""
Bank Option model - Stores bank technical configuration and infrastructure details
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class BankOption(Base):
    """
    Bank option/configuration model containing technical infrastructure details
    """
    __tablename__ = "bank_options"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("banks.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Transaction volumes
    transaction_volume_per_day = Column(Integer, nullable=True)
    transaction_volume_per_month = Column(Integer, nullable=True)
    peak_tps = Column(Integer, nullable=True)  # Peak transactions per second

    # Architecture
    architecture_diagram_url = Column(String(500), nullable=True)

    # App server details
    number_of_app_servers = Column(Integer, nullable=True)
    app_server_type = Column(String(100), nullable=True)  # e.g., Tomcat, JBoss, WebLogic
    app_server_cpu = Column(String(50), nullable=True)  # e.g., "16 vCPU"
    app_server_memory = Column(String(50), nullable=True)  # e.g., "32 GB"
    app_server_os = Column(String(100), nullable=True)  # e.g., "RHEL 8.5", "Ubuntu 22.04"

    # Database details
    db_type = Column(String(100), nullable=True)  # e.g., Oracle, PostgreSQL, MySQL
    number_of_db_instances = Column(Integer, nullable=True)
    db_server_cpu = Column(String(50), nullable=True)  # e.g., "32 vCPU"
    db_server_memory = Column(String(50), nullable=True)  # e.g., "128 GB"
    db_server_storage = Column(String(100), nullable=True)  # e.g., "2 TB SSD"
    db_server_os = Column(String(100), nullable=True)  # e.g., "Oracle Linux 8"

    # Aerospike server details
    aerospike_enabled = Column(Boolean, default=False, nullable=False)
    aerospike_version = Column(String(50), nullable=True)
    aerospike_description = Column(Text, nullable=True)
    number_of_aerospike_servers = Column(Integer, nullable=True)
    aerospike_server_cpu = Column(String(50), nullable=True)  # e.g., "16 vCPU"
    aerospike_server_memory = Column(String(50), nullable=True)  # e.g., "64 GB"
    aerospike_server_storage = Column(String(100), nullable=True)  # e.g., "1 TB NVMe"
    aerospike_server_os = Column(String(100), nullable=True)

    # Redis configuration
    redis_enabled = Column(Boolean, default=False, nullable=False)
    redis_description = Column(Text, nullable=True)
    number_of_redis_servers = Column(Integer, nullable=True)
    redis_server_memory = Column(String(50), nullable=True)  # e.g., "16 GB"
    redis_version = Column(String(50), nullable=True)

    # Recon configuration
    recon_enabled = Column(Boolean, default=False, nullable=False)
    recon_technology = Column(String(50), nullable=True)  # redis, pandas, procedure

    # Load Balancer details
    load_balancer_type = Column(String(100), nullable=True)  # e.g., F5, HAProxy, AWS ALB
    number_of_load_balancers = Column(Integer, nullable=True)

    # Monitoring & Logging
    monitoring_tool = Column(String(100), nullable=True)  # e.g., Prometheus, Datadog, New Relic
    logging_tool = Column(String(100), nullable=True)  # e.g., ELK, Splunk, Graylog

    # Network & Security
    network_zone = Column(String(100), nullable=True)  # e.g., DMZ, Internal, Secure
    ssl_certificate_expiry = Column(DateTime(timezone=True), nullable=True)
    waf_enabled = Column(Boolean, default=False, nullable=False)  # Web Application Firewall

    # Developer contacts
    implementation_developer_name = Column(String(200), nullable=True)
    implementation_developer_contact = Column(String(200), nullable=True)
    db_developer_name = Column(String(200), nullable=True)
    db_developer_contact = Column(String(200), nullable=True)  # email or phone
    ops_team_contact = Column(String(200), nullable=True)

    # Environment info
    deployment_region = Column(String(100), nullable=True)  # e.g., us-east-1, eu-west-1
    data_center = Column(String(200), nullable=True)  # e.g., Primary DC Mumbai
    dr_enabled = Column(Boolean, default=False, nullable=False)  # Disaster Recovery
    dr_location = Column(String(200), nullable=True)

    # SLA info
    uptime_sla = Column(String(50), nullable=True)  # e.g., "99.99%"
    rto = Column(String(50), nullable=True)  # Recovery Time Objective
    rpo = Column(String(50), nullable=True)  # Recovery Point Objective

    # Kubernetes Deployment Configuration
    kubernetes_enabled = Column(Boolean, default=False, nullable=False)
    # JSON array of deployment objects, each containing:
    # {
    #   "deployment_name": "imps-service",
    #   "namespace": "payment-prod",
    #   "replicas": 3,
    #   "cpu_request": "500m",
    #   "cpu_limit": "2000m",
    #   "memory_request": "1Gi",
    #   "memory_limit": "4Gi",
    #   "alb_enabled": true,
    #   "alb_name": "imps-alb",
    #   "alb_target_group": "imps-tg",
    #   "db_pool_config": {
    #     "txn": {"min": 5, "max": 20},
    #     "meta": {"min": 2, "max": 10},
    #     "recon": {"min": 2, "max": 10},
    #     "report": {"min": 2, "max": 10},
    #     "mandate": {"min": 2, "max": 10}
    #   }
    # }
    kubernetes_deployments = Column(JSON, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    bank = relationship("Bank", backref="bank_option")
    updated_by = relationship("User")

    def __repr__(self):
        return f"<BankOption for {self.bank.name if self.bank else 'Unknown'}>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "bank_id": self.bank_id,
            "bank_name": self.bank.name if self.bank else None,
            "exists": True,

            # Transaction volumes
            "transaction_volume_per_day": self.transaction_volume_per_day,
            "transaction_volume_per_month": self.transaction_volume_per_month,
            "peak_tps": self.peak_tps,

            # Architecture
            "architecture_diagram_url": self.architecture_diagram_url,

            # App server
            "number_of_app_servers": self.number_of_app_servers,
            "app_server_type": self.app_server_type,
            "app_server_cpu": self.app_server_cpu,
            "app_server_memory": self.app_server_memory,
            "app_server_os": self.app_server_os,

            # Database
            "db_type": self.db_type,
            "number_of_db_instances": self.number_of_db_instances,
            "db_server_cpu": self.db_server_cpu,
            "db_server_memory": self.db_server_memory,
            "db_server_storage": self.db_server_storage,
            "db_server_os": self.db_server_os,

            # Aerospike
            "aerospike_enabled": self.aerospike_enabled,
            "aerospike_version": self.aerospike_version,
            "aerospike_description": self.aerospike_description,
            "number_of_aerospike_servers": self.number_of_aerospike_servers,
            "aerospike_server_cpu": self.aerospike_server_cpu,
            "aerospike_server_memory": self.aerospike_server_memory,
            "aerospike_server_storage": self.aerospike_server_storage,
            "aerospike_server_os": self.aerospike_server_os,

            # Redis
            "redis_enabled": self.redis_enabled,
            "redis_description": self.redis_description,
            "number_of_redis_servers": self.number_of_redis_servers,
            "redis_server_memory": self.redis_server_memory,
            "redis_version": self.redis_version,

            # Recon
            "recon_enabled": self.recon_enabled,
            "recon_technology": self.recon_technology,

            # Load Balancer
            "load_balancer_type": self.load_balancer_type,
            "number_of_load_balancers": self.number_of_load_balancers,

            # Monitoring & Logging
            "monitoring_tool": self.monitoring_tool,
            "logging_tool": self.logging_tool,

            # Network & Security
            "network_zone": self.network_zone,
            "ssl_certificate_expiry": self.ssl_certificate_expiry.isoformat() if self.ssl_certificate_expiry else None,
            "waf_enabled": self.waf_enabled,

            # Developers
            "implementation_developer_name": self.implementation_developer_name,
            "implementation_developer_contact": self.implementation_developer_contact,
            "db_developer_name": self.db_developer_name,
            "db_developer_contact": self.db_developer_contact,
            "ops_team_contact": self.ops_team_contact,

            # Environment
            "deployment_region": self.deployment_region,
            "data_center": self.data_center,
            "dr_enabled": self.dr_enabled,
            "dr_location": self.dr_location,

            # SLA
            "uptime_sla": self.uptime_sla,
            "rto": self.rto,
            "rpo": self.rpo,

            # Kubernetes
            "kubernetes_enabled": self.kubernetes_enabled,
            "kubernetes_deployments": self.kubernetes_deployments,

            # Audit
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by.name if self.updated_by else None
        }
