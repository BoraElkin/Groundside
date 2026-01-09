"""
Flight data model.
"""
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models.database import Base


class FlightType(str, enum.Enum):
    """Flight type enumeration."""
    ARRIVAL = "arrival"
    DEPARTURE = "departure"


class FlightStatus(str, enum.Enum):
    """Flight status enumeration."""
    SCHEDULED = "scheduled"
    AIRBORNE = "airborne"
    LANDED = "landed"
    AT_GATE = "at_gate"
    BOARDING = "boarding"
    DEPARTED = "departed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class Flight(Base):
    """
    Flight model representing scheduled and actual flight information.

    Tracks both inbound and outbound flights with their schedules,
    actual times, and operational details.
    """
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)

    # Flight identification
    flight_number = Column(String(10), nullable=False, index=True)
    airline_code = Column(String(3), nullable=False, index=True)  # IATA code
    airline_name = Column(String(100), nullable=False)

    # Flight type and status
    flight_type = Column(Enum(FlightType), nullable=False)
    status = Column(Enum(FlightStatus), default=FlightStatus.SCHEDULED)

    # Aircraft information
    aircraft_type = Column(String(10), nullable=False)  # e.g., A321, B737
    aircraft_registration = Column(String(10))
    aircraft_config = Column(String(20))  # e.g., "narrow-body", "wide-body"

    # Route information
    origin_airport = Column(String(3), nullable=False)  # IATA code
    destination_airport = Column(String(3), nullable=False)  # IATA code

    # Gate and stand
    gate = Column(String(10))
    stand = Column(String(10))
    terminal = Column(String(10))

    # Scheduled times (UTC)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    scheduled_arrival = Column(DateTime)  # For arrivals
    scheduled_departure = Column(DateTime)  # For departures

    # Estimated times
    estimated_time = Column(DateTime)
    estimated_arrival = Column(DateTime)
    estimated_departure = Column(DateTime)

    # Actual times
    actual_time = Column(DateTime)
    actual_arrival = Column(DateTime)
    actual_departure = Column(DateTime)

    # Delay information (in minutes)
    arrival_delay = Column(Integer, default=0)
    departure_delay = Column(Integer, default=0)
    predicted_delay = Column(Integer)  # ML prediction

    # Ground handler
    ground_handler = Column(String(100))
    handler_code = Column(String(10))

    # Passenger information
    passenger_count = Column(Integer)
    passenger_capacity = Column(Integer)
    load_factor = Column(Float)  # Percentage

    # Cargo
    cargo_weight = Column(Float)  # kg
    baggage_count = Column(Integer)

    # Weather and conditions
    weather_code = Column(String(10))
    weather_impact_score = Column(Float)  # 0-1 scale

    # Operational notes
    notes = Column(Text)
    delay_reason = Column(String(200))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    turnarounds = relationship("Turnaround", back_populates="flight", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="flight", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Flight {self.airline_code}{self.flight_number} {self.origin_airport}-{self.destination_airport}>"

    @property
    def is_delayed(self) -> bool:
        """Check if flight is delayed."""
        if self.flight_type == FlightType.ARRIVAL:
            return (self.arrival_delay or 0) > 15
        else:
            return (self.departure_delay or 0) > 15

    @property
    def delay_minutes(self) -> int:
        """Get current delay in minutes."""
        if self.flight_type == FlightType.ARRIVAL:
            return self.arrival_delay or 0
        else:
            return self.departure_delay or 0
