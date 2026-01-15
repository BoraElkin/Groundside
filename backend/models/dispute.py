"""
Dispute and Evidence models for dispute resolution agent.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Enum as SQLEnum, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from models.database import Base


class DisputeState(str, enum.Enum):
    """State of dispute processing."""
    PENALTY_UPLOADED = "penalty_uploaded"
    EXTRACTING_DETAILS = "extracting_details"
    DETAILS_EXTRACTED = "details_extracted"
    GATHERING_EVIDENCE = "gathering_evidence"
    EVIDENCE_GATHERED = "evidence_gathered"
    ANALYZING = "analyzing"
    ANALYSIS_COMPLETE = "analysis_complete"
    GENERATING_RESPONSE = "generating_response"
    RESPONSE_GENERATED = "response_generated"
    USER_REVIEWING = "user_reviewing"
    APPROVED = "approved"
    EXPORTED = "exported"
    FAILED = "failed"


class DisputeRecommendation(str, enum.Enum):
    """Recommended action for dispute."""
    FULL_DISPUTE = "full_dispute"
    PARTIAL_DISPUTE = "partial_dispute"
    ACCEPT = "accept"
    UNKNOWN = "unknown"


class EvidenceType(str, enum.Enum):
    """Type of evidence."""
    TURNAROUND_LOG = "turnaround_log"
    GPS_TRACK = "gps_track"
    COMMUNICATION = "communication"
    WEATHER = "weather"
    AODB_RECORD = "aodb_record"
    VENDOR_LOG = "vendor_log"
    PHOTO = "photo"
    OTHER = "other"


class ResponsibleParty(str, enum.Enum):
    """Who is responsible for delay."""
    HANDLER = "handler"
    AIRLINE = "airline"
    AIRPORT_ATC = "airport_atc"
    WEATHER = "weather"
    VENDOR_CATERING = "vendor_catering"
    VENDOR_FUEL = "vendor_fuel"
    VENDOR_OTHER = "vendor_other"
    PASSENGERS = "passengers"
    OTHER = "other"


class Dispute(Base):
    """
    Dispute model for tracking airline penalty disputes.

    Represents a single dispute case where a ground handler challenges
    an airline's delay penalty claim.
    """
    __tablename__ = "disputes"

    # Identity
    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, index=True)  # Which ground handler
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # State management
    state = Column(SQLEnum(DisputeState), nullable=False, default=DisputeState.PENALTY_UPLOADED, index=True)
    state_history = Column(JSON, default=list)  # [{state: "extracting", timestamp: "...", message: "..."}]
    error_message = Column(Text)  # If state = FAILED

    # Extracted from penalty notice
    flight_number = Column(String, index=True)
    flight_date = Column(DateTime(timezone=True), index=True)
    airline_code = Column(String, index=True)
    aircraft_type = Column(String)
    origin = Column(String)
    destination = Column(String)
    gate = Column(String)

    # Penalty details
    claimed_delay_minutes = Column(Integer)
    penalty_amount = Column(Float)
    penalty_currency = Column(String, default="USD")
    airline_claimed_reason = Column(Text)
    airline_specific_claims = Column(JSON, default=list)  # List of specific claims made

    # Timing details
    scheduled_arrival = Column(DateTime(timezone=True))
    actual_arrival = Column(DateTime(timezone=True))
    scheduled_departure = Column(DateTime(timezone=True))
    actual_departure = Column(DateTime(timezone=True))

    # Our analysis
    actual_delay_minutes = Column(Integer)
    handler_responsible_minutes = Column(Integer)
    root_cause_analysis = Column(Text)
    responsibility_breakdown = Column(JSON, default=dict)  # {handler: 0, airline: 12, vendor_catering: 15}
    iata_delay_codes = Column(JSON, default=list)  # ["32", "11", "93"]

    # Generated response
    dispute_response_text = Column(Text)
    recommendation = Column(SQLEnum(DisputeRecommendation), default=DisputeRecommendation.UNKNOWN, index=True)
    confidence_score = Column(Float)  # 0.0 to 1.0
    generation_metadata = Column(JSON, default=dict)  # LLM model, temperature, tokens used, etc.

    # User edits
    user_edited_response = Column(Text)  # If user modifies the generated response
    user_notes = Column(Text)  # User's notes about the dispute

    # Files
    penalty_notice_file_id = Column(String)  # Uploaded penalty notice
    evidence_package_file_id = Column(String)  # Compiled evidence package
    response_document_file_id = Column(String)  # Final exported response

    # Outcome tracking (for analytics)
    submitted_at = Column(DateTime(timezone=True))  # When dispute was sent to airline
    resolved_at = Column(DateTime(timezone=True))  # When airline responded
    outcome = Column(String)  # "accepted_full", "accepted_partial", "rejected", "pending"
    actual_penalty_charged = Column(Float)  # What airline actually charged (if partial acceptance)
    savings_amount = Column(Float)  # How much was saved

    # Relationships
    evidence = relationship("Evidence", back_populates="dispute", cascade="all, delete-orphan")
    activities = relationship("DisputeTurnaroundActivity", back_populates="dispute", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dispute {self.id}: {self.flight_number} on {self.flight_date} - {self.state}>"


class Evidence(Base):
    """
    Evidence item supporting a dispute.

    Each evidence item represents a piece of data that supports
    the handler's position in the dispute.
    """
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False, index=True)

    # Evidence details
    evidence_type = Column(SQLEnum(EvidenceType), nullable=False, index=True)
    source = Column(String)  # "AODB", "GPS system", "Radio log", "Weather API"
    timestamp = Column(DateTime(timezone=True), index=True)

    # Content
    summary = Column(Text)  # Human-readable summary
    raw_data = Column(JSON, default=dict)  # Original data
    file_id = Column(String)  # If evidence is a file (photo, PDF, etc.)

    # Analysis
    supports_dispute = Column(Boolean, default=True)  # True if this helps handler's case
    relevance_score = Column(Float)  # 0.0 to 1.0
    responsible_party = Column(SQLEnum(ResponsibleParty))
    delay_minutes_attributed = Column(Integer)  # How many minutes of delay this evidence explains

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes = Column(Text)

    # Relationships
    dispute = relationship("Dispute", back_populates="evidence")

    def __repr__(self):
        return f"<Evidence {self.id}: {self.evidence_type} for {self.dispute_id}>"


class DisputeTurnaroundActivity(Base):
    """
    Turnaround activity log for a disputed flight.

    Tracks what happened during the turnaround and who was responsible.
    """
    __tablename__ = "dispute_turnaround_activities"

    id = Column(String, primary_key=True, index=True)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False, index=True)

    # Activity details
    activity_type = Column(String, nullable=False)  # deboarding, cleaning, catering, fueling, boarding, pushback
    performed_by = Column(SQLEnum(ResponsibleParty), nullable=False)  # Who performed this activity

    # Timing
    scheduled_start = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    scheduled_end = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))

    # Calculated
    scheduled_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer)
    delay_minutes = Column(Integer)  # How late this activity made the departure

    # Status
    status = Column(String, default="completed")  # completed, in_progress, cancelled, delayed

    # Details
    notes = Column(Text)  # Any special circumstances
    standard_duration_min = Column(Integer)  # Industry standard for this activity
    standard_duration_max = Column(Integer)
    was_within_standard = Column(Boolean)  # True if actual duration was within industry standard

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    dispute = relationship("Dispute", back_populates="activities")

    def __repr__(self):
        return f"<DisputeTurnaroundActivity {self.activity_type} for {self.dispute_id}>"


class DisputeTemplate(Base):
    """
    Template for dispute responses customized per airline.

    Some airlines prefer specific formats or language.
    """
    __tablename__ = "dispute_templates"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, index=True)  # Which handler created this

    # Template details
    name = Column(String, nullable=False)
    airline_code = Column(String, index=True)  # Specific airline or "default"
    language = Column(String, default="en")

    # Template content
    header_template = Column(Text)
    body_template = Column(Text)
    footer_template = Column(Text)

    # Customization
    tone = Column(String, default="professional")  # professional, formal, friendly
    include_iata_codes = Column(Boolean, default=True)
    include_evidence_summary = Column(Boolean, default=True)
    include_timeline = Column(Boolean, default=True)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    usage_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<DisputeTemplate {self.name} for {self.airline_code}>"
