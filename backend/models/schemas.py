"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum


# Enums
class FlightTypeSchema(str, Enum):
    ARRIVAL = "arrival"
    DEPARTURE = "departure"


class FlightStatusSchema(str, Enum):
    SCHEDULED = "scheduled"
    AIRBORNE = "airborne"
    LANDED = "landed"
    AT_GATE = "at_gate"
    BOARDING = "boarding"
    DEPARTED = "departed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class TurnaroundStatusSchema(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    ON_TIME = "on_time"
    AT_RISK = "at_risk"
    DELAYED = "delayed"
    COMPLETED = "completed"


class AlertSeveritySchema(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatusSchema(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# Flight Schemas
class FlightBase(BaseModel):
    """Base flight schema."""
    flight_number: str
    airline_code: str
    airline_name: str
    flight_type: FlightTypeSchema
    aircraft_type: str
    origin_airport: str
    destination_airport: str
    scheduled_time: datetime


class FlightCreate(FlightBase):
    """Schema for creating a flight."""
    gate: Optional[str] = None
    stand: Optional[str] = None
    terminal: Optional[str] = None
    ground_handler: Optional[str] = None
    passenger_count: Optional[int] = None


class FlightUpdate(BaseModel):
    """Schema for updating a flight."""
    status: Optional[FlightStatusSchema] = None
    estimated_time: Optional[datetime] = None
    actual_time: Optional[datetime] = None
    gate: Optional[str] = None
    arrival_delay: Optional[int] = None
    departure_delay: Optional[int] = None


class FlightResponse(FlightBase):
    """Schema for flight response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: FlightStatusSchema
    gate: Optional[str] = None
    stand: Optional[str] = None
    estimated_time: Optional[datetime] = None
    actual_time: Optional[datetime] = None
    arrival_delay: Optional[int] = 0
    departure_delay: Optional[int] = 0
    predicted_delay: Optional[int] = None
    ground_handler: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Turnaround Schemas
class TurnaroundActivitySchema(BaseModel):
    """Schema for turnaround activity."""
    model_config = ConfigDict(from_attributes=True)

    activity_type: str
    activity_name: str
    status: str
    scheduled_start: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    progress_percentage: float = 0.0
    delay_minutes: int = 0


class TurnaroundBase(BaseModel):
    """Base turnaround schema."""
    turnaround_id: str
    flight_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    scheduled_duration: int


class TurnaroundCreate(TurnaroundBase):
    """Schema for creating a turnaround."""
    gate: Optional[str] = None
    stand: Optional[str] = None
    ground_handler: Optional[str] = None


class TurnaroundUpdate(BaseModel):
    """Schema for updating a turnaround."""
    status: Optional[TurnaroundStatusSchema] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    predicted_delay: Optional[int] = None
    risk_score: Optional[float] = None


class TurnaroundResponse(TurnaroundBase):
    """Schema for turnaround response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TurnaroundStatusSchema
    actual_start: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    predicted_delay: Optional[int] = None
    prediction_confidence: Optional[float] = None
    completion_percentage: float = 0.0
    risk_score: float = 0.0
    activities: List[TurnaroundActivitySchema] = []
    created_at: datetime
    updated_at: datetime


# Alert Schemas
class AlertBase(BaseModel):
    """Base alert schema."""
    alert_type: str
    severity: AlertSeveritySchema
    title: str
    message: str


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    flight_id: Optional[int] = None
    flight_number: Optional[str] = None
    recommended_actions: Optional[str] = None
    predicted_delay_minutes: Optional[int] = None
    confidence_score: Optional[float] = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    status: Optional[AlertStatusSchema] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertResponse(AlertBase):
    """Schema for alert response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: AlertStatusSchema
    flight_id: Optional[int] = None
    flight_number: Optional[str] = None
    recommended_actions: Optional[str] = None
    predicted_delay_minutes: Optional[int] = None
    confidence_score: Optional[float] = None
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# Analytics Schemas
class DelayStatistics(BaseModel):
    """Delay statistics schema."""
    total_flights: int
    delayed_flights: int
    average_delay_minutes: float
    on_time_percentage: float
    most_delayed_airline: Optional[str] = None
    most_delayed_route: Optional[str] = None


class TurnaroundStatistics(BaseModel):
    """Turnaround statistics schema."""
    total_turnarounds: int
    completed_on_time: int
    at_risk: int
    delayed: int
    average_duration_minutes: float
    average_delay_minutes: float


class PredictionResult(BaseModel):
    """ML prediction result schema."""
    flight_id: int
    predicted_delay_minutes: int
    confidence: float
    risk_level: str
    contributing_factors: List[str]
    recommended_actions: List[str]


# WebSocket Message Schemas
class WSMessage(BaseModel):
    """WebSocket message schema."""
    type: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
