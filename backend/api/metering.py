"""
API metering middleware and utilities for tracking usage and billing.
"""
import time
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
import structlog
import uuid

from models.database import AsyncSessionLocal
from models.customer import APIUsage, Customer, APIKey
from api.auth import hash_api_key

logger = structlog.get_logger()


class MeteringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API usage for billing purposes.

    Captures every API call and stores:
    - Endpoint accessed
    - Response time
    - Success/failure
    - Cost calculation
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track usage."""
        # Skip metering for health checks and non-API endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Skip metering for customer management endpoints (internal)
        if request.url.path.startswith("/api/v1/customers") and not request.url.path.startswith("/api/v1/customers/me"):
            return await call_next(request)

        # Start timing
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Extract customer info from API key
        customer_id = None
        api_key_id = None
        api_key_header = request.headers.get("X-API-Key")

        if api_key_header:
            # We need to look up the customer from the API key
            # This is done again in the auth dependency, but we need it here for metering
            async with AsyncSessionLocal() as db:
                try:
                    from sqlalchemy import select
                    key_hash = hash_api_key(api_key_header)
                    result = await db.execute(
                        select(APIKey).where(APIKey.key_hash == key_hash)
                    )
                    api_key_obj = result.scalar_one_or_none()
                    if api_key_obj:
                        customer_id = api_key_obj.customer_id
                        api_key_id = api_key_obj.id
                except Exception as e:
                    logger.warning("metering_key_lookup_failed", error=str(e))

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Determine API type and calculate cost
        api_type = None
        cost = Decimal("0.0")

        if "/predict" in request.url.path:
            api_type = "predict"
        elif "/parse" in request.url.path:
            api_type = "parse"
        elif "/benchmark" in request.url.path:
            api_type = "benchmark"

        # Only track billable endpoints
        billable = api_type is not None and customer_id is not None

        # Record usage asynchronously
        if billable:
            try:
                async with AsyncSessionLocal() as db:
                    # Get customer to determine rates
                    result = await db.execute(
                        select(Customer).where(Customer.id == customer_id)
                    )
                    customer = result.scalar_one_or_none()

                    if customer:
                        # Calculate cost based on API type
                        if api_type == "predict":
                            cost = customer.predict_api_rate
                        elif api_type == "parse":
                            cost = customer.parse_api_rate
                        elif api_type == "benchmark":
                            cost = customer.benchmark_api_rate

                        # Create usage record
                        usage = APIUsage(
                            customer_id=customer_id,
                            api_key_id=api_key_id,
                            endpoint=request.url.path,
                            method=request.method,
                            api_type=api_type,
                            timestamp=datetime.utcnow(),
                            response_time_ms=response_time_ms,
                            status_code=response.status_code,
                            success=200 <= response.status_code < 300,
                            billable=billable,
                            cost=cost,
                            request_id=request_id,
                            user_agent=request.headers.get("User-Agent"),
                            ip_address=request.client.host if request.client else None,
                        )

                        db.add(usage)
                        await db.commit()

                        logger.info(
                            "api_call_metered",
                            customer_id=customer_id,
                            api_type=api_type,
                            endpoint=request.url.path,
                            response_time_ms=response_time_ms,
                            status_code=response.status_code,
                            cost=float(cost),
                            request_id=request_id,
                        )
            except Exception as e:
                # Don't fail the request if metering fails
                logger.error(
                    "metering_failed",
                    error=str(e),
                    request_id=request_id,
                    customer_id=customer_id,
                )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(response_time_ms)

        return response


async def check_rate_limit(api_key: APIKey, db: AsyncSession) -> bool:
    """
    Check if API key has exceeded rate limit.

    Args:
        api_key: API key object
        db: Database session

    Returns:
        True if within rate limit, False if exceeded
    """
    from sqlalchemy import select, func
    from datetime import timedelta

    # Count calls in the last minute
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)

    result = await db.execute(
        select(func.count(APIUsage.id)).where(
            APIUsage.api_key_id == api_key.id,
            APIUsage.timestamp >= one_minute_ago,
        )
    )
    call_count = result.scalar() or 0

    return call_count < api_key.rate_limit_per_minute


async def check_monthly_quota(customer: Customer, db: AsyncSession) -> tuple[bool, int, int]:
    """
    Check if customer has exceeded monthly API call quota.

    Args:
        customer: Customer object
        db: Database session

    Returns:
        Tuple of (within_quota, current_usage, quota_limit)
    """
    from sqlalchemy import select, func
    from datetime import timedelta

    # If no limit set, always within quota
    if customer.monthly_api_call_limit is None:
        return True, 0, -1  # -1 indicates unlimited

    # Count calls this month
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.count(APIUsage.id)).where(
            APIUsage.customer_id == customer.id,
            APIUsage.timestamp >= month_start,
            APIUsage.billable == True,
        )
    )
    current_usage = result.scalar() or 0

    within_quota = current_usage < customer.monthly_api_call_limit

    return within_quota, current_usage, customer.monthly_api_call_limit


async def get_current_month_cost(customer: Customer, db: AsyncSession) -> Decimal:
    """
    Calculate total cost for current billing period.

    Args:
        customer: Customer object
        db: Database session

    Returns:
        Total cost in dollars
    """
    from sqlalchemy import select, func

    # Get month start
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.sum(APIUsage.cost)).where(
            APIUsage.customer_id == customer.id,
            APIUsage.timestamp >= month_start,
            APIUsage.billable == True,
        )
    )
    total_cost = result.scalar() or Decimal("0.0")

    return total_cost
