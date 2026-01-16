"""
Penalty extractor - parses uploaded penalty notices to extract details.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from agents.shared.llm_client import LLMFactory
from agents.shared.base_llm_client import BaseLLMClient
from agents.shared.prompts import PENALTY_EXTRACTION_PROMPT

logger = structlog.get_logger()


class PenaltyExtractor:
    """
    Extracts penalty details from uploaded documents using configured LLM provider.
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        """
        Initialize penalty extractor.

        Args:
            llm_client: LLM client (creates default from factory if not provided)
        """
        self.llm_client = llm_client or LLMFactory.create_default()

    async def extract_from_text(self, document_text: str) -> Dict[str, Any]:
        """
        Extract penalty details from document text.

        Args:
            document_text: Text content of penalty notice

        Returns:
            Dict with extracted fields:
                - flight_number
                - flight_date
                - origin
                - destination
                - claimed_delay_minutes
                - penalty_amount
                - penalty_currency
                - airline_claimed_reason
                - airline_specific_claims
                - confidence
        """
        logger.info("penalty_extraction_start", text_length=len(document_text))

        prompt = PENALTY_EXTRACTION_PROMPT.format(document_text=document_text)

        try:
            result = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are an expert at extracting structured data from airline penalty notices.",
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for more deterministic extraction
                response_format="json",
            )

            extracted = result.get("parsed_json")

            if not extracted:
                raise ValueError("Failed to parse JSON from LLM response")

            # Convert date string to datetime
            if extracted.get("flight_date"):
                try:
                    extracted["flight_date"] = datetime.fromisoformat(extracted["flight_date"])
                except (ValueError, TypeError):
                    logger.warning("invalid_flight_date", date_str=extracted.get("flight_date"))
                    extracted["flight_date"] = None

            # Ensure numeric fields are correct type
            if extracted.get("claimed_delay_minutes"):
                extracted["claimed_delay_minutes"] = int(extracted["claimed_delay_minutes"])

            if extracted.get("penalty_amount"):
                extracted["penalty_amount"] = float(extracted["penalty_amount"])

            # Default values
            extracted.setdefault("penalty_currency", "USD")
            extracted.setdefault("confidence", 0.9)
            extracted.setdefault("airline_specific_claims", [])

            logger.info(
                "penalty_extraction_success",
                flight_number=extracted.get("flight_number"),
                penalty_amount=extracted.get("penalty_amount"),
                confidence=extracted.get("confidence"),
            )

            return extracted

        except Exception as e:
            logger.error("penalty_extraction_failed", error=str(e))
            raise

    async def extract_from_image(self, image_base64: str, media_type: str = "image/jpeg") -> Dict[str, Any]:
        """
        Extract penalty details from image.

        Args:
            image_base64: Base64-encoded image data
            media_type: MIME type (image/jpeg, image/png)

        Returns:
            Dict with extracted fields
        """
        logger.info("penalty_extraction_from_image_start", media_type=media_type)

        image_data = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_base64,
                },
            }
        ]

        prompt = """Analyze this penalty notice document and extract the following information:

1. Flight number (e.g., TK1234, LH456)
2. Flight date (YYYY-MM-DD format)
3. Origin and destination airports (IATA codes if available)
4. Claimed delay in minutes
5. Penalty amount and currency
6. Reason given by airline for the delay
7. Any specific claims about ground handler responsibility

Respond in JSON format:
{
    "flight_number": "...",
    "flight_date": "YYYY-MM-DD",
    "origin": "...",
    "destination": "...",
    "claimed_delay_minutes": ...,
    "penalty_amount": ...,
    "penalty_currency": "...",
    "airline_claimed_reason": "...",
    "airline_specific_claims": ["...", "..."],
    "confidence": 0.95
}

If any information is not found in the document, use null for that field."""

        try:
            result = await self.llm_client.generate_with_images(
                prompt=prompt,
                image_data=image_data,
                system_prompt="You are an expert at extracting structured data from airline penalty notices.",
                max_tokens=2000,
                temperature=0.3,
            )

            # Parse JSON from response
            content = result["content"]
            extracted = self.llm_client._extract_json(content)

            # Convert date string to datetime
            if extracted.get("flight_date"):
                try:
                    extracted["flight_date"] = datetime.fromisoformat(extracted["flight_date"])
                except (ValueError, TypeError):
                    extracted["flight_date"] = None

            # Ensure numeric fields
            if extracted.get("claimed_delay_minutes"):
                extracted["claimed_delay_minutes"] = int(extracted["claimed_delay_minutes"])

            if extracted.get("penalty_amount"):
                extracted["penalty_amount"] = float(extracted["penalty_amount"])

            extracted.setdefault("penalty_currency", "USD")
            extracted.setdefault("confidence", 0.9)
            extracted.setdefault("airline_specific_claims", [])

            logger.info(
                "penalty_extraction_from_image_success",
                flight_number=extracted.get("flight_number"),
                penalty_amount=extracted.get("penalty_amount"),
            )

            return extracted

        except Exception as e:
            logger.error("penalty_extraction_from_image_failed", error=str(e))
            raise
