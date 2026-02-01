"""
Bank Option model - Stores bank technical configuration and infrastructure details
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
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

    # Architecture
    architecture_diagram_url = Column(String(500), nullable=True)

    # App server details
    number_of_app_servers = Column(Integer, nullable=True)
    app_server_type = Column(String(100), nullable=True)  # e.g., Tomcat, JBoss, WebLogic

    # Database details
    db_type = Column(String(100), nullable=True)  # e.g., Oracle, PostgreSQL, MySQL
    number_of_db_instances = Column(Integer, nullable=True)

    # Developer contacts
    implementation_developer_name = Column(String(200), nullable=True)
    db_developer_name = Column(String(200), nullable=True)
    db_developer_contact = Column(String(200), nullable=True)  # email or phone

    # Aerospike configuration
    aerospike_enabled = Column(Boolean, default=False, nullable=False)
    aerospike_version = Column(String(50), nullable=True)
    aerospike_description = Column(Text, nullable=True)

    # Redis configuration
    redis_enabled = Column(Boolean, default=False, nullable=False)
    redis_description = Column(Text, nullable=True)

    # Recon configuration
    recon_enabled = Column(Boolean, default=False, nullable=False)
    recon_technology = Column(String(50), nullable=True)  # redis, pandas, procedure

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

            # Transaction volumes
            "transaction_volume_per_day": self.transaction_volume_per_day,
            "transaction_volume_per_month": self.transaction_volume_per_month,

            # Architecture
            "architecture_diagram_url": self.architecture_diagram_url,

            # App server
            "number_of_app_servers": self.number_of_app_servers,
            "app_server_type": self.app_server_type,

            # Database
            "db_type": self.db_type,
            "number_of_db_instances": self.number_of_db_instances,

            # Developers
            "implementation_developer_name": self.implementation_developer_name,
            "db_developer_name": self.db_developer_name,
            "db_developer_contact": self.db_developer_contact,

            # Aerospike
            "aerospike_enabled": self.aerospike_enabled,
            "aerospike_version": self.aerospike_version,
            "aerospike_description": self.aerospike_description,

            # Redis
            "redis_enabled": self.redis_enabled,
            "redis_description": self.redis_description,

            # Recon
            "recon_enabled": self.recon_enabled,
            "recon_technology": self.recon_technology,

            # Audit
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by_id": self.updated_by_id,
            "updated_by_name": self.updated_by.name if self.updated_by else None
        }
