"""
API routes for dispute management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from api.dependencies import get_db
from models.dispute import Dispute, Evidence, DisputeTurnaroundActivity, DisputeState
from schemas.dispute import (
    DisputeCreate,
    DisputeResponse,
    DisputeDetailResponse,
    DisputeStatusResponse,
    DisputeAnalysisRequest,
    DisputeStats,
    TurnaroundActivityResponse,
    EvidenceResponse,
)
from agents.dispute_agent.orchestrator import DisputeOrchestrator
from agents.dispute_agent.state_machine import DisputeStateMachine
from services.file_storage import file_storage

logger = structlog.get_logger()
router = APIRouter()


@router.post("", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    dispute_data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new dispute manually.
    """
    logger.info("create_dispute_manual", flight_number=dispute_data.flight_number)

    orchestrator = DisputeOrchestrator(db)

    dispute = await orchestrator.create_dispute_manual(
        flight_number=dispute_data.flight_number,
        flight_date=dispute_data.flight_date,
        airline_code=dispute_data.airline_code,
        claimed_delay_minutes=dispute_data.claimed_delay_minutes,
        penalty_amount=dispute_data.penalty_amount,
        penalty_currency=dispute_data.penalty_currency,
        airline_claimed_reason=dispute_data.airline_claimed_reason,
        scheduled_arrival=dispute_data.scheduled_arrival,
        actual_arrival=dispute_data.actual_arrival,
        scheduled_departure=dispute_data.scheduled_departure,
        actual_departure=dispute_data.actual_departure,
    )

    return dispute


