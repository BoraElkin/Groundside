"""
Delay cascade analysis service.

Analyzes how delays propagate through the flight network
and predicts downstream impacts.
"""
from typing import List, Dict, Set
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class CascadeAnalyzer:
    """
    Service for analyzing delay cascades.

    Predicts how delays propagate through connected flights,
    shared aircraft, crew, and gates.
    """

    def __init__(self):
        pass

    def analyze_cascade(
        self,
        initial_delay: int,
        aircraft_registration: str,
        scheduled_departures: List[Dict],
        gate: str = None
    ) -> Dict:
        """
        Analyze potential delay cascade effects.

        Args:
            initial_delay: Initial delay in minutes
            aircraft_registration: Aircraft registration number
            scheduled_departures: List of scheduled departures for this aircraft
            gate: Gate identifier (optional)

        Returns:
            Cascade analysis with affected flights and total impact
        """
        affected_flights = []
        total_cascaded_delay = 0
        propagation_factor = 0.7  # 70% of delay typically carries over

        # Sort departures by scheduled time
        departures = sorted(
            scheduled_departures,
            key=lambda x: x.get("scheduled_time", datetime.max)
        )

        remaining_delay = initial_delay

        for i, departure in enumerate(departures):
            if remaining_delay <= 5:  # Below threshold, cascade stops
                break

            # Calculate propagated delay
            propagated_delay = round(remaining_delay * propagation_factor)

            # Add buffer time impact
            scheduled_time = departure.get("scheduled_time")
            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

            # Check if there's enough buffer time
            if i > 0:
                prev_arrival = departures[i-1].get("scheduled_arrival")
                if isinstance(prev_arrival, str):
                    prev_arrival = datetime.fromisoformat(prev_arrival.replace('Z', '+00:00'))

                if prev_arrival and scheduled_time:
                    buffer_minutes = (scheduled_time - prev_arrival).total_seconds() / 60
                    # Delay absorbed by buffer
                    absorbed = min(propagated_delay, max(0, buffer_minutes - 60))
                    propagated_delay = max(0, propagated_delay - absorbed)

            if propagated_delay > 0:
                affected_flights.append({
                    "flight_number": departure.get("flight_number"),
                    "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
                    "estimated_delay_minutes": propagated_delay,
                    "impact_level": self._get_impact_level(propagated_delay),
                    "reason": "Aircraft delay cascade"
                })

                total_cascaded_delay += propagated_delay

            # Reduce for next iteration
            remaining_delay = propagated_delay

        # Analyze gate impact if provided
        gate_impact = self._analyze_gate_impact(initial_delay, gate) if gate else None

        cascade_severity = self._calculate_cascade_severity(
            len(affected_flights),
            total_cascaded_delay
        )

        logger.info(
            "cascade_analyzed",
            initial_delay=initial_delay,
            affected_count=len(affected_flights),
            total_impact=total_cascaded_delay,
            severity=cascade_severity
        )

        return {
            "initial_delay_minutes": initial_delay,
            "affected_flights_count": len(affected_flights),
            "affected_flights": affected_flights,
            "total_cascaded_delay_minutes": total_cascaded_delay,
            "cascade_severity": cascade_severity,
            "gate_impact": gate_impact,
            "mitigation_recommendations": self._get_mitigation_recommendations(
                affected_flights,
                total_cascaded_delay
            )
        }

    def analyze_crew_impact(
        self,
        delay: int,
        crew_schedule: List[Dict]
    ) -> Dict:
        """
        Analyze impact on crew schedules.

        Args:
            delay: Delay in minutes
            crew_schedule: List of crew duty periods

        Returns:
            Crew impact analysis
        """
        issues = []
        affected_crew = []

        for crew_duty in crew_schedule:
            duty_end = crew_duty.get("duty_end_time")
            if isinstance(duty_end, str):
                duty_end = datetime.fromisoformat(duty_end.replace('Z', '+00:00'))

            scheduled_completion = crew_duty.get("scheduled_completion_time")
            if isinstance(scheduled_completion, str):
                scheduled_completion = datetime.fromisoformat(
                    scheduled_completion.replace('Z', '+00:00')
                )

            # Check if delay causes duty time violation
            if scheduled_completion and duty_end:
                new_completion = scheduled_completion + timedelta(minutes=delay)
                if new_completion > duty_end:
                    violation_minutes = (new_completion - duty_end).total_seconds() / 60
                    issues.append({
                        "crew_id": crew_duty.get("crew_id"),
                        "issue_type": "duty_time_violation",
                        "violation_minutes": round(violation_minutes),
                        "severity": "critical" if violation_minutes > 30 else "warning"
                    })
                    affected_crew.append(crew_duty.get("crew_id"))

        return {
            "has_crew_issues": len(issues) > 0,
            "affected_crew_count": len(affected_crew),
            "issues": issues,
            "requires_crew_change": len([i for i in issues if i["severity"] == "critical"]) > 0
        }

    def _analyze_gate_impact(self, delay: int, gate: str) -> Dict:
        """
        Analyze impact on gate availability.

        Args:
            delay: Delay in minutes
            gate: Gate identifier

        Returns:
            Gate impact analysis
        """
        # This would query database for next scheduled gate usage
        # For now, return estimated impact

        creates_conflict = delay > 30  # Simplified logic

        return {
            "gate": gate,
            "creates_conflict": creates_conflict,
            "conflict_severity": "high" if delay > 60 else "medium" if creates_conflict else "low",
            "recommended_action": "Reassign gate" if creates_conflict else "Monitor situation"
        }

    def _get_impact_level(self, delay: int) -> str:
        """
        Categorize delay impact level.

        Args:
            delay: Delay in minutes

        Returns:
            Impact level string
        """
        if delay < 15:
            return "low"
        elif delay < 30:
            return "medium"
        elif delay < 60:
            return "high"
        else:
            return "critical"

    def _calculate_cascade_severity(
        self,
        affected_count: int,
        total_delay: int
    ) -> str:
        """
        Calculate overall cascade severity.

        Args:
            affected_count: Number of affected flights
            total_delay: Total cascaded delay in minutes

        Returns:
            Severity level
        """
        severity_score = (affected_count * 10) + (total_delay / 10)

        if severity_score < 50:
            return "low"
        elif severity_score < 150:
            return "medium"
        elif severity_score < 300:
            return "high"
        else:
            return "critical"

    def _get_mitigation_recommendations(
        self,
        affected_flights: List[Dict],
        total_delay: int
    ) -> List[str]:
        """
        Generate mitigation recommendations.

        Args:
            affected_flights: List of affected flights
            total_delay: Total cascaded delay

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if len(affected_flights) == 0:
            return ["No mitigation required - delay contained"]

        if total_delay > 60:
            recommendations.append("Consider aircraft swap to break cascade chain")

        if len(affected_flights) > 3:
            recommendations.append("Alert operations center for network impact")

        if any(f["estimated_delay_minutes"] > 45 for f in affected_flights):
            recommendations.append("Proactively notify affected passengers")
            recommendations.append("Review crew duty times for affected flights")

        if len(affected_flights) > 1:
            recommendations.append("Expedite turnaround procedures where possible")
            recommendations.append("Pre-position equipment for affected flights")

        return recommendations
