"""
Authentication and authorization for TurnaroundIQ APIs.
"""
import hashlib
import secrets
from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from models.customer import Customer, APIKey
from api.dependencies import get_db

logger = structlog.get_logger()

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.

    Args:
        api_key: Raw API key

    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key(prefix: str = "gs_live") -> tuple[str, str, str]:
    """
    Generate a new API key.

    Args:
        prefix: Key prefix (gs_live for production, gs_test for sandbox)

    Returns:
        Tuple of (full_key, key_hash, key_prefix)
    """
    # Generate random key
    random_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}_{random_part}"

    # Hash for storage
    key_hash = hash_api_key(full_key)

    # Store prefix for identification
    key_prefix = full_key[:16]

    return full_key, key_hash, key_prefix


async def get_api_key(
    api_key: Optional[str] = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    """
    Validate API key and return APIKey object.

    Args:
        api_key: API key from header
        db: Database session

    Returns:
        APIKey object

    Raises:
        HTTPException: If API key is invalid or inactive
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'X-API-Key' header.",
            headers={"WWW-Authenticate": "APIKey"},
        )

    # Hash the provided key
    key_hash = hash_api_key(api_key)

    # Query database
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        logger.warning("invalid_api_key_attempt", key_prefix=api_key[:16] if len(api_key) >= 16 else "short_key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "APIKey"},
        )

    # Check expiration
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        logger.warning("expired_api_key_attempt", key_id=api_key_obj.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last used timestamp
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()

    logger.info("api_key_authenticated", key_id=api_key_obj.id, customer_id=api_key_obj.customer_id)

    return api_key_obj


async def get_current_customer(
    api_key: APIKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
) -> Customer:
    """
    Get current customer from API key.

    Args:
        api_key: Validated API key
        db: Database session

    Returns:
        Customer object

    Raises:
        HTTPException: If customer is not found or inactive
    """
    result = await db.execute(
        select(Customer).where(
            Customer.id == api_key.customer_id,
            Customer.is_active == True
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        logger.error("customer_not_found", customer_id=api_key.customer_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account not found or inactive",
        )

    return customer


def require_scope(required_scope: str):
    """
    Dependency factory to require specific API scope.

    Args:
        required_scope: Required scope (e.g., "predict:read", "parse:write")

    Returns:
        Dependency function
    """
    async def scope_checker(api_key: APIKey = Depends(get_api_key)):
        if required_scope not in api_key.scopes and "admin:all" not in api_key.scopes:
            logger.warning(
                "insufficient_scope",
                key_id=api_key.id,
                required=required_scope,
                available=api_key.scopes
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}",
            )
        return api_key

    return scope_checker


def require_organization_type(*allowed_types: str):
    """
    Dependency factory to require specific organization type.

    Args:
        allowed_types: Allowed organization types (e.g., "airline", "ground_handler")

    Returns:
        Dependency function
    """
    async def org_type_checker(customer: Customer = Depends(get_current_customer)):
        if customer.organization_type not in allowed_types:
            logger.warning(
                "invalid_organization_type",
                customer_id=customer.id,
                org_type=customer.organization_type,
                allowed=allowed_types
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This endpoint is only available for: {', '.join(allowed_types)}",
            )
        return customer

    return org_type_checker
