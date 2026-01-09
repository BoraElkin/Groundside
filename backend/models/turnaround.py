"""
Turnaround and activity models.
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.database import Base


class TurnaroundStatus(str, enum.Enum):
    """Turnaround status enumeration."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    ON_TIME = "on_time"
    AT_RISK = "at_risk"
    DELAYED = "delayed"
    COMPLETED = "completed"


class ActivityType(str, enum.Enum):
    """Turnaround activity type enumeration."""
    AIRCRAFT_ARRIVAL = "aircraft_arrival"
    PASSENGER_DEBOARDING = "passenger_deboarding"
    CARGO_UNLOADING = "cargo_unloading"
    CLEANING = "cleaning"
    CATERING = "catering"
    REFUELING = "refueling"
    WATER_SERVICE = "water_service"
    LAVATORY_SERVICE = "lavatory_service"
    CARGO_LOADING = "cargo_loading"
    PASSENGER_BOARDING = "passenger_boarding"
    PUSHBACK = "pushback"
    AIRCRAFT_DEPARTURE = "aircraft_departure"


class ActivityStatus(str, enum.Enum):
    """Activity status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    BLOCKED = "blocked"


class Turnaround(Base):
    """
    Turnaround model representing the complete ground operation cycle
    from aircraft arrival to departure.
    """
    __tablename__ = "turnarounds"

    id = Column(Integer, primary_key=True, index=True)

    # Associated flight
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False, index=True)

    # Turnaround identification
    turnaround_id = Column(String(50), unique=True, nullable=False, index=True)

    # Status
    status = Column(Enum(TurnaroundStatus), default=TurnaroundStatus.SCHEDULED)

    # Timing
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    scheduled_duration = Column(Integer)  # minutes

    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    actual_duration = Column(Integer)  # minutes

    estimated_completion = Column(DateTime)
    predicted_delay = Column(Integer)  # minutes, from ML model
    prediction_confidence = Column(Float)  # 0-1 scale

    # Gate and resources
    gate = Column(String(10))
    stand = Column(String(10))
    ground_handler = Column(String(100))

    # Critical path analysis
    critical_activity = Column(String(50))  # Current bottleneck activity
    completion_percentage = Column(Float, default=0.0)

    # Risk factors
    risk_score = Column(Float, default=0.0)  # 0-1 scale
    risk_factors = Column(Text)  # JSON array of risk factors

    # Weather impact
    weather_delay_minutes = Column(Integer, default=0)

    # Notes and issues
    notes = Column(Text)
    issues = Column(Text)  # JSON array of issues

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    flight = relationship("Flight", back_populates="turnarounds")
    activities = relationship("TurnaroundActivity", back_populates="turnaround", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Turnaround {self.turnaround_id} status={self.status}>"

    @property
    def is_at_risk(self) -> bool:
        """Check if turnaround is at risk of delay."""
        return self.risk_score > 0.5 or self.status == TurnaroundStatus.AT_RISK

    @property
    def delay_minutes(self) -> int:
        """Calculate current delay in minutes."""
        if self.actual_duration and self.scheduled_duration:
            return max(0, self.actual_duration - self.scheduled_duration)
        return 0


class TurnaroundActivity(Base):
    """
    Individual activity within a turnaround operation.
    """
    __tablename__ = "turnaround_activities"

    id = Column(Integer, primary_key=True, index=True)

    # Associated turnaround
    turnaround_id = Column(Integer, ForeignKey("turnarounds.id"), nullable=False, index=True)

    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False)
    activity_name = Column(String(100), nullable=False)
    status = Column(Enum(ActivityStatus), default=ActivityStatus.PENDING)

    # Timing
    scheduled_start = Column(DateTime)
    scheduled_end = Column(DateTime)
    scheduled_duration = Column(Integer)  # minutes

    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    actual_duration = Column(Integer)  # minutes

    # Dependencies
    depends_on = Column(String(200))  # Comma-separated activity IDs
    is_critical_path = Column(Boolean, default=False)

    # Resource assignment
    assigned_crew = Column(String(200))
    assigned_vehicle = Column(String(50))
    vehicle_location = Column(String(100))  # GPS coordinates or zone

    # Service provider
    service_provider = Column(String(100))
    crew_count = Column(Integer)

    # Progress
    progress_percentage = Column(Float, default=0.0)

    # Delay information
    delay_minutes = Column(Integer, default=0)
    delay_reason = Column(String(200))

    # Notes
    notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    turnaround = relationship("Turnaround", back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.activity_type} status={self.status}>"

    @property
    def is_delayed(self) -> bool:
        """Check if activity is delayed."""
        return self.delay_minutes > 0 or self.status == ActivityStatus.DELAYED
