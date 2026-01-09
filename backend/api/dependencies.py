"""
FastAPI dependencies for dependency injection.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from redis import Redis

from models.database import AsyncSessionLocal
from config import settings


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_redis() -> Redis:
    """
    Dependency that provides a Redis connection.

    Returns:
        Redis: Redis client instance
    """
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True
    )


async def get_current_user():
    """
    Dependency for getting the current authenticated user.

    TODO: Implement proper authentication (JWT, OAuth, etc.)

    Returns:
        dict: User information
    """
    # Placeholder for authentication
    # In production, implement proper JWT validation
    return {
        "id": "user_123",
        "email": "operator@example.com",
        "role": "ops_manager"
    }


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Required role for access

    Returns:
        Callable: Dependency function
    """
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user

    return role_checker
