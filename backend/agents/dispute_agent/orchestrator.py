"""
Dispute orchestrator - main controller for dispute resolution workflow.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.dispute import Dispute, Evidence, DisputeTurnaroundActivity, DisputeState, DisputeRecommendation
from agents.dispute_agent.state_machine import DisputeStateMachine
from agents.dispute_agent.penalty_extractor import PenaltyExtractor
from agents.dispute_agent.root_cause_analyzer import RootCauseAnalyzer
from agents.dispute_agent.response_generator import ResponseGenerator
from agents.shared.llm_client import LLMFactory
from agents.shared.base_llm_client import BaseLLMClient

logger = structlog.get_logger()


class DisputeOrchestrator:
    """
    Orchestrates the complete dispute resolution workflow using configured LLM provider.
    """

    def __init__(self, db: AsyncSession, llm_client: Optional[BaseLLMClient] = None):
        """
        Initialize orchestrator.

        Args:
            db: Database session
            llm_client: Shared LLM client (creates default from factory if not provided)
        """
        self.db = db
        self.llm_client = llm_client or LLMFactory.create_default()

        # Initialize agent components with shared LLM client
        self.penalty_extractor = PenaltyExtractor(self.llm_client)
        self.root_cause_analyzer = RootCauseAnalyzer(self.llm_client)
        self.response_generator = ResponseGenerator(self.llm_client)

    async def create_dispute_from_text(
        self,
        document_text: str,
        customer_id: Optional[str] = None,
    ) -> Dispute:
        """
        Create dispute from penalty notice text.

        Args:
            document_text: Text content of penalty notice
            customer_id: Customer ID (optional)

        Returns:
            Created dispute
        """
        logger.info("create_dispute_from_text_start", text_length=len(document_text))

        # Create dispute record
        dispute = Dispute(
            id=f"disp_{secrets.token_urlsafe(16)}",
            customer_id=customer_id,
            state=DisputeState.PENALTY_UPLOADED,
            state_history=[],
        )

        self.db.add(dispute)
        await self.db.commit()
        await self.db.refresh(dispute)

        # Start state machine
        state_machine = DisputeStateMachine(dispute)

        try:
            # Extract penalty details
            state_machine.transition_to(DisputeState.EXTRACTING_DETAILS)
            await self.db.commit()

            extracted = await self.penalty_extractor.extract_from_text(document_text)

            # Update dispute with extracted data
            dispute.flight_number = extracted.get("flight_number")
            dispute.flight_date = extracted.get("flight_date")
            dispute.origin = extracted.get("origin")
            dispute.destination = extracted.get("destination")
            dispute.claimed_delay_minutes = extracted.get("claimed_delay_minutes")
            dispute.penalty_amount = extracted.get("penalty_amount")
            dispute.penalty_currency = extracted.get("penalty_currency", "USD")
            dispute.airline_claimed_reason = extracted.get("airline_claimed_reason")
            dispute.airline_specific_claims = extracted.get("airline_specific_claims", [])

            # Extract airline code from flight number
            if dispute.flight_number:
                dispute.airline_code = "".join([c for c in dispute.flight_number if c.isalpha()])

            state_machine.transition_to(DisputeState.DETAILS_EXTRACTED, message="Penalty details extracted successfully")
            await self.db.commit()

            logger.info(
                "dispute_created_from_text",
                dispute_id=dispute.id,
                flight_number=dispute.flight_number,
            )

            return dispute

        except Exception as e:
            logger.error("create_dispute_from_text_failed", error=str(e))
            state_machine.mark_failed(f"Failed to extract penalty details: {str(e)}")
            await self.db.commit()
            raise

    async def create_dispute_manual(
        self,
        flight_number: str,
        flight_date: datetime,
        claimed_delay_minutes: int,
        penalty_amount: float,
        penalty_currency: str = "USD",
        airline_claimed_reason: Optional[str] = None,
        customer_id: Optional[str] = None,
        **kwargs,
    ) -> Dispute:
        """
        Create dispute from manual entry.

        Args:
            flight_number: Flight number
            flight_date: Flight date
            claimed_delay_minutes: Claimed delay
            penalty_amount: Penalty amount
            penalty_currency: Currency
            airline_claimed_reason: Airline's reason
            customer_id: Customer ID
            **kwargs: Additional fields

        Returns:
            Created dispute
        """
        logger.info("create_dispute_manual", flight_number=flight_number)

        # Extract airline code
        airline_code = "".join([c for c in flight_number if c.isalpha()])

        dispute = Dispute(
            id=f"disp_{secrets.token_urlsafe(16)}",
            customer_id=customer_id,
            state=DisputeState.DETAILS_EXTRACTED,
            flight_number=flight_number,
            flight_date=flight_date,
            airline_code=airline_code,
            claimed_delay_minutes=claimed_delay_minutes,
            penalty_amount=penalty_amount,
            penalty_currency=penalty_currency,
            airline_claimed_reason=airline_claimed_reason,
            **kwargs,
        )

        self.db.add(dispute)
        await self.db.commit()
        await self.db.refresh(dispute)

        logger.info("dispute_created_manual", dispute_id=dispute.id)

        return dispute

    async def add_activities(
        self,
        dispute_id: str,
        activities: List[Dict[str, Any]],
    ) -> None:
        """
        Add turnaround activities to dispute.

        Args:
            dispute_id: Dispute ID
            activities: List of activity dicts
        """
        logger.info("add_activities_start", dispute_id=dispute_id, count=len(activities))

        result = await self.db.execute(select(Dispute).where(Dispute.id == dispute_id))
        dispute = result.scalar_one_or_none()

        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        state_machine = DisputeStateMachine(dispute)

        try:
            state_machine.transition_to(DisputeState.GATHERING_EVIDENCE)
            await self.db.commit()

            for act_data in activities:
                activity = DisputeTurnaroundActivity(
                    id=f"act_{secrets.token_urlsafe(12)}",
                    dispute_id=dispute_id,
                    activity_type=act_data.get("activity_type"),
                    performed_by=act_data.get("performed_by"),
                    scheduled_start=act_data.get("scheduled_start"),
                    actual_start=act_data.get("actual_start"),
                    scheduled_end=act_data.get("scheduled_end"),
                    actual_end=act_data.get("actual_end"),
                    notes=act_data.get("notes"),
                )

                # Calculate durations
                if activity.actual_start and activity.actual_end:
                    duration = (activity.actual_end - activity.actual_start).total_seconds() / 60
                    activity.actual_duration_minutes = int(duration)

                if activity.scheduled_start and activity.scheduled_end:
                    duration = (activity.scheduled_end - activity.scheduled_start).total_seconds() / 60
                    activity.scheduled_duration_minutes = int(duration)

                self.db.add(activity)

            state_machine.transition_to(DisputeState.EVIDENCE_GATHERED)
            await self.db.commit()

            logger.info("activities_added", dispute_id=dispute_id, count=len(activities))

        except Exception as e:
            logger.error("add_activities_failed", error=str(e), dispute_id=dispute_id)
            state_machine.mark_failed(f"Failed to add activities: {str(e)}")
            await self.db.commit()
            raise

    async def analyze_and_generate(
        self,
        dispute_id: str,
        handler_name: str = "Ground Handler",
    ) -> Dispute:
        """
        Analyze root cause and generate dispute response.

        Args:
            dispute_id: Dispute ID
            handler_name: Handler name for letter

        Returns:
            Updated dispute
        """
        logger.info("analyze_and_generate_start", dispute_id=dispute_id)

        result = await self.db.execute(
            select(Dispute).where(Dispute.id == dispute_id)
        )
        dispute = result.scalar_one_or_none()

        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        state_machine = DisputeStateMachine(dispute)

        try:
            # Get activities
            activities_result = await self.db.execute(
                select(DisputeTurnaroundActivity).where(
                    DisputeTurnaroundActivity.dispute_id == dispute_id
                )
            )
            activities = activities_result.scalars().all()

            # Get evidence
            evidence_result = await self.db.execute(
                select(Evidence).where(Evidence.dispute_id == dispute_id)
            )
            evidence_items = evidence_result.scalars().all()

            # Analyze root cause
            state_machine.transition_to(DisputeState.ANALYZING)
            await self.db.commit()

            analysis = await self.root_cause_analyzer.analyze(
                flight_number=dispute.flight_number,
                flight_date=dispute.flight_date,
                claimed_delay_minutes=dispute.claimed_delay_minutes,
                airline_claimed_reason=dispute.airline_claimed_reason or "",
                scheduled_arrival=dispute.scheduled_arrival,
                actual_arrival=dispute.actual_arrival,
                scheduled_departure=dispute.scheduled_departure,
                actual_departure=dispute.actual_departure,
                activities=[
                    {
                        "activity_type": a.activity_type,
                        "performed_by": a.performed_by.value,
                        "scheduled_start": a.scheduled_start,
                        "actual_start": a.actual_start,
                        "actual_end": a.actual_end,
                        "notes": a.notes,
                    }
                    for a in activities
                ],
                evidence_items=[
                    {
                        "evidence_type": e.evidence_type.value,
                        "summary": e.summary,
                        "timestamp": e.timestamp,
                    }
                    for e in evidence_items
                ],
                aircraft_type=dispute.aircraft_type,
            )

            # Update dispute with analysis
            dispute.actual_delay_minutes = analysis.get("actual_delay_minutes")
            dispute.handler_responsible_minutes = analysis.get("handler_responsible_minutes")
            dispute.root_cause_analysis = analysis.get("analysis_summary")
            dispute.responsibility_breakdown = analysis.get("responsibility_breakdown")
            dispute.iata_delay_codes = analysis.get("iata_delay_codes", [])
            dispute.confidence_score = analysis.get("confidence")

            # Set recommendation
            recommendation_str = analysis.get("recommendation", "unknown")
            dispute.recommendation = DisputeRecommendation(recommendation_str)

            state_machine.transition_to(DisputeState.ANALYSIS_COMPLETE)
            await self.db.commit()

            # Generate response
            state_machine.transition_to(DisputeState.GENERATING_RESPONSE)
            await self.db.commit()

            airline_name = f"{dispute.airline_code} Airlines" if dispute.airline_code else "Airline"

            response_result = await self.response_generator.generate(
                handler_name=handler_name,
                airline_name=airline_name,
                flight_number=dispute.flight_number,
                flight_date=dispute.flight_date,
                origin=dispute.origin,
                destination=dispute.destination,
                penalty_amount=dispute.penalty_amount,
                penalty_currency=dispute.penalty_currency,
                airline_claimed_reason=dispute.airline_claimed_reason or "",
                root_cause_analysis=analysis,
                evidence_items=[
                    {
                        "evidence_type": e.evidence_type.value,
                        "summary": e.summary,
                        "timestamp": e.timestamp,
                    }
                    for e in evidence_items
                ],
                iata_codes=dispute.iata_delay_codes,
                recommendation=recommendation_str,
            )

            dispute.dispute_response_text = response_result["response_text"]
            dispute.generation_metadata = response_result["metadata"]

            state_machine.transition_to(DisputeState.RESPONSE_GENERATED)
            await self.db.commit()

            logger.info(
                "analyze_and_generate_success",
                dispute_id=dispute_id,
                recommendation=dispute.recommendation.value,
            )

            return dispute

        except Exception as e:
            logger.error("analyze_and_generate_failed", error=str(e), dispute_id=dispute_id)
            state_machine.mark_failed(f"Analysis/generation failed: {str(e)}")
            await self.db.commit()
            raise

    async def regenerate_response(
        self,
        dispute_id: str,
        user_feedback: str,
    ) -> Dispute:
        """
        Regenerate response based on user feedback.

        Args:
            dispute_id: Dispute ID
            user_feedback: User's requested changes

        Returns:
            Updated dispute
        """
        logger.info("regenerate_response_start", dispute_id=dispute_id)

        result = await self.db.execute(select(Dispute).where(Dispute.id == dispute_id))
        dispute = result.scalar_one_or_none()

        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        if not dispute.dispute_response_text:
            raise ValueError("No original response to regenerate")

        state_machine = DisputeStateMachine(dispute)

        try:
            state_machine.transition_to(DisputeState.GENERATING_RESPONSE, message="Regenerating based on feedback")
            await self.db.commit()

            response_result = await self.response_generator.regenerate(
                original_response=dispute.dispute_response_text,
                user_feedback=user_feedback,
            )

            dispute.dispute_response_text = response_result["response_text"]
            dispute.generation_metadata = response_result["metadata"]

            state_machine.transition_to(DisputeState.RESPONSE_GENERATED, message="Response regenerated")
            await self.db.commit()

            logger.info("regenerate_response_success", dispute_id=dispute_id)

            return dispute

        except Exception as e:
            logger.error("regenerate_response_failed", error=str(e), dispute_id=dispute_id)
            raise
