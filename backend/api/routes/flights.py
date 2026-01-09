"""
Flight management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta

from api.dependencies import get_db
from models.flight import Flight, FlightStatus
from models.schemas import FlightResponse, FlightCreate, FlightUpdate

router = APIRouter()


@router.get("/", response_model=List[FlightResponse])
async def get_flights(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = None,
    airline: Optional[str] = None,
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of flights with optional filtering.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        status: Filter by flight status
        airline: Filter by airline code
        date: Filter by date (YYYY-MM-DD)
        db: Database session

    Returns:
        List of flights
    """
    query = select(Flight).where(Flight.is_active == True)

    # Apply filters
    if status:
        query = query.where(Flight.status == status)

    if airline:
        query = query.where(Flight.airline_code == airline)

    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d")
            next_day = filter_date + timedelta(days=1)
            query = query.where(
                and_(
                    Flight.scheduled_time >= filter_date,
                    Flight.scheduled_time < next_day
                )
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    query = query.offset(skip).limit(limit).order_by(Flight.scheduled_time.desc())

    result = await db.execute(query)
    flights = result.scalars().all()

    return flights


@router.get("/{flight_id}", response_model=FlightResponse)
async def get_flight(
    flight_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific flight by ID.

    Args:
        flight_id: Flight ID
        db: Database session

    Returns:
        Flight details
    """
    result = await db.execute(
        select(Flight).where(Flight.id == flight_id)
    )
    flight = result.scalar_one_or_none()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    return flight


@router.get("/number/{flight_number}", response_model=List[FlightResponse])
async def get_flight_by_number(
    flight_number: str,
    date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get flights by flight number.

    Args:
        flight_number: Flight number (e.g., TK123)
        date: Optional date filter (YYYY-MM-DD)
        db: Database session

    Returns:
        List of flights matching the flight number
    """
    query = select(Flight).where(
        and_(
            Flight.flight_number == flight_number,
            Flight.is_active == True
        )
    )

    if date:
        try:
            filter_date = datetime.strptime(date, "%Y-%m-%d")
            next_day = filter_date + timedelta(days=1)
            query = query.where(
                and_(
                    Flight.scheduled_time >= filter_date,
                    Flight.scheduled_time < next_day
                )
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    query = query.order_by(Flight.scheduled_time.desc())

    result = await db.execute(query)
    flights = result.scalars().all()

    return flights


@router.post("/", response_model=FlightResponse, status_code=201)
async def create_flight(
    flight: FlightCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new flight.

    Args:
        flight: Flight data
        db: Database session

    Returns:
        Created flight
    """
    db_flight = Flight(**flight.model_dump())
    db.add(db_flight)
    await db.commit()
    await db.refresh(db_flight)

    return db_flight


@router.patch("/{flight_id}", response_model=FlightResponse)
async def update_flight(
    flight_id: int,
    flight_update: FlightUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a flight.

    Args:
        flight_id: Flight ID
        flight_update: Flight update data
        db: Database session

    Returns:
        Updated flight
    """
    result = await db.execute(
        select(Flight).where(Flight.id == flight_id)
    )
    flight = result.scalar_one_or_none()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    # Update fields
    update_data = flight_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(flight, field, value)

    flight.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(flight)

    return flight


@router.get("/delayed/list", response_model=List[FlightResponse])
async def get_delayed_flights(
    threshold_minutes: int = Query(15, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all currently delayed flights.

    Args:
        threshold_minutes: Minimum delay in minutes to be considered delayed
        db: Database session

    Returns:
        List of delayed flights
    """
    query = select(Flight).where(
        and_(
            Flight.is_active == True,
            Flight.status == FlightStatus.DELAYED
        )
    ).order_by(Flight.departure_delay.desc())

    result = await db.execute(query)
    flights = result.scalars().all()

    return flights
