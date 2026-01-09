"""
LLM-powered root cause analysis service.

Uses AI to analyze delays and operational issues to identify
root causes and patterns.
"""
from typing import Dict, List, Optional
from anthropic import Anthropic
import json
import structlog

from config import settings

logger = structlog.get_logger()


class RootCauseAnalyzer:
    """
    AI-powered root cause analysis for operational delays.

    Analyzes complex operational data to identify underlying causes
    and patterns in delays and inefficiencies.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def analyze_delay(
        self,
        flight_data: Dict,
        turnaround_activities: List[Dict],
        historical_context: Optional[Dict] = None
    ) -> Dict:
        """
        Perform root cause analysis on a delay.

        Args:
            flight_data: Flight information
            turnaround_activities: List of turnaround activities with timings
            historical_context: Optional historical data for context

        Returns:
            Root cause analysis with recommendations
        """
        try:
            # Build context
            context_str = ""
            if historical_context:
                context_str = f"\n\nHistorical Context:\n{json.dumps(historical_context, indent=2)}"

            prompt = f"""Perform root cause analysis on this flight delay.

Flight Data:
{json.dumps(flight_data, indent=2)}

Turnaround Activities:
{json.dumps(turnaround_activities, indent=2)}
{context_str}

Analyze:
1. What was the primary root cause of the delay?
2. What were contributing factors?
3. Was this delay preventable? If so, how?
4. Are there systemic issues indicated?
5. What patterns are evident?
6. Specific recommendations to prevent recurrence

Return as JSON:
{{
  "root_cause": "primary root cause with specific details",
  "root_cause_category": "equipment|crew|weather|process|coordination|other",
  "contributing_factors": [
    {{"factor": "description", "impact_percentage": 20}}
  ],
  "preventable": true/false,
  "prevention_methods": ["specific preventive measures"],
  "systemic_issues": ["any underlying systemic problems identified"],
  "pattern_analysis": "description of patterns if any",
  "recommendations": [
    {{
      "recommendation": "specific action",
      "priority": "immediate|short-term|long-term",
      "expected_impact": "description of expected improvement"
    }}
  ],
  "confidence_level": "low|medium|high"
}}

Be specific and data-driven in the analysis."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            analysis = json.loads(response_text)

            logger.info(
                "root_cause_analyzed",
                flight=flight_data.get("flight_number"),
                root_cause_category=analysis.get("root_cause_category"),
                preventable=analysis.get("preventable")
            )

            return analysis

        except Exception as e:
            logger.error("root_cause_analysis_error", error=str(e))
            return self._get_fallback_analysis()

    async def analyze_pattern(
        self,
        delays: List[Dict],
        timeframe: str = "7 days"
    ) -> Dict:
        """
        Analyze patterns across multiple delays.

        Args:
            delays: List of delay incidents
            timeframe: Time period for analysis

        Returns:
            Pattern analysis with insights
        """
        try:
            prompt = f"""Analyze patterns in these delays over the past {timeframe}.

Delays Data:
{json.dumps(delays[:20], indent=2)}  # Limit to 20 most recent

Total delays in period: {len(delays)}

Identify:
1. Common root causes and their frequency
2. Time-based patterns (time of day, day of week)
3. Resource-related patterns (specific gates, aircraft types, handlers)
4. Cascade patterns
5. Seasonal or operational patterns
6. Emerging trends

Return as JSON:
{{
  "most_common_causes": [
    {{"cause": "description", "frequency": 15, "percentage": 30}}
  ],
  "time_patterns": {{
    "peak_delay_hours": ["hour ranges"],
    "peak_delay_days": ["day names"],
    "pattern_description": "description"
  }},
  "resource_patterns": {{
    "problematic_gates": ["gate IDs"],
    "problematic_aircraft_types": ["types"],
    "problematic_handlers": ["handler names"]
  }},
  "trends": [
    {{"trend": "description", "direction": "improving|worsening|stable"}}
  ],
  "key_insights": ["list of key insights"],
  "strategic_recommendations": ["high-level recommendations"]
}}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error("pattern_analysis_error", error=str(e))
            return {
                "most_common_causes": [],
                "time_patterns": {},
                "resource_patterns": {},
                "trends": [],
                "key_insights": ["Analysis unavailable"],
                "strategic_recommendations": []
            }

    async def generate_performance_report(
        self,
        metrics: Dict,
        period: str = "weekly"
    ) -> str:
        """
        Generate natural language performance report.

        Args:
            metrics: Performance metrics dictionary
            period: Reporting period

        Returns:
            Formatted performance report text
        """
        try:
            prompt = f"""Generate a concise {period} performance report for airport ground operations.

Metrics:
{json.dumps(metrics, indent=2)}

Create a professional report with:
1. Executive summary (2-3 sentences)
2. Key performance highlights
3. Areas of concern
4. Notable improvements or deteriorations
5. Actionable recommendations

Format as a readable report, not JSON."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            report = response.content[0].text

            logger.info("performance_report_generated", period=period)

            return report

        except Exception as e:
            logger.error("report_generation_error", error=str(e))
            return f"Performance Report - {period}\n\nReport generation failed. Please review metrics manually."

    async def compare_incidents(
        self,
        incident1: Dict,
        incident2: Dict
    ) -> Dict:
        """
        Compare two similar incidents to identify differences and learnings.

        Args:
            incident1: First incident data
            incident2: Second incident data

        Returns:
            Comparison analysis
        """
        try:
            prompt = f"""Compare these two similar delay incidents and identify key differences and learnings.

Incident 1:
{json.dumps(incident1, indent=2)}

Incident 2:
{json.dumps(incident2, indent=2)}

Analyze:
- Similarities and differences
- Why one might have been worse/better
- What was done differently
- Lessons learned

Return as JSON with: similarities, differences, lessons_learned, recommendations"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error("incident_comparison_error", error=str(e))
            return {
                "similarities": [],
                "differences": [],
                "lessons_learned": [],
                "recommendations": []
            }

    def _get_fallback_analysis(self) -> Dict:
        """Generate fallback analysis when LLM fails."""
        return {
            "root_cause": "Analysis unavailable - manual investigation required",
            "root_cause_category": "other",
            "contributing_factors": [],
            "preventable": False,
            "prevention_methods": [],
            "systemic_issues": [],
            "pattern_analysis": "Automated analysis failed",
            "recommendations": [{
                "recommendation": "Conduct manual root cause analysis",
                "priority": "immediate",
                "expected_impact": "Better understanding of delay cause"
            }],
            "confidence_level": "low"
        }
