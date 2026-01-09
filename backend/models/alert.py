"""
Alert model for notifications and warnings.
"""
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.database import Base


class AlertSeverity(str, enum.Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(str, enum.Enum):
    """Alert type enumeration."""
    DELAY_PREDICTION = "delay_prediction"
    RESOURCE_SHORTAGE = "resource_shortage"
    WEATHER_IMPACT = "weather_impact"
    EQUIPMENT_FAILURE = "equipment_failure"
    CREW_UNAVAILABLE = "crew_unavailable"
    GATE_CONFLICT = "gate_conflict"
    TURNAROUND_AT_RISK = "turnaround_at_risk"
    CASCADE_DELAY = "cascade_delay"
    OPERATIONAL_ISSUE = "operational_issue"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Alert(Base):
    """
    Alert model for system-generated notifications and warnings.
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Associated flight (optional)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=True, index=True)

    # Alert details
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)

    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    recommended_actions = Column(Text)  # JSON array of recommended actions

    # Context
    flight_number = Column(String(10))
    gate = Column(String(10))
    turnaround_id = Column(String(50))
    affected_resource = Column(String(100))

    # Prediction/analysis
    predicted_delay_minutes = Column(Integer)
    confidence_score = Column(Float)  # 0-1 scale
    impact_score = Column(Float)  # 0-1 scale

    # Root cause (from LLM analysis)
    root_cause = Column(Text)
    contributing_factors = Column(Text)  # JSON array

    # Timing
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)

    # User interaction
    acknowledged_by = Column(String(100))
    resolved_by = Column(String(100))
    resolution_notes = Column(Text)

    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(String(200))  # Comma-separated: email,slack,sms

    # Metadata
    source = Column(String(50))  # e.g., "delay_predictor", "llm_transcript_parser"
    metadata = Column(Text)  # JSON object with additional context

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    flight = relationship("Flight", back_populates="alerts")

    def __repr__(self):
        return f"<Alert {self.alert_type} severity={self.severity} status={self.status}>"

    @property
    def is_active(self) -> bool:
        """Check if alert is still active."""
        return self.status == AlertStatus.ACTIVE

    @property
    def is_critical(self) -> bool:
        """Check if alert is critical severity."""
        return self.severity == AlertSeverity.CRITICAL

    @property
    def age_minutes(self) -> int:
        """Get alert age in minutes."""
        if self.triggered_at:
            delta = datetime.utcnow() - self.triggered_at
            return int(delta.total_seconds() / 60)
        return 0
