"""
Alert management API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, timedelta

from api.dependencies import get_db
from models.alert import Alert, AlertStatus, AlertSeverity
from models.schemas import AlertResponse, AlertCreate, AlertUpdate, AlertStatusSchema

router = APIRouter()


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    flight_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of alerts with optional filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by alert status
        severity: Filter by severity level
        flight_id: Filter by flight ID
        db: Database session

    Returns:
        List of alerts
    """
    query = select(Alert)

    # Apply filters
    if status:
        query = query.where(Alert.status == status)

    if severity:
        query = query.where(Alert.severity == severity)

    if flight_id:
        query = query.where(Alert.flight_id == flight_id)

    query = query.offset(skip).limit(limit).order_by(Alert.triggered_at.desc())

    result = await db.execute(query)
    alerts = result.scalars().all()

    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific alert by ID.

    Args:
        alert_id: Alert ID
        db: Database session

    Returns:
        Alert details
    """
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert: AlertCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new alert.

    Args:
        alert: Alert data
        db: Database session

    Returns:
        Created alert
    """
    db_alert = Alert(**alert.model_dump())
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)

    # TODO: Trigger notification via Celery task
    # send_alert_notification.delay(db_alert.id)

    return db_alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an alert.

    Args:
        alert_id: Alert ID
        alert_update: Alert update data
        db: Database session

    Returns:
        Updated alert
    """
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Update fields
    update_data = alert_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)

    # Set timestamps
    if alert_update.status == AlertStatusSchema.ACKNOWLEDGED and not alert.acknowledged_at:
        alert.acknowledged_at = datetime.utcnow()

    if alert_update.status == AlertStatusSchema.RESOLVED and not alert.resolved_at:
        alert.resolved_at = datetime.utcnow()

    alert.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    acknowledged_by: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert ID
        acknowledged_by: User who acknowledged the alert
        db: Database session

    Returns:
        Updated alert
    """
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    resolved_by: str,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Resolve an alert.

    Args:
        alert_id: Alert ID
        resolved_by: User who resolved the alert
        resolution_notes: Optional resolution notes
        db: Database session

    Returns:
        Updated alert
    """
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = AlertStatus.RESOLVED
    alert.resolved_by = resolved_by
    alert.resolved_at = datetime.utcnow()
    if resolution_notes:
        alert.resolution_notes = resolution_notes
    alert.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alert)

    return alert


@router.get("/active/list", response_model=List[AlertResponse])
async def get_active_alerts(
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all currently active alerts.

    Args:
        severity: Optional severity filter
        db: Database session

    Returns:
        List of active alerts
    """
    query = select(Alert).where(Alert.status == AlertStatus.ACTIVE)

    if severity:
        query = query.where(Alert.severity == severity)

    query = query.order_by(
        Alert.severity.desc(),
        Alert.triggered_at.desc()
    )

    result = await db.execute(query)
    alerts = result.scalars().all()

    return alerts


@router.get("/critical/recent", response_model=List[AlertResponse])
async def get_recent_critical_alerts(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent critical alerts.

    Args:
        hours: Number of hours to look back (default: 24)
        db: Database session

    Returns:
        List of recent critical alerts
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(Alert).where(
            and_(
                Alert.severity == AlertSeverity.CRITICAL,
                Alert.triggered_at >= cutoff_time
            )
        ).order_by(Alert.triggered_at.desc())
    )
    alerts = result.scalars().all()

    return alerts