@router.post("/upload", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def upload_penalty_notice(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload penalty notice and extract details automatically.
    """
    logger.info("upload_penalty_notice", filename=file.filename, content_type=file.content_type)

    # Read file
    file_content = await file.read()

    # Save file
    file_id = file_storage.save_file(file_content, file.filename, category="penalty_notices")

    orchestrator = DisputeOrchestrator(db)

    # For PDF/images, we'd use OCR/vision API
    # For MVP, assume it's text or use Claude vision
    if file.content_type.startswith("image/"):
        # TODO: Implement image extraction
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Image upload not yet implemented. Please use manual entry or text upload.",
        )
    else:
        # Assume text content
        document_text = file_content.decode("utf-8", errors="ignore")
        dispute = await orchestrator.create_dispute_from_text(document_text)

    dispute.penalty_notice_file_id = file_id
    await db.commit()

    return dispute


@router.get("", response_model=List[DisputeResponse])
async def list_disputes(
    skip: int = 0,
    limit: int = 100,
    state: Optional[DisputeState] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all disputes.
    """
    query = select(Dispute)

    if state:
        query = query.where(Dispute.state == state)

    query = query.order_by(desc(Dispute.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    disputes = result.scalars().all()

    return disputes


@router.get("/stats", response_model=DisputeStats)
async def get_dispute_stats(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """
    Get dispute statistics.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Total disputes
    total_result = await db.execute(
        select(func.count(Dispute.id))
    )
    total_disputes = total_result.scalar() or 0

    # This month
    month_result = await db.execute(
        select(func.count(Dispute.id)).where(Dispute.created_at >= since)
    )
    disputes_this_month = month_result.scalar() or 0

    # Total penalties claimed
    penalties_result = await db.execute(
        select(func.sum(Dispute.penalty_amount)).where(Dispute.created_at >= since)
    )
    total_penalties_claimed = penalties_result.scalar() or 0.0

    # Total savings
    savings_result = await db.execute(
        select(func.sum(Dispute.savings_amount)).where(
            Dispute.created_at >= since,
            Dispute.savings_amount.isnot(None),
        )
    )
    total_savings = savings_result.scalar() or 0.0

    # Win rate (disputes with outcome "accepted_full" or "accepted_partial")
    won_result = await db.execute(
        select(func.count(Dispute.id)).where(
            Dispute.created_at >= since,
            Dispute.outcome.in_(["accepted_full", "accepted_partial"]),
        )
    )
    won_disputes = won_result.scalar() or 0

    resolved_result = await db.execute(
        select(func.count(Dispute.id)).where(
            Dispute.created_at >= since,
            Dispute.outcome.isnot(None),
        )
    )
    resolved_disputes = resolved_result.scalar() or 1  # Avoid division by zero

    win_rate_percentage = (won_disputes / resolved_disputes * 100) if resolved_disputes > 0 else 0

    # Avg time to resolve (in minutes)
    # TODO: Calculate based on created_at vs resolved_at
    avg_time_to_resolve_minutes = 4.5  # Default for MVP

    # By state
    disputes_by_state = {}
    for state in DisputeState:
        count_result = await db.execute(
            select(func.count(Dispute.id)).where(
                Dispute.created_at >= since,
                Dispute.state == state,
            )
        )
        disputes_by_state[state] = count_result.scalar() or 0

    # By recommendation
    from models.dispute import DisputeRecommendation

    disputes_by_recommendation = {}
    for rec in DisputeRecommendation:
        count_result = await db.execute(
            select(func.count(Dispute.id)).where(
                Dispute.created_at >= since,
                Dispute.recommendation == rec,
            )
        )
        disputes_by_recommendation[rec] = count_result.scalar() or 0

    return DisputeStats(
        total_disputes=total_disputes,
        disputes_this_month=disputes_this_month,
        total_penalties_claimed=total_penalties_claimed,
        total_savings=total_savings,
        win_rate_percentage=win_rate_percentage,
        avg_time_to_resolve_minutes=avg_time_to_resolve_minutes,
        disputes_by_state={state.value: count for state, count in disputes_by_state.items()},
        disputes_by_recommendation={rec.value: count for rec, count in disputes_by_recommendation.items()},
    )


@router.get("/{dispute_id}", response_model=DisputeDetailResponse)
async def get_dispute(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get dispute details with evidence and activities.
    """
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    # Get activities
    activities_result = await db.execute(
        select(DisputeTurnaroundActivity).where(DisputeTurnaroundActivity.dispute_id == dispute_id)
    )
    activities = activities_result.scalars().all()

    # Get evidence
    evidence_result = await db.execute(
        select(Evidence).where(Evidence.dispute_id == dispute_id)
    )
    evidence_items = evidence_result.scalars().all()

    return DisputeDetailResponse(
        **dispute.__dict__,
        activities=[TurnaroundActivityResponse.model_validate(a) for a in activities],
        evidence=[EvidenceResponse.model_validate(e) for e in evidence_items],
    )


@router.get("/{dispute_id}/status", response_model=DisputeStatusResponse)
async def get_dispute_status(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get dispute processing status.
    """
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    state_machine = DisputeStateMachine(dispute)

    return DisputeStatusResponse(
        id=dispute.id,
        state=dispute.state,
        progress_percentage=state_machine.get_progress_percentage(),
        current_step=state_machine.get_current_step_description(),
        error_message=dispute.error_message,
        estimated_completion_seconds=state_machine.get_estimated_completion_seconds(),
    )


@router.post("/{dispute_id}/analyze", response_model=DisputeResponse)
async def analyze_dispute(
    dispute_id: str,
    analysis_request: DisputeAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Add activities and trigger analysis + response generation.
    """
    logger.info("analyze_dispute", dispute_id=dispute_id, activities_count=len(analysis_request.activities))

    orchestrator = DisputeOrchestrator(db)

    # Add activities
    activities_data = [act.model_dump() for act in analysis_request.activities]
    await orchestrator.add_activities(dispute_id, activities_data)

    # Trigger analysis and generation in background
    background_tasks.add_task(
        run_analysis_and_generation,
        dispute_id=dispute_id,
    )

    # Return updated dispute
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one()

    return dispute


async def run_analysis_and_generation(dispute_id: str):
    """Background task to run analysis and generation."""
    from models.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            orchestrator = DisputeOrchestrator(db)
            await orchestrator.analyze_and_generate(dispute_id)
        except Exception as e:
            logger.error("background_analysis_failed", dispute_id=dispute_id, error=str(e))


@router.post("/{dispute_id}/regenerate", response_model=DisputeResponse)
async def regenerate_response(
    dispute_id: str,
    feedback: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate response based on user feedback.
    """
    logger.info("regenerate_response", dispute_id=dispute_id)

    orchestrator = DisputeOrchestrator(db)
    dispute = await orchestrator.regenerate_response(dispute_id, feedback)

    return dispute


@router.delete("/{dispute_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dispute(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a dispute.
    """
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    dispute = result.scalar_one_or_none()

    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")

    await db.delete(dispute)
    await db.commit()

    logger.info("dispute_deleted", dispute_id=dispute_id)

    return None
