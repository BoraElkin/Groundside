"""
FastAPI dependencies for dependency injection.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import AsyncSessionLocal


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
