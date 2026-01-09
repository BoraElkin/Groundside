"""
Turnaround duration estimation service.

Estimates expected turnaround duration based on aircraft type,
flight parameters, and operational conditions.
"""
from typing import Dict, List
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class TurnaroundEstimator:
    """
    Service for estimating turnaround durations.

    Provides baseline and adjusted estimates based on operational factors.
    """

    # Baseline turnaround times (in minutes) by aircraft category
    BASELINE_DURATIONS = {
        "narrow_body_short": 45,    # A320, B737 for short haul
        "narrow_body_medium": 55,    # A321, B738 for medium haul
        "wide_body_short": 75,       # A330, B777 for short haul
        "wide_body_long": 120,       # A330, B777, A350 for long haul
        "super_wide": 180,           # A380, B747 for long haul
    }

    # Activity duration estimates (in minutes)
    ACTIVITY_DURATIONS = {
        "aircraft_arrival": 5,
        "passenger_deboarding": 15,
        "cargo_unloading": 20,
        "cleaning": 25,
        "catering": 18,
        "refueling": 20,
        "water_service": 10,
        "lavatory_service": 8,
        "cargo_loading": 25,
        "passenger_boarding": 30,
        "pushback": 5,
        "aircraft_departure": 5,
    }

    def __init__(self):
        pass

    def estimate_turnaround(
        self,
        aircraft_type: str,
        flight_type: str,
        passenger_count: int,
        has_cargo: bool = True,
        is_international: bool = False
    ) -> Dict:
        """
        Estimate turnaround duration and breakdown.

        Args:
            aircraft_type: Aircraft type code (e.g., "A321")
            flight_type: "short", "medium", or "long" haul
            passenger_count: Number of passengers
            has_cargo: Whether flight has cargo
            is_international: Whether it's an international flight

        Returns:
            Dictionary with total estimate and activity breakdown
        """
        # Get aircraft category
        category = self._get_aircraft_category(aircraft_type, flight_type)

        # Get baseline duration
        baseline = self.BASELINE_DURATIONS.get(category, 60)

        # Calculate activity durations with adjustments
        activities = self._calculate_activity_durations(
            aircraft_type,
            passenger_count,
            has_cargo,
            is_international
        )

        # Calculate total from critical path
        total_duration = self._calculate_critical_path(activities)

        # Apply operational adjustments
        adjusted_duration = self._apply_adjustments(
            total_duration,
            aircraft_type,
            passenger_count,
            is_international
        )

        logger.info(
            "turnaround_estimated",
            aircraft=aircraft_type,
            baseline=baseline,
            adjusted=adjusted_duration
        )

        return {
            "estimated_duration_minutes": round(adjusted_duration),
            "baseline_duration_minutes": baseline,
            "activities": activities,
            "critical_path_activities": self._get_critical_path_activities(activities),
            "buffer_minutes": round(adjusted_duration * 0.1)  # 10% buffer
        }

    def _get_aircraft_category(self, aircraft_type: str, flight_type: str) -> str:
        """
        Determine aircraft category for baseline lookup.

        Args:
            aircraft_type: Aircraft type
            flight_type: Flight haul type

        Returns:
            Category key
        """
        wide_body = ["A330", "A340", "A350", "B777", "B787"]
        super_wide = ["A380", "B747"]
        large_narrow = ["A321", "B757"]

        if aircraft_type in super_wide:
            return "super_wide"
        elif aircraft_type in wide_body:
            return "wide_body_long" if flight_type == "long" else "wide_body_short"
        elif aircraft_type in large_narrow:
            return "narrow_body_medium"
        else:
            return "narrow_body_short"

    def _calculate_activity_durations(
        self,
        aircraft_type: str,
        passenger_count: int,
        has_cargo: bool,
        is_international: bool
    ) -> List[Dict]:
        """
        Calculate duration for each turnaround activity.

        Args:
            aircraft_type: Aircraft type
            passenger_count: Passenger count
            has_cargo: Has cargo flag
            is_international: International flight flag

        Returns:
            List of activity dictionaries with durations
        """
        activities = []

        # Arrival
        activities.append({
            "activity_type": "aircraft_arrival",
            "duration_minutes": 5,
            "can_parallel": False
        })

        # Deboarding (scales with passenger count)
        deboarding_time = max(10, (passenger_count / 180) * 20)
        if is_international:
            deboarding_time *= 1.2

        activities.append({
            "activity_type": "passenger_deboarding",
            "duration_minutes": round(deboarding_time),
            "can_parallel": False
        })

        # Cargo unloading (if applicable, can parallel with other activities)
        if has_cargo:
            wide_body = aircraft_type in ["A330", "B777", "A380", "B787", "B747"]
            cargo_time = 25 if wide_body else 15

            activities.append({
                "activity_type": "cargo_unloading",
                "duration_minutes": cargo_time,
                "can_parallel": True
            })

        # Cleaning (scales with aircraft size)
        cleaning_time = self._get_cleaning_duration(aircraft_type, is_international)
        activities.append({
            "activity_type": "cleaning",
            "duration_minutes": cleaning_time,
            "can_parallel": True
        })

        # Catering
        activities.append({
            "activity_type": "catering",
            "duration_minutes": 18,
            "can_parallel": True
        })

        # Refueling (can parallel)
        refuel_time = self._get_refueling_duration(aircraft_type)
        activities.append({
            "activity_type": "refueling",
            "duration_minutes": refuel_time,
            "can_parallel": True
        })

        # Water and lavatory service
        activities.append({
            "activity_type": "water_service",
            "duration_minutes": 10,
            "can_parallel": True
        })

        activities.append({
            "activity_type": "lavatory_service",
            "duration_minutes": 8,
            "can_parallel": True
        })

        # Cargo loading
        if has_cargo:
            activities.append({
                "activity_type": "cargo_loading",
                "duration_minutes": cargo_time,
                "can_parallel": True
            })

        # Boarding (scales with passenger count)
        boarding_time = max(15, (passenger_count / 150) * 25)
        if is_international:
            boarding_time *= 1.15

        activities.append({
            "activity_type": "passenger_boarding",
            "duration_minutes": round(boarding_time),
            "can_parallel": False
        })

        # Departure prep
        activities.append({
            "activity_type": "pushback",
            "duration_minutes": 5,
            "can_parallel": False
        })

        return activities

    def _get_cleaning_duration(self, aircraft_type: str, is_international: bool) -> int:
        """Get cleaning duration based on aircraft size."""
        wide_body = aircraft_type in ["A330", "B777", "A380", "B787", "B747"]
        super_wide = aircraft_type in ["A380", "B747"]

        if super_wide:
            base = 40
        elif wide_body:
            base = 30
        else:
            base = 20

        # International flights get deep clean
        if is_international:
            base *= 1.3

        return round(base)

    def _get_refueling_duration(self, aircraft_type: str) -> int:
        """Get refueling duration based on aircraft size."""
        wide_body = aircraft_type in ["A330", "B777", "A380", "B787", "B747"]
        return 30 if wide_body else 20

    def _calculate_critical_path(self, activities: List[Dict]) -> float:
        """
        Calculate total duration based on critical path.

        Sequential activities add linearly, parallel activities overlap.

        Args:
            activities: List of activity dictionaries

        Returns:
            Total duration in minutes
        """
        sequential_time = sum(
            a["duration_minutes"]
            for a in activities
            if not a["can_parallel"]
        )

        parallel_time = max(
            (a["duration_minutes"] for a in activities if a["can_parallel"]),
            default=0
        )

        return sequential_time + parallel_time

    def _get_critical_path_activities(self, activities: List[Dict]) -> List[str]:
        """
        Identify activities on the critical path.

        Args:
            activities: List of activity dictionaries

        Returns:
            List of critical activity types
        """
        # Sequential activities are always critical
        critical = [a["activity_type"] for a in activities if not a["can_parallel"]]

        # Longest parallel activity is critical
        parallel_activities = [a for a in activities if a["can_parallel"]]
        if parallel_activities:
            longest = max(parallel_activities, key=lambda x: x["duration_minutes"])
            critical.append(longest["activity_type"])

        return critical

    def _apply_adjustments(
        self,
        base_duration: float,
        aircraft_type: str,
        passenger_count: int,
        is_international: bool
    ) -> float:
        """
        Apply operational adjustments to base estimate.

        Args:
            base_duration: Base duration estimate
            aircraft_type: Aircraft type
            passenger_count: Passenger count
            is_international: International flag

        Returns:
            Adjusted duration
        """
        adjusted = base_duration

        # High load factor adjustment
        if passenger_count > 200:
            adjusted *= 1.05

        # Add coordination buffer for international flights
        if is_international:
            adjusted += 10

        return adjusted
