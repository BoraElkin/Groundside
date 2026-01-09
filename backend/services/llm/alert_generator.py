"""
AI-powered alert generation service.

Uses LLM to generate natural language alerts and recommendations
based on operational data and predictions.
"""
from typing import Dict, List
from anthropic import Anthropic
import json
import structlog

from config import settings

logger = structlog.get_logger()


class AlertGenerator:
    """
    LLM-powered alert message generator.

    Creates clear, actionable alerts with context-aware recommendations.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def generate_delay_alert(
        self,
        flight_data: Dict,
        prediction: Dict,
        turnaround_data: Dict
    ) -> Dict:
        """
        Generate delay prediction alert with recommendations.

        Args:
            flight_data: Flight information
            prediction: ML prediction results
            turnaround_data: Turnaround context

        Returns:
            Alert with title, message, and recommendations
        """
        try:
            prompt = f"""Generate a clear, actionable alert for airport ground operations team.

Flight Information:
{json.dumps(flight_data, indent=2)}

Delay Prediction:
{json.dumps(prediction, indent=2)}

Turnaround Context:
{json.dumps(turnaround_data, indent=2)}

Create an alert with:
1. Clear, concise title (under 60 characters)
2. Detailed message explaining the situation (2-3 sentences)
3. List of 3-5 specific, actionable recommendations
4. Risk level assessment

Return as JSON:
{{
  "title": "alert title",
  "message": "detailed explanation of the situation and impact",
  "recommended_actions": [
    "Specific action 1",
    "Specific action 2",
    "Specific action 3"
  ],
  "priority": "low|medium|high|critical",
  "estimated_impact": "brief impact summary"
}}

Focus on actionable information that operations team can use immediately."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            alert_data = json.loads(response_text)

            logger.info(
                "alert_generated",
                flight=flight_data.get("flight_number"),
                priority=alert_data.get("priority")
            )

            return alert_data

        except Exception as e:
            logger.error("alert_generation_error", error=str(e))
            return self._get_fallback_alert(flight_data, prediction)

    async def generate_resource_alert(
        self,
        resource_type: str,
        shortage_info: Dict,
        affected_flights: List[str]
    ) -> Dict:
        """
        Generate alert for resource shortages.

        Args:
            resource_type: Type of resource (crew, equipment, gate, etc.)
            shortage_info: Details about the shortage
            affected_flights: List of affected flight numbers

        Returns:
            Resource shortage alert
        """
        try:
            prompt = f"""Generate alert for {resource_type} shortage affecting airport operations.

Shortage Details:
{json.dumps(shortage_info, indent=2)}

Affected Flights: {', '.join(affected_flights)}

Create alert with:
- Clear title indicating resource type and severity
- Explanation of shortage and its cause
- List of affected flights
- Specific recommendations to mitigate the shortage
- Timeline/urgency information

Return as JSON with title, message, recommended_actions, priority fields."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1200,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error("resource_alert_error", error=str(e))
            return {
                "title": f"{resource_type.title()} Shortage Detected",
                "message": f"Shortage of {resource_type} affecting {len(affected_flights)} flights.",
                "recommended_actions": ["Review resource allocation", "Contact resource manager"],
                "priority": "high"
            }

    async def generate_cascade_alert(
        self,
        cascade_analysis: Dict,
        initial_flight: str
    ) -> Dict:
        """
        Generate alert for delay cascade situation.

        Args:
            cascade_analysis: Cascade analysis results
            initial_flight: Initial delayed flight number

        Returns:
            Cascade alert with mitigation strategies
        """
        try:
            prompt = f"""Generate alert for delay cascade starting from flight {initial_flight}.

Cascade Analysis:
{json.dumps(cascade_analysis, indent=2)}

Create comprehensive alert explaining:
- The cascade chain and its progression
- Total impact (flights affected, cumulative delays)
- Critical decision points
- Proactive mitigation strategies
- Timeline for intervention

Return as JSON with standard alert structure."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error("cascade_alert_error", error=str(e))
            affected_count = cascade_analysis.get("affected_flights_count", 0)
            return {
                "title": f"Delay Cascade Alert: {affected_count} Flights Affected",
                "message": f"Flight {initial_flight} delay cascading to {affected_count} downstream flights.",
                "recommended_actions": cascade_analysis.get("mitigation_recommendations", []),
                "priority": cascade_analysis.get("cascade_severity", "medium")
            }

    async def format_notification(
        self,
        alert: Dict,
        channel: str = "email"
    ) -> str:
        """
        Format alert for specific notification channel.

        Args:
            alert: Alert dictionary
            channel: Notification channel (email, sms, slack, etc.)

        Returns:
            Formatted message string
        """
        try:
            prompt = f"""Format this alert for {channel} notification:

Alert:
{json.dumps(alert, indent=2)}

Requirements for {channel}:
{'- Keep under 160 characters' if channel == 'sms' else ''}
{'- Use Slack markdown formatting' if channel == 'slack' else ''}
{'- Professional email format with greeting and signature' if channel == 'email' else ''}
- Clear, scannable format
- Maintain urgency and key information

Return only the formatted message text."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error("notification_format_error", error=str(e))
            # Fallback formatting
            if channel == "sms":
                return f"{alert.get('title', 'Alert')}: {alert.get('message', '')[:100]}"
            else:
                return f"{alert.get('title', 'Alert')}\n\n{alert.get('message', '')}"

    def _get_fallback_alert(self, flight_data: Dict, prediction: Dict) -> Dict:
        """Generate basic fallback alert."""
        flight_number = flight_data.get("flight_number", "Unknown")
        predicted_delay = prediction.get("predicted_delay_minutes", 0)

        return {
            "title": f"Delay Predicted: {flight_number} - {predicted_delay} minutes",
            "message": f"Flight {flight_number} is predicted to experience a {predicted_delay} minute delay.",
            "recommended_actions": [
                "Monitor turnaround progress",
                "Review resource allocation",
                "Notify relevant stakeholders"
            ],
            "priority": prediction.get("risk_level", "medium"),
            "estimated_impact": f"{predicted_delay} minute delay predicted"
        }
