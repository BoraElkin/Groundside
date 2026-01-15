"""
Pydantic schemas for dispute management.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from models.dispute import (
    DisputeState,
    DisputeRecommendation,
    EvidenceType,
    ResponsibleParty,
)


# Turnaround Activity schemas
class TurnaroundActivityCreate(BaseModel):
    """Schema for creating turnaround activity."""
    activity_type: str = Field(..., description="Type of activity (deboarding, cleaning, catering, etc.)")
    performed_by: ResponsibleParty
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    notes: Optional[str] = None


class TurnaroundActivityResponse(BaseModel):
    """Schema for turnaround activity response."""
    id: str
    activity_type: str
    performed_by: ResponsibleParty
    scheduled_start: Optional[datetime]
    actual_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    actual_end: Optional[datetime]
    actual_duration_minutes: Optional[int]
    delay_minutes: Optional[int]
    was_within_standard: Optional[bool]
    notes: Optional[str]

    class Config:
        from_attributes = True


# Evidence schemas
class EvidenceCreate(BaseModel):
    """Schema for creating evidence."""
    evidence_type: EvidenceType
    source: Optional[str] = None
    timestamp: Optional[datetime] = None
    summary: str
    raw_data: Optional[Dict[str, Any]] = None
    supports_dispute: bool = True


class EvidenceResponse(BaseModel):
    """Schema for evidence response."""
    id: str
    dispute_id: str
    evidence_type: EvidenceType
    source: Optional[str]
    timestamp: Optional[datetime]
    summary: str
    supports_dispute: bool
    relevance_score: Optional[float]
    responsible_party: Optional[ResponsibleParty]
    delay_minutes_attributed: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# Dispute schemas
class DisputeCreate(BaseModel):
    """Schema for creating a dispute manually."""
    flight_number: str
    flight_date: datetime
    airline_code: Optional[str] = None
    claimed_delay_minutes: int
    penalty_amount: float
    penalty_currency: str = "USD"
    airline_claimed_reason: Optional[str] = None

    # Optional timing details
    scheduled_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    scheduled_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None


class DisputeUpdate(BaseModel):
    """Schema for updating a dispute."""
    user_edited_response: Optional[str] = None
    user_notes: Optional[str] = None
    state: Optional[DisputeState] = None


class DisputeResponse(BaseModel):
    """Schema for dispute response."""
    id: str
    customer_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    state: DisputeState

    # Penalty details
    flight_number: Optional[str]
    flight_date: Optional[datetime]
    airline_code: Optional[str]
    claimed_delay_minutes: Optional[int]
    penalty_amount: Optional[float]
    penalty_currency: str
    airline_claimed_reason: Optional[str]

    # Analysis
    actual_delay_minutes: Optional[int]
    handler_responsible_minutes: Optional[int]
    root_cause_analysis: Optional[str]
    responsibility_breakdown: Optional[Dict[str, int]]
    iata_delay_codes: Optional[List[str]]

    # Response
    dispute_response_text: Optional[str]
    user_edited_response: Optional[str]
    recommendation: DisputeRecommendation
    confidence_score: Optional[float]

    # Files
    penalty_notice_file_id: Optional[str]
    evidence_package_file_id: Optional[str]
    response_document_file_id: Optional[str]

    # Outcome
    submitted_at: Optional[datetime]
    resolved_at: Optional[datetime]
    outcome: Optional[str]
    savings_amount: Optional[float]

    class Config:
        from_attributes = True


class DisputeDetailResponse(DisputeResponse):
    """Schema for detailed dispute response with evidence and activities."""
    evidence: List[EvidenceResponse] = []
    activities: List[TurnaroundActivityResponse] = []


class DisputeStatusResponse(BaseModel):
    """Schema for dispute processing status."""
    id: str
    state: DisputeState
    progress_percentage: int = Field(..., ge=0, le=100)
    current_step: str
    error_message: Optional[str]
    estimated_completion_seconds: Optional[int]


class DisputeAnalysisRequest(BaseModel):
    """Schema for submitting evidence and triggering analysis."""
    activities: List[TurnaroundActivityCreate]
    additional_notes: Optional[str] = None


class ResponsibilityBreakdown(BaseModel):
    """Schema for responsibility breakdown."""
    party: ResponsibleParty
    delay_minutes: int
    percentage: float
    explanation: str


class DisputeAnalysisResponse(BaseModel):
    """Schema for analysis results."""
    actual_delay_minutes: int
    handler_responsible_minutes: int
    root_causes: List[Dict[str, Any]]
    responsibility_breakdown: Dict[str, float]
    recommendation: DisputeRecommendation
    confidence: float
    analysis_summary: str
    iata_delay_codes: List[str]


class DisputeExportRequest(BaseModel):
    """Schema for export request."""
    format: str = Field(..., description="Export format: pdf, docx, or txt")
    include_evidence: bool = True
    include_timeline: bool = True


class DisputeStats(BaseModel):
    """Schema for dispute statistics."""
    total_disputes: int
    disputes_this_month: int
    total_penalties_claimed: float
    total_savings: float
    win_rate_percentage: float
    avg_time_to_resolve_minutes: float
    disputes_by_state: Dict[DisputeState, int]
    disputes_by_recommendation: Dict[DisputeRecommendation, int]


class PenaltyExtractionResult(BaseModel):
    """Schema for extracted penalty details from uploaded document."""
    flight_number: str
    flight_date: datetime
    origin: Optional[str]
    destination: Optional[str]
    claimed_delay_minutes: int
    penalty_amount: float
    penalty_currency: str
    airline_claimed_reason: str
    airline_specific_claims: List[str]
    confidence: float
    extraction_notes: Optional[str]
