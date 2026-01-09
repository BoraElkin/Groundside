"""
Turnaround monitoring API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime

from api.dependencies import get_db
from models.turnaround import Turnaround, TurnaroundStatus
from models.schemas import TurnaroundResponse, TurnaroundCreate, TurnaroundUpdate

router = APIRouter()


@router.get("/", response_model=List[TurnaroundResponse])
async def get_turnarounds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = None,
    gate: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of turnarounds with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by turnaround status
        gate: Filter by gate
        db: Database session

    Returns:
        List of turnarounds with activities
    """
    query = select(Turnaround).options(
        selectinload(Turnaround.activities)
    )

    # Apply filters
    if status:
        query = query.where(Turnaround.status == status)

    if gate:
        query = query.where(Turnaround.gate == gate)

    query = query.offset(skip).limit(limit).order_by(Turnaround.scheduled_start.desc())

    result = await db.execute(query)
    turnarounds = result.scalars().all()

    return turnarounds


@router.get("/{turnaround_id}", response_model=TurnaroundResponse)
async def get_turnaround(
    turnaround_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific turnaround by ID.

    Args:
        turnaround_id: Turnaround ID
        db: Database session

    Returns:
        Turnaround details with activities
    """
    result = await db.execute(
        select(Turnaround)
        .options(selectinload(Turnaround.activities))
        .where(Turnaround.id == turnaround_id)
    )
    turnaround = result.scalar_one_or_none()

    if not turnaround:
        raise HTTPException(status_code=404, detail="Turnaround not found")

    return turnaround


@router.get("/flight/{flight_id}", response_model=List[TurnaroundResponse])
async def get_turnarounds_by_flight(
    flight_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all turnarounds for a specific flight.

    Args:
        flight_id: Flight ID
        db: Database session

    Returns:
        List of turnarounds for the flight
    """
    result = await db.execute(
        select(Turnaround)
        .options(selectinload(Turnaround.activities))
        .where(Turnaround.flight_id == flight_id)
        .order_by(Turnaround.scheduled_start.desc())
    )
    turnarounds = result.scalars().all()

    return turnarounds


@router.post("/", response_model=TurnaroundResponse, status_code=201)
async def create_turnaround(
    turnaround: TurnaroundCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new turnaround.

    Args:
        turnaround: Turnaround data
        db: Database session

    Returns:
        Created turnaround
    """
    db_turnaround = Turnaround(**turnaround.model_dump())
    db.add(db_turnaround)
    await db.commit()
    await db.refresh(db_turnaround)

    return db_turnaround


@router.patch("/{turnaround_id}", response_model=TurnaroundResponse)
async def update_turnaround(
    turnaround_id: int,
    turnaround_update: TurnaroundUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a turnaround.

    Args:
        turnaround_id: Turnaround ID
        turnaround_update: Turnaround update data
        db: Database session

    Returns:
        Updated turnaround
    """
    result = await db.execute(
        select(Turnaround).where(Turnaround.id == turnaround_id)
    )
    turnaround = result.scalar_one_or_none()

    if not turnaround:
        raise HTTPException(status_code=404, detail="Turnaround not found")

    # Update fields
    update_data = turnaround_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(turnaround, field, value)

    turnaround.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(turnaround)

    return turnaround


@router.get("/at-risk/list", response_model=List[TurnaroundResponse])
async def get_at_risk_turnarounds(
    risk_threshold: float = Query(0.5, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all turnarounds currently at risk of delay.

    Args:
        risk_threshold: Minimum risk score (0-1) to be considered at-risk
        db: Database session

    Returns:
        List of at-risk turnarounds
    """
    result = await db.execute(
        select(Turnaround)
        .options(selectinload(Turnaround.activities))
        .where(
            and_(
                Turnaround.risk_score >= risk_threshold,
                Turnaround.status.in_([
                    TurnaroundStatus.IN_PROGRESS,
                    TurnaroundStatus.AT_RISK
                ])
            )
        )
        .order_by(Turnaround.risk_score.desc())
    )
    turnarounds = result.scalars().all()

    return turnarounds


@router.get("/active/dashboard", response_model=List[TurnaroundResponse])
async def get_active_turnarounds_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active turnarounds for dashboard display.

    Returns turnarounds that are scheduled, in progress, or at risk.

    Args:
        db: Database session

    Returns:
        List of active turnarounds
    """
    result = await db.execute(
        select(Turnaround)
        .options(selectinload(Turnaround.activities))
        .where(
            Turnaround.status.in_([
                TurnaroundStatus.SCHEDULED,
                TurnaroundStatus.IN_PROGRESS,
                TurnaroundStatus.ON_TIME,
                TurnaroundStatus.AT_RISK,
                TurnaroundStatus.DELAYED
            ])
        )
        .order_by(Turnaround.scheduled_start.asc())
        .limit(50)
    )
    turnarounds = result.scalars().all()

    return turnarounds
