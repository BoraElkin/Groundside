"""
Customer/Organization models for multi-tenancy.
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from models.database import Base


class OrganizationType(str, enum.Enum):
    """Type of organization."""
    AIRLINE = "airline"
    GROUND_HANDLER = "ground_handler"
    AIRPORT = "airport"
    INTEGRATOR = "integrator"


class SubscriptionTier(str, enum.Enum):
    """Subscription tier for pricing."""
    FREE = "free"
    STARTER = "starter"  # $5K/month
    PROFESSIONAL = "professional"  # $20K/month
    ENTERPRISE = "enterprise"  # $50K+/month
    CUSTOM = "custom"  # Custom negotiated pricing


class Customer(Base):
    """
    Customer/Organization model for multi-tenancy.

    Represents airlines, ground handlers, airports, or integration partners
    that use the TurnaroundIQ platform.
    """
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    legal_name = Column(String)
    organization_type = Column(SQLEnum(OrganizationType), nullable=False, index=True)

    # Contact information
    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String)

    # Address
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String, index=True)
    postal_code = Column(String)

    # Subscription details
    subscription_tier = Column(SQLEnum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    monthly_fee = Column(Numeric(10, 2))  # Base monthly fee
    contract_start_date = Column(DateTime(timezone=True))
    contract_end_date = Column(DateTime(timezone=True))

    # API Usage limits
    monthly_api_call_limit = Column(Integer)  # null = unlimited
    predict_api_rate = Column(Numeric(6, 4))  # $ per prediction call
    parse_api_rate = Column(Numeric(6, 4))  # $ per parse call
    benchmark_api_rate = Column(Numeric(6, 4))  # $ per benchmark query

    # Integration connectors (charged separately)
    enabled_connectors = Column(JSON, default=list)  # ["SITA", "Amadeus", "Swissport"]
    connector_annual_fees = Column(JSON, default=dict)  # {"SITA": 15000, "Amadeus": 20000}

    # Data contribution (for benchmark API)
    contributes_data = Column(Boolean, default=False)
    data_anonymization_level = Column(String, default="standard")  # standard, strict, custom

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_design_partner = Column(Boolean, default=False)  # Early adopters get special treatment

    # Metadata
    settings = Column(JSON, default=dict)  # Custom settings per customer
    notes = Column(String)  # Internal notes about the customer

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    api_keys = relationship("APIKey", back_populates="customer", cascade="all, delete-orphan")
    usage_records = relationship("APIUsage", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.id}: {self.name} ({self.organization_type})>"


class APIKey(Base):
    """
    API Key for authenticating customer requests.
    """
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, nullable=False, index=True)

    # Key details
    key_hash = Column(String, nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = Column(String, nullable=False)  # First 8 chars for identification (e.g., "gs_live_12345678")
    name = Column(String, nullable=False)  # User-friendly name (e.g., "Production API Key")

    # Environment
    environment = Column(String, default="production", index=True)  # production, sandbox, development

    # Permissions
    scopes = Column(JSON, default=list)  # ["predict:read", "parse:read", "benchmark:read"]
    rate_limit_per_minute = Column(Integer, default=100)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))

    # Metadata
    created_by = Column(String)  # User ID who created the key
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(String)
    revoked_reason = Column(String)

    # Relationships
    customer = relationship("Customer", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.key_prefix}... for {self.customer_id}>"


class APIUsage(Base):
    """
    API usage tracking for metering and billing.
    """
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, nullable=False, index=True)
    api_key_id = Column(String, index=True)

    # Request details
    endpoint = Column(String, nullable=False, index=True)  # /api/v1/predict, /api/v1/parse, etc.
    method = Column(String, nullable=False)  # GET, POST, etc.
    api_type = Column(String, index=True)  # predict, parse, benchmark

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    response_time_ms = Column(Integer)

    # Status
    status_code = Column(Integer, index=True)
    success = Column(Boolean, index=True)

    # Billing
    billable = Column(Boolean, default=True, index=True)
    cost = Column(Numeric(10, 6))  # Cost in dollars for this call

    # Request metadata
    request_id = Column(String, index=True)
    user_agent = Column(String)
    ip_address = Column(String)

    # Relationships
    customer = relationship("Customer", back_populates="usage_records")

    def __repr__(self):
        return f"<APIUsage {self.customer_id}: {self.endpoint} at {self.timestamp}>"


class BillingPeriod(Base):
    """
    Monthly billing period and invoice generation.
    """
    __tablename__ = "billing_periods"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, nullable=False, index=True)

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Usage summary
    total_api_calls = Column(Integer, default=0)
    predict_calls = Column(Integer, default=0)
    parse_calls = Column(Integer, default=0)
    benchmark_calls = Column(Integer, default=0)

    # Costs
    base_subscription_fee = Column(Numeric(10, 2))
    usage_charges = Column(Numeric(10, 2))
    connector_fees = Column(Numeric(10, 2))
    total_amount = Column(Numeric(10, 2))

    # Invoice
    invoice_id = Column(String, unique=True, index=True)
    invoice_url = Column(String)
    invoice_status = Column(String, default="pending", index=True)  # pending, paid, overdue, cancelled
    paid_at = Column(DateTime(timezone=True))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(String)

    def __repr__(self):
        return f"<BillingPeriod {self.customer_id}: {self.period_start.strftime('%Y-%m')} - ${self.total_amount}>"
