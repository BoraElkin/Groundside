"""
Root cause analyzer - determines actual responsibility for delays.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from agents.shared.llm_client import LLMFactory
from agents.shared.base_llm_client import BaseLLMClient
from agents.shared.prompts import ROOT_CAUSE_ANALYSIS_PROMPT
from agents.shared.iata_codes import get_standard_time, is_within_standard

logger = structlog.get_logger()


class RootCauseAnalyzer:
    """
    Analyzes delay root cause and assigns responsibility percentages using configured LLM provider.
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        """
        Initialize root cause analyzer.

        Args:
            llm_client: LLM client (creates default from factory if not provided)
        """
        self.llm_client = llm_client or LLMFactory.create_default()

    async def analyze(
        self,
        flight_number: str,
        flight_date: datetime,
        claimed_delay_minutes: int,
        airline_claimed_reason: str,
        scheduled_arrival: Optional[datetime],
        actual_arrival: Optional[datetime],
        scheduled_departure: Optional[datetime],
        actual_departure: Optional[datetime],
        activities: List[Dict[str, Any]],
        evidence_items: Optional[List[Dict[str, Any]]] = None,
        aircraft_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze root cause of delay.

        Args:
            flight_number: Flight number
            flight_date: Flight date
            claimed_delay_minutes: Delay claimed by airline
            airline_claimed_reason: Airline's stated reason
            scheduled_arrival: Scheduled arrival time
            actual_arrival: Actual arrival time
            scheduled_departure: Scheduled departure time
            actual_departure: Actual departure time
            activities: List of turnaround activities
            evidence_items: Additional evidence
            aircraft_type: Aircraft type for standard comparison

        Returns:
            Dict with:
                - actual_delay_minutes
                - root_causes
                - responsibility_breakdown
                - handler_responsible_minutes
                - iata_delay_codes
                - analysis_summary
                - recommendation
                - confidence
                - key_evidence
        """
        logger.info(
            "root_cause_analysis_start",
            flight_number=flight_number,
            claimed_delay=claimed_delay_minutes,
        )

        # Format activities for prompt
        activities_text = self._format_activities(activities, aircraft_type)

        # Format evidence
        evidence_text = self._format_evidence(evidence_items or [])

        # Format timing
        timing = {
            "scheduled_arrival": scheduled_arrival.isoformat() if scheduled_arrival else "Unknown",
            "actual_arrival": actual_arrival.isoformat() if actual_arrival else "Unknown",
            "scheduled_departure": scheduled_departure.isoformat() if scheduled_departure else "Unknown",
            "actual_departure": actual_departure.isoformat() if actual_departure else "Unknown",
        }

        prompt = ROOT_CAUSE_ANALYSIS_PROMPT.format(
            flight_number=flight_number,
            flight_date=flight_date.strftime("%Y-%m-%d"),
            claimed_delay_minutes=claimed_delay_minutes,
            airline_claimed_reason=airline_claimed_reason,
            scheduled_arrival=timing["scheduled_arrival"],
            actual_arrival=timing["actual_arrival"],
            scheduled_departure=timing["scheduled_departure"],
            actual_departure=timing["actual_departure"],
            turnaround_activities=activities_text,
            evidence_summary=evidence_text,
        )

        try:
            result = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are an aviation operations expert analyzing delay incidents objectively.",
                max_tokens=4000,
                temperature=0.5,
                response_format="json",
            )

            analysis = result.get("parsed_json")

            if not analysis:
                raise ValueError("Failed to parse analysis JSON from LLM")

            # Validate structure
            required_fields = [
                "actual_delay_minutes",
                "root_causes",
                "responsibility_breakdown",
                "handler_responsible_minutes",
                "recommendation",
                "confidence",
            ]

            for field in required_fields:
                if field not in analysis:
                    logger.warning("missing_analysis_field", field=field)
                    analysis[field] = self._get_default_value(field)

            logger.info(
                "root_cause_analysis_success",
                flight_number=flight_number,
                handler_minutes=analysis.get("handler_responsible_minutes"),
                recommendation=analysis.get("recommendation"),
                confidence=analysis.get("confidence"),
            )

            return analysis

        except Exception as e:
            logger.error("root_cause_analysis_failed", error=str(e), flight_number=flight_number)
            raise

    def _format_activities(self, activities: List[Dict[str, Any]], aircraft_type: Optional[str]) -> str:
        """Format activities for LLM prompt."""
        if not activities:
            return "No activity data provided."

        # Determine aircraft size
        aircraft_size = "narrow_body"
        if aircraft_type and any(t in aircraft_type.upper() for t in ["A330", "A350", "B777", "B787", "A380"]):
            aircraft_size = "wide_body"

        lines = ["Activity Log:\n"]

        for act in activities:
            activity_type = act.get("activity_type", "unknown")
            performed_by = act.get("performed_by", "unknown")
            scheduled_start = act.get("scheduled_start")
            actual_start = act.get("actual_start")
            actual_end = act.get("actual_end")
            notes = act.get("notes", "")

            # Calculate duration
            duration = None
            if actual_start and actual_end:
                if isinstance(actual_start, str):
                    actual_start = datetime.fromisoformat(actual_start.replace("Z", "+00:00"))
                if isinstance(actual_end, str):
                    actual_end = datetime.fromisoformat(actual_end.replace("Z", "+00:00"))

                duration = int((actual_end - actual_start).total_seconds() / 60)

                # Check against standard
                standard = get_standard_time(aircraft_size, activity_type)
                within_standard = is_within_standard(aircraft_size, activity_type, duration)
                standard_text = f"{standard['min']}-{standard['max']} min"
                status = "✓ WITHIN STANDARD" if within_standard else "⚠️ OVER STANDARD"
            else:
                duration = "Unknown"
                standard_text = "N/A"
                status = ""

            line = f"- {activity_type.upper()}: {duration} min (standard: {standard_text}) {status}\n"
            line += f"  Performed by: {performed_by}\n"

            if scheduled_start and actual_start:
                if isinstance(scheduled_start, str):
                    scheduled_start = datetime.fromisoformat(scheduled_start.replace("Z", "+00:00"))
                delay = int((actual_start - scheduled_start).total_seconds() / 60)
                if delay > 0:
                    line += f"  Started {delay} min late\n"

            if notes:
                line += f"  Notes: {notes}\n"

            lines.append(line)

        return "\n".join(lines)

    def _format_evidence(self, evidence_items: List[Dict[str, Any]]) -> str:
        """Format evidence for LLM prompt."""
        if not evidence_items:
            return "No additional evidence provided."

        lines = ["Additional Evidence:\n"]

        for ev in evidence_items:
            evidence_type = ev.get("evidence_type", "unknown")
            summary = ev.get("summary", "")
            timestamp = ev.get("timestamp", "")

            line = f"- [{evidence_type.upper()}] {summary}"
            if timestamp:
                line += f" (at {timestamp})"

            lines.append(line)

        return "\n".join(lines)

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing field."""
        defaults = {
            "actual_delay_minutes": 0,
            "root_causes": [],
            "responsibility_breakdown": {
                "handler": 0,
                "airline": 0,
                "airport_atc": 0,
                "weather": 0,
                "vendor_catering": 0,
                "vendor_fuel": 0,
                "vendor_other": 0,
                "passengers": 0,
                "other": 0,
            },
            "handler_responsible_minutes": 0,
            "iata_delay_codes": [],
            "analysis_summary": "Analysis incomplete due to error",
            "recommendation": "unknown",
            "confidence": 0.0,
            "key_evidence": [],
        }
        return defaults.get(field)
