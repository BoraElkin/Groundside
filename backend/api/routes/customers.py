"""
API routes for customer and API key management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timedelta
import secrets
import structlog

from api.dependencies import get_db
from api.auth import get_current_customer, get_api_key, generate_api_key
from models.customer import Customer, APIKey, APIUsage
from schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    APIKeyCreate,
    APIKeyCreated,
    APIKeyResponse,
    UsageSummary,
    APIUsageResponse,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/customers", tags=["customers"])


# Customer Management (Admin only - no auth for now, add later)
@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new customer/organization.

    This endpoint should be admin-only in production.
    """
    # Generate customer ID
    customer_id = f"cust_{secrets.token_urlsafe(16)}"

    # Create customer
    customer = Customer(
        id=customer_id,
        name=customer_data.name,
        legal_name=customer_data.legal_name,
        organization_type=customer_data.organization_type,
        email=customer_data.email,
        phone=customer_data.phone,
        address_line1=customer_data.address_line1,
        address_line2=customer_data.address_line2,
        city=customer_data.city,
        state=customer_data.state,
        country=customer_data.country,
        postal_code=customer_data.postal_code,
        subscription_tier=customer_data.subscription_tier,
        monthly_fee=customer_data.monthly_fee,
        monthly_api_call_limit=customer_data.monthly_api_call_limit,
        predict_api_rate=customer_data.predict_api_rate,
        parse_api_rate=customer_data.parse_api_rate,
        benchmark_api_rate=customer_data.benchmark_api_rate,
        enabled_connectors=[],
        connector_annual_fees={},
    )

    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    logger.info("customer_created", customer_id=customer.id, name=customer.name)

    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get customer details by ID."""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    updates: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update customer details."""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    # Update fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    customer.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(customer)

    logger.info("customer_updated", customer_id=customer.id)

    return customer


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    organization_type: str = None,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db)
):
    """List all customers with optional filtering."""
    query = select(Customer)

    if organization_type:
        query = query.where(Customer.organization_type == organization_type)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    customers = result.scalars().all()

    return customers


# API Key Management
@router.post("/me/api-keys", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key for the current customer.
    """
    # Determine prefix based on environment
    prefix_map = {
        "production": "gs_live",
        "sandbox": "gs_test",
        "development": "gs_dev",
    }
    prefix = prefix_map.get(key_data.environment, "gs_live")

    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key(prefix)

    # Generate key ID
    key_id = f"key_{secrets.token_urlsafe(16)}"

    # Create API key record
    api_key = APIKey(
        id=key_id,
        customer_id=customer.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
        environment=key_data.environment,
        scopes=key_data.scopes,
        rate_limit_per_minute=key_data.rate_limit_per_minute,
        expires_at=key_data.expires_at,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info("api_key_created", key_id=api_key.id, customer_id=customer.id, name=key_data.name)

    # Return response with full key (only time it's shown)
    response = APIKeyCreated(
        id=api_key.id,
        customer_id=api_key.customer_id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        environment=api_key.environment,
        scopes=api_key.scopes,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        api_key=full_key,
    )

    return response


@router.get("/me/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """List all API keys for the current customer."""
    result = await db.execute(
        select(APIKey).where(APIKey.customer_id == customer.id)
    )
    api_keys = result.scalars().all()

    return api_keys


@router.delete("/me/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    reason: str = "Revoked by user",
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.customer_id == customer.id
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Revoke the key
    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()
    api_key.revoked_reason = reason

    await db.commit()

    logger.info("api_key_revoked", key_id=key_id, customer_id=customer.id, reason=reason)

    return None


# Usage and Billing
@router.get("/me/usage", response_model=UsageSummary)
async def get_usage_summary(
    days: int = 30,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage summary for the current customer.
    """
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    # Query usage
    result = await db.execute(
        select(
            func.count(APIUsage.id).label("total_calls"),
            func.count(APIUsage.id).filter(APIUsage.api_type == "predict").label("predict_calls"),
            func.count(APIUsage.id).filter(APIUsage.api_type == "parse").label("parse_calls"),
            func.count(APIUsage.id).filter(APIUsage.api_type == "benchmark").label("benchmark_calls"),
            func.sum(APIUsage.cost).label("total_cost"),
            func.count(APIUsage.id).filter(APIUsage.success == True).label("successful_calls"),
            func.count(APIUsage.id).filter(APIUsage.success == False).label("failed_calls"),
        ).where(
            APIUsage.customer_id == customer.id,
            APIUsage.timestamp >= period_start,
            APIUsage.timestamp <= period_end,
        )
    )

    row = result.one()

    summary = UsageSummary(
        period_start=period_start,
        period_end=period_end,
        total_calls=row.total_calls or 0,
        predict_calls=row.predict_calls or 0,
        parse_calls=row.parse_calls or 0,
        benchmark_calls=row.benchmark_calls or 0,
        total_cost=row.total_cost or 0,
        successful_calls=row.successful_calls or 0,
        failed_calls=row.failed_calls or 0,
    )

    return summary


@router.get("/me/usage/history", response_model=List[APIUsageResponse])
async def get_usage_history(
    skip: int = 0,
    limit: int = 100,
    api_type: str = None,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed usage history."""
    query = select(APIUsage).where(APIUsage.customer_id == customer.id)

    if api_type:
        query = query.where(APIUsage.api_type == api_type)

    query = query.order_by(APIUsage.timestamp.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    usage_records = result.scalars().all()

    return usage_records
