"""
Radio transcript parsing service using LLM.

Uses Anthropic Claude to parse and extract structured information
from radio communications and operational transcripts.
"""
from typing import Dict, List, Optional
from anthropic import Anthropic
import json
import structlog

from config import settings

logger = structlog.get_logger()


class TranscriptParser:
    """
    LLM-powered transcript parser for radio communications.

    Extracts structured operational intelligence from unstructured
    radio chatter, messages, and logs.
    """

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def parse_radio_transcript(
        self,
        transcript: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Parse radio transcript and extract operational information.

        Args:
            transcript: Raw radio transcript text
            context: Optional context (flight numbers, gates, etc.)

        Returns:
            Structured information extracted from transcript
        """
        try:
            # Build context string
            context_str = ""
            if context:
                context_str = f"\nContext: {json.dumps(context, indent=2)}"

            # Create prompt for Claude
            prompt = f"""Analyze this airport ground operations radio transcript and extract structured information.

{context_str}

Transcript:
{transcript}

Extract and return a JSON object with the following structure:
{{
  "mentioned_flights": ["list of flight numbers mentioned"],
  "issues_detected": [
    {{
      "issue_type": "delay|equipment|weather|crew|other",
      "description": "clear description",
      "severity": "low|medium|high|critical",
      "affected_resource": "flight/gate/equipment identifier"
    }}
  ],
  "urgency_level": "low|medium|high|critical",
  "recommended_actions": ["list of recommended immediate actions"],
  "extracted_entities": {{
    "gates": ["gate identifiers"],
    "aircraft": ["aircraft registrations or types"],
    "personnel": ["crew or staff mentions"],
    "equipment": ["equipment mentions"]
  }},
  "summary": "brief 1-2 sentence summary"
}}

Focus on operational issues, delays, equipment problems, and safety concerns.
Return only valid JSON."""

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,  # Low temperature for structured extraction
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract and parse JSON response
            response_text = response.content[0].text

            # Try to parse JSON from response
            # Claude might wrap it in markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            parsed_data = json.loads(response_text)

            logger.info(
                "transcript_parsed",
                issues_count=len(parsed_data.get("issues_detected", [])),
                urgency=parsed_data.get("urgency_level"),
                flights=len(parsed_data.get("mentioned_flights", []))
            )

            return parsed_data

        except json.JSONDecodeError as e:
            logger.error("json_parse_error", error=str(e), response=response_text)
            return self._get_fallback_response(transcript)

        except Exception as e:
            logger.error("transcript_parse_error", error=str(e))
            return self._get_fallback_response(transcript)

    async def analyze_operational_message(
        self,
        message: str,
        message_type: str = "general"
    ) -> Dict:
        """
        Analyze operational messages (emails, SMS, app messages).

        Args:
            message: Message text
            message_type: Type of message (email, sms, app, etc.)

        Returns:
            Analyzed message with extracted information
        """
        try:
            prompt = f"""Analyze this ground operations {message_type} message and extract key information.

Message:
{message}

Extract:
1. Main topic/purpose
2. Any time-critical information
3. Required actions
4. Mentioned resources (flights, gates, equipment)
5. Priority level

Return as JSON:
{{
  "topic": "main topic",
  "is_time_critical": true/false,
  "priority": "low|medium|high|urgent",
  "required_actions": ["action items"],
  "mentioned_resources": {{
    "flights": [],
    "gates": [],
    "equipment": []
  }},
  "deadline": "extracted deadline if any",
  "summary": "brief summary"
}}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error("message_analysis_error", error=str(e))
            return {
                "topic": "unknown",
                "is_time_critical": False,
                "priority": "low",
                "required_actions": [],
                "summary": message[:200]
            }

    async def extract_delay_information(
        self,
        text: str,
        flight_number: str
    ) -> Dict:
        """
        Extract delay-related information from free text.

        Args:
            text: Free text containing delay information
            flight_number: Associated flight number

        Returns:
            Structured delay information
        """
        try:
            prompt = f"""Extract delay information for flight {flight_number} from this text:

{text}

Return JSON:
{{
  "delay_duration_minutes": estimated delay in minutes (number or null),
  "delay_reason": "primary reason for delay",
  "root_cause": "underlying root cause",
  "affected_activities": ["list of affected turnaround activities"],
  "is_recoverable": true/false,
  "estimated_recovery_time": minutes to recover (number or null)
}}"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error("delay_extraction_error", error=str(e))
            return {
                "delay_duration_minutes": None,
                "delay_reason": "Unknown",
                "root_cause": "Unable to extract",
                "affected_activities": [],
                "is_recoverable": False
            }

    def _get_fallback_response(self, transcript: str) -> Dict:
        """
        Generate fallback response when LLM fails.

        Args:
            transcript: Original transcript

        Returns:
            Basic structured response
        """
        return {
            "mentioned_flights": [],
            "issues_detected": [],
            "urgency_level": "low",
            "recommended_actions": ["Manual review required"],
            "extracted_entities": {
                "gates": [],
                "aircraft": [],
                "personnel": [],
                "equipment": []
            },
            "summary": "Automated parsing failed - manual review recommended",
            "raw_transcript": transcript[:500]
        }
