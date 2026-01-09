"""
Analytics and reporting API routes.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime, timedelta

from api.dependencies import get_db
from models.flight import Flight, FlightStatus
from models.turnaround import Turnaround, TurnaroundStatus
from models.alert import Alert, AlertSeverity
from models.schemas import DelayStatistics, TurnaroundStatistics

router = APIRouter()


@router.get("/delays", response_model=DelayStatistics)
async def get_delay_statistics(
    hours: int = Query(24, ge=1, le=168),
    airline: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get delay statistics for a time period.

    Args:
        hours: Number of hours to analyze (default: 24)
        airline: Optional airline filter
        db: Database session

    Returns:
        Delay statistics
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    # Base query
    query = select(Flight).where(
        and_(
            Flight.scheduled_time >= cutoff_time,
            Flight.is_active == True
        )
    )

    if airline:
        query = query.where(Flight.airline_code == airline)

    result = await db.execute(query)
    flights = result.scalars().all()

    if not flights:
        return DelayStatistics(
            total_flights=0,
            delayed_flights=0,
            average_delay_minutes=0.0,
            on_time_percentage=100.0
        )

    total_flights = len(flights)
    delayed_flights = sum(1 for f in flights if f.is_delayed)
    total_delay = sum(f.delay_minutes for f in flights)
    average_delay = total_delay / total_flights if total_flights > 0 else 0.0
    on_time_percentage = ((total_flights - delayed_flights) / total_flights * 100) if total_flights > 0 else 100.0

    # Find most delayed airline
    airline_delays = {}
    for flight in flights:
        if flight.airline_code not in airline_delays:
            airline_delays[flight.airline_code] = []
        airline_delays[flight.airline_code].append(flight.delay_minutes)

    most_delayed_airline = None
    if airline_delays:
        most_delayed_airline = max(
            airline_delays.items(),
            key=lambda x: sum(x[1]) / len(x[1])
        )[0]

    return DelayStatistics(
        total_flights=total_flights,
        delayed_flights=delayed_flights,
        average_delay_minutes=round(average_delay, 2),
        on_time_percentage=round(on_time_percentage, 2),
        most_delayed_airline=most_delayed_airline
    )


@router.get("/turnarounds", response_model=TurnaroundStatistics)
async def get_turnaround_statistics(
    hours: int = Query(24, ge=1, le=168),
    gate: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get turnaround performance statistics.

    Args:
        hours: Number of hours to analyze
        gate: Optional gate filter
        db: Database session

    Returns:
        Turnaround statistics
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    query = select(Turnaround).where(
        Turnaround.scheduled_start >= cutoff_time
    )

    if gate:
        query = query.where(Turnaround.gate == gate)

    result = await db.execute(query)
    turnarounds = result.scalars().all()

    if not turnarounds:
        return TurnaroundStatistics(
            total_turnarounds=0,
            completed_on_time=0,
            at_risk=0,
            delayed=0,
            average_duration_minutes=0.0,
            average_delay_minutes=0.0
        )

    total_turnarounds = len(turnarounds)
    completed_on_time = sum(
        1 for t in turnarounds
        if t.status == TurnaroundStatus.COMPLETED and t.delay_minutes == 0
    )
    at_risk = sum(1 for t in turnarounds if t.status == TurnaroundStatus.AT_RISK)
    delayed = sum(1 for t in turnarounds if t.status == TurnaroundStatus.DELAYED)

    # Calculate averages for completed turnarounds
    completed = [t for t in turnarounds if t.actual_duration]
    avg_duration = sum(t.actual_duration for t in completed) / len(completed) if completed else 0.0
    avg_delay = sum(t.delay_minutes for t in turnarounds) / total_turnarounds if total_turnarounds > 0 else 0.0

    return TurnaroundStatistics(
        total_turnarounds=total_turnarounds,
        completed_on_time=completed_on_time,
        at_risk=at_risk,
        delayed=delayed,
        average_duration_minutes=round(avg_duration, 2),
        average_delay_minutes=round(avg_delay, 2)
    )


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics for dashboard.

    Args:
        db: Database session

    Returns:
        Dashboard summary with key metrics
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's flights
    flights_result = await db.execute(
        select(func.count(Flight.id)).where(
            and_(
                Flight.scheduled_time >= today_start,
                Flight.is_active == True
            )
        )
    )
    total_flights_today = flights_result.scalar() or 0

    # Delayed flights
    delayed_result = await db.execute(
        select(func.count(Flight.id)).where(
            and_(
                Flight.scheduled_time >= today_start,
                Flight.status == FlightStatus.DELAYED,
                Flight.is_active == True
            )
        )
    )
    delayed_flights = delayed_result.scalar() or 0

    # Active turnarounds
    active_turnarounds_result = await db.execute(
        select(func.count(Turnaround.id)).where(
            Turnaround.status.in_([
                TurnaroundStatus.IN_PROGRESS,
                TurnaroundStatus.AT_RISK
            ])
        )
    )
    active_turnarounds = active_turnarounds_result.scalar() or 0

    # Active alerts
    active_alerts_result = await db.execute(
        select(func.count(Alert.id)).where(
            Alert.status == "active"
        )
    )
    active_alerts = active_alerts_result.scalar() or 0

    # Critical alerts
    critical_alerts_result = await db.execute(
        select(func.count(Alert.id)).where(
            and_(
                Alert.status == "active",
                Alert.severity == AlertSeverity.CRITICAL
            )
        )
    )
    critical_alerts = critical_alerts_result.scalar() or 0

    return {
        "timestamp": now.isoformat(),
        "flights": {
            "total_today": total_flights_today,
            "delayed": delayed_flights,
            "on_time_percentage": round(
                ((total_flights_today - delayed_flights) / total_flights_today * 100)
                if total_flights_today > 0 else 100.0,
                2
            )
        },
        "turnarounds": {
            "active": active_turnarounds
        },
        "alerts": {
            "active": active_alerts,
            "critical": critical_alerts
        }
    }


@router.get("/performance/hourly")
async def get_hourly_performance(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Get hourly performance metrics.

    Args:
        hours: Number of hours to analyze
        db: Database session

    Returns:
        Hourly breakdown of performance metrics
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(Flight).where(
            and_(
                Flight.scheduled_time >= cutoff_time,
                Flight.is_active == True
            )
        ).order_by(Flight.scheduled_time)
    )
    flights = result.scalars().all()

    # Group by hour
    hourly_data = {}
    for flight in flights:
        hour_key = flight.scheduled_time.strftime("%Y-%m-%d %H:00")
        if hour_key not in hourly_data:
            hourly_data[hour_key] = {
                "hour": hour_key,
                "total_flights": 0,
                "delayed_flights": 0,
                "average_delay": 0.0
            }

        hourly_data[hour_key]["total_flights"] += 1
        if flight.is_delayed:
            hourly_data[hour_key]["delayed_flights"] += 1
        hourly_data[hour_key]["average_delay"] += flight.delay_minutes

    # Calculate averages
    for data in hourly_data.values():
        if data["total_flights"] > 0:
            data["average_delay"] = round(
                data["average_delay"] / data["total_flights"],
                2
            )

    return {
        "period_hours": hours,
        "data": sorted(hourly_data.values(), key=lambda x: x["hour"])
    }
