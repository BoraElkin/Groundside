"""
Response generator - creates professional dispute response letters.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from agents.shared.llm_client import LLMFactory
from agents.shared.base_llm_client import BaseLLMClient
from agents.shared.prompts import (
    DISPUTE_RESPONSE_GENERATION_PROMPT,
    EVIDENCE_SUMMARIZATION_PROMPT,
    RESPONSE_REGENERATION_PROMPT,
)

logger = structlog.get_logger()


class ResponseGenerator:
    """
    Generates professional dispute response letters using configured LLM provider.
    """

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        """
        Initialize response generator.

        Args:
            llm_client: LLM client (creates default from factory if not provided)
        """
        self.llm_client = llm_client or LLMFactory.create_default()

    async def generate(
        self,
        handler_name: str,
        airline_name: str,
        flight_number: str,
        flight_date: datetime,
        origin: Optional[str],
        destination: Optional[str],
        penalty_amount: float,
        penalty_currency: str,
        airline_claimed_reason: str,
        root_cause_analysis: Dict[str, Any],
        evidence_items: List[Dict[str, Any]],
        iata_codes: List[str],
        recommendation: str,
    ) -> Dict[str, Any]:
        """
        Generate dispute response letter.

        Args:
            handler_name: Ground handler name
            airline_name: Airline name
            flight_number: Flight number
            flight_date: Flight date
            origin: Origin airport
            destination: Destination airport
            penalty_amount: Penalty amount
            penalty_currency: Currency
            airline_claimed_reason: Airline's stated reason
            root_cause_analysis: Analysis from RootCauseAnalyzer
            evidence_items: List of evidence
            iata_codes: IATA delay codes
            recommendation: full_dispute, partial_dispute, or accept

        Returns:
            Dict with:
                - response_text: Generated letter
                - metadata: Generation metadata (tokens, model, etc.)
        """
        logger.info(
            "response_generation_start",
            flight_number=flight_number,
            recommendation=recommendation,
        )

        # Format responsibility breakdown
        breakdown = root_cause_analysis.get("responsibility_breakdown", {})
        handler_minutes = root_cause_analysis.get("handler_responsible_minutes", 0)
        handler_percent = breakdown.get("handler", 0)

        airline_minutes = breakdown.get("airline", 0)
        airline_percent = breakdown.get("airline", 0)

        vendor_minutes = (
            breakdown.get("vendor_catering", 0)
            + breakdown.get("vendor_fuel", 0)
            + breakdown.get("vendor_other", 0)
        )
        vendor_percent = (
            breakdown.get("vendor_catering", 0)
            + breakdown.get("vendor_fuel", 0)
            + breakdown.get("vendor_other", 0)
        )

        other_minutes = (
            breakdown.get("airport_atc", 0) + breakdown.get("weather", 0) + breakdown.get("passengers", 0) + breakdown.get("other", 0)
        )
        other_percent = (
            breakdown.get("airport_atc", 0) + breakdown.get("weather", 0) + breakdown.get("passengers", 0) + breakdown.get("other", 0)
        )

        # Summarize evidence
        evidence_summary = await self._summarize_evidence(evidence_items)

        # Format IATA codes
        iata_codes_text = ", ".join(iata_codes) if iata_codes else "N/A"

        # Build prompt
        prompt = DISPUTE_RESPONSE_GENERATION_PROMPT.format(
            handler_name=handler_name,
            airline_name=airline_name,
            flight_number=flight_number,
            flight_date=flight_date.strftime("%d %B %Y"),
            origin=origin or "N/A",
            destination=destination or "N/A",
            penalty_amount=f"{penalty_amount:,.2f}",
            penalty_currency=penalty_currency,
            airline_claimed_reason=airline_claimed_reason,
            root_cause_analysis=root_cause_analysis.get("analysis_summary", ""),
            evidence_summary=evidence_summary,
            handler_minutes=handler_minutes,
            handler_percent=handler_percent,
            airline_minutes=airline_minutes,
            airline_percent=airline_percent,
            vendor_minutes=vendor_minutes,
            vendor_percent=vendor_percent,
            other_minutes=other_minutes,
            other_percent=other_percent,
            iata_codes=iata_codes_text,
            recommendation=recommendation,
        )

        try:
            result = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are a professional business writer drafting formal dispute letters.",
                max_tokens=4096,
                temperature=0.7,
            )

            response_text = result["content"]

            logger.info(
                "response_generation_success",
                flight_number=flight_number,
                response_length=len(response_text),
                tokens_used=result["usage"]["output_tokens"],
            )

            return {
                "response_text": response_text,
                "metadata": {
                    "model": result["model"],
                    "tokens_input": result["usage"]["input_tokens"],
                    "tokens_output": result["usage"]["output_tokens"],
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            logger.error("response_generation_failed", error=str(e), flight_number=flight_number)
            raise

    async def regenerate(
        self,
        original_response: str,
        user_feedback: str,
    ) -> Dict[str, Any]:
        """
        Regenerate response based on user feedback.

        Args:
            original_response: Original generated response
            user_feedback: User's feedback/requested changes

        Returns:
            Dict with updated response_text and metadata
        """
        logger.info("response_regeneration_start", feedback_length=len(user_feedback))

        prompt = RESPONSE_REGENERATION_PROMPT.format(
            original_response=original_response,
            user_feedback=user_feedback,
        )

        try:
            result = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are a professional business writer revising dispute letters based on feedback.",
                max_tokens=4096,
                temperature=0.7,
            )

            response_text = result["content"]

            logger.info(
                "response_regeneration_success",
                response_length=len(response_text),
            )

            return {
                "response_text": response_text,
                "metadata": {
                    "model": result["model"],
                    "tokens_input": result["usage"]["input_tokens"],
                    "tokens_output": result["usage"]["output_tokens"],
                    "regenerated_at": datetime.utcnow().isoformat(),
                    "user_feedback": user_feedback,
                },
            }

        except Exception as e:
            logger.error("response_regeneration_failed", error=str(e))
            raise

    async def _summarize_evidence(self, evidence_items: List[Dict[str, Any]]) -> str:
        """
        Summarize evidence items for inclusion in letter.

        Args:
            evidence_items: List of evidence

        Returns:
            Formatted evidence summary
        """
        if not evidence_items:
            return "No additional evidence available."

        # Format evidence list
        evidence_text = "\n".join([
            f"- [{ev.get('evidence_type', 'unknown')}] {ev.get('summary', '')}"
            for ev in evidence_items
        ])

        prompt = EVIDENCE_SUMMARIZATION_PROMPT.format(evidence_items=evidence_text)

        try:
            result = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are summarizing evidence for a formal dispute letter.",
                max_tokens=1000,
                temperature=0.5,
            )

            return result["content"]

        except Exception as e:
            logger.warning("evidence_summarization_failed", error=str(e))
            # Return simple formatted list as fallback
            return evidence_text
