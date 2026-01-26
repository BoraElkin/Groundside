"""
Pydantic schemas for customer/organization management.
"""
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field

from models.customer import OrganizationType, SubscriptionTier


# Customer schemas
class CustomerBase(BaseModel):
    """Base schema for customer."""
    name: str
    legal_name: Optional[str] = None
    organization_type: OrganizationType
    email: EmailStr
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    monthly_fee: Optional[Decimal] = None
    monthly_api_call_limit: Optional[int] = 10000
    predict_api_rate: Decimal = Decimal("0.03")
    parse_api_rate: Decimal = Decimal("0.05")
    benchmark_api_rate: Decimal = Decimal("0.02")


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    name: Optional[str] = None
    legal_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    subscription_tier: Optional[SubscriptionTier] = None
    monthly_fee: Optional[Decimal] = None
    monthly_api_call_limit: Optional[int] = None
    predict_api_rate: Optional[Decimal] = None
    parse_api_rate: Optional[Decimal] = None
    benchmark_api_rate: Optional[Decimal] = None
    is_active: Optional[bool] = None
    is_design_partner: Optional[bool] = None
    contributes_data: Optional[bool] = None
    settings: Optional[Dict] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response."""
    id: str
    subscription_tier: SubscriptionTier
    monthly_fee: Optional[Decimal]
    monthly_api_call_limit: Optional[int]
    predict_api_rate: Decimal
    parse_api_rate: Decimal
    benchmark_api_rate: Decimal
    enabled_connectors: List[str]
    contributes_data: bool
    is_active: bool
    is_design_partner: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# API Key schemas
class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., description="Human-readable name for the key")
    environment: str = Field(default="production", description="Environment: production, sandbox, development")
    scopes: List[str] = Field(default_factory=lambda: ["predict:read", "parse:read", "benchmark:read"])
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (null = never expires)")


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: str
    customer_id: str
    key_prefix: str
    name: str
    environment: str
    scopes: List[str]
    rate_limit_per_minute: int
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreated(APIKeyResponse):
    """Schema returned when a new API key is created (includes full key)."""
    api_key: str = Field(..., description="Full API key - save this, it won't be shown again!")


# API Usage schemas
class APIUsageResponse(BaseModel):
    """Schema for API usage record."""
    id: int
    customer_id: str
    endpoint: str
    method: str
    api_type: str
    timestamp: datetime
    response_time_ms: Optional[int]
    status_code: int
    success: bool
    billable: bool
    cost: Optional[Decimal]

    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    """Schema for usage summary."""
    period_start: datetime
    period_end: datetime
    total_calls: int
    predict_calls: int
    parse_calls: int
    benchmark_calls: int
    total_cost: Decimal
    successful_calls: int
    failed_calls: int


# Billing schemas
class BillingPeriodResponse(BaseModel):
    """Schema for billing period."""
    id: int
    customer_id: str
    period_start: datetime
    period_end: datetime
    total_api_calls: int
    predict_calls: int
    parse_calls: int
    benchmark_calls: int
    base_subscription_fee: Decimal
    usage_charges: Decimal
    connector_fees: Decimal
    total_amount: Decimal
    invoice_id: Optional[str]
    invoice_status: str
    paid_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
