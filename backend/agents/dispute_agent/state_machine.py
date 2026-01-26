"""
State machine for dispute processing.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

from models.dispute import DisputeState

logger = structlog.get_logger()


class DisputeStateMachine:
    """
    Manages state transitions for dispute processing.
    """

    # Valid state transitions
    VALID_TRANSITIONS = {
        DisputeState.PENALTY_UPLOADED: [DisputeState.EXTRACTING_DETAILS, DisputeState.FAILED],
        DisputeState.EXTRACTING_DETAILS: [DisputeState.DETAILS_EXTRACTED, DisputeState.FAILED],
        DisputeState.DETAILS_EXTRACTED: [DisputeState.GATHERING_EVIDENCE, DisputeState.FAILED],
        DisputeState.GATHERING_EVIDENCE: [DisputeState.EVIDENCE_GATHERED, DisputeState.FAILED],
        DisputeState.EVIDENCE_GATHERED: [DisputeState.ANALYZING, DisputeState.FAILED],
        DisputeState.ANALYZING: [DisputeState.ANALYSIS_COMPLETE, DisputeState.FAILED],
        DisputeState.ANALYSIS_COMPLETE: [DisputeState.GENERATING_RESPONSE, DisputeState.FAILED],
        DisputeState.GENERATING_RESPONSE: [DisputeState.RESPONSE_GENERATED, DisputeState.FAILED],
        DisputeState.RESPONSE_GENERATED: [
            DisputeState.USER_REVIEWING,
            DisputeState.GENERATING_RESPONSE,  # Allow regeneration
            DisputeState.FAILED,
        ],
        DisputeState.USER_REVIEWING: [
            DisputeState.APPROVED,
            DisputeState.GENERATING_RESPONSE,  # Allow regeneration after review
            DisputeState.FAILED,
        ],
        DisputeState.APPROVED: [DisputeState.EXPORTED, DisputeState.FAILED],
        DisputeState.EXPORTED: [],  # Terminal state
        DisputeState.FAILED: [],  # Terminal state
    }

    # State progress percentages (for UI)
    STATE_PROGRESS = {
        DisputeState.PENALTY_UPLOADED: 10,
        DisputeState.EXTRACTING_DETAILS: 20,
        DisputeState.DETAILS_EXTRACTED: 30,
        DisputeState.GATHERING_EVIDENCE: 40,
        DisputeState.EVIDENCE_GATHERED: 50,
        DisputeState.ANALYZING: 60,
        DisputeState.ANALYSIS_COMPLETE: 70,
        DisputeState.GENERATING_RESPONSE: 80,
        DisputeState.RESPONSE_GENERATED: 90,
        DisputeState.USER_REVIEWING: 95,
        DisputeState.APPROVED: 98,
        DisputeState.EXPORTED: 100,
        DisputeState.FAILED: 0,
    }

    def __init__(self, dispute):
        """
        Initialize state machine with a dispute.

        Args:
            dispute: Dispute model instance
        """
        self.dispute = dispute

    def can_transition_to(self, new_state: DisputeState) -> bool:
        """
        Check if transition to new state is valid.

        Args:
            new_state: Target state

        Returns:
            True if transition is valid
        """
        current_state = self.dispute.state
        valid_next_states = self.VALID_TRANSITIONS.get(current_state, [])
        return new_state in valid_next_states

    def transition_to(
        self,
        new_state: DisputeState,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Transition to a new state.

        Args:
            new_state: Target state
            message: Optional message about the transition
            metadata: Optional metadata about the transition

        Returns:
            True if transition successful

        Raises:
            ValueError: If transition is not valid
        """
        if not self.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition from {self.dispute.state} to {new_state}"
            )

        old_state = self.dispute.state
        self.dispute.state = new_state

        # Update state history
        if self.dispute.state_history is None:
            self.dispute.state_history = []

        history_entry = {
            "from_state": old_state.value,
            "to_state": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "metadata": metadata or {},
        }

        self.dispute.state_history.append(history_entry)

        logger.info(
            "dispute_state_transition",
            dispute_id=self.dispute.id,
            from_state=old_state.value,
            to_state=new_state.value,
            message=message,
        )

        return True

    def get_progress_percentage(self) -> int:
        """Get current progress as percentage (0-100)."""
        return self.STATE_PROGRESS.get(self.dispute.state, 0)

    def get_current_step_description(self) -> str:
        """Get human-readable description of current step."""
        descriptions = {
            DisputeState.PENALTY_UPLOADED: "Penalty notice uploaded",
            DisputeState.EXTRACTING_DETAILS: "Extracting penalty details...",
            DisputeState.DETAILS_EXTRACTED: "Penalty details extracted",
            DisputeState.GATHERING_EVIDENCE: "Gathering evidence...",
            DisputeState.EVIDENCE_GATHERED: "Evidence gathered",
            DisputeState.ANALYZING: "Analyzing root cause...",
            DisputeState.ANALYSIS_COMPLETE: "Analysis complete",
            DisputeState.GENERATING_RESPONSE: "Generating dispute response...",
            DisputeState.RESPONSE_GENERATED: "Response generated",
            DisputeState.USER_REVIEWING: "Awaiting user review",
            DisputeState.APPROVED: "Approved by user",
            DisputeState.EXPORTED: "Exported and ready to send",
            DisputeState.FAILED: "Processing failed",
        }
        return descriptions.get(self.dispute.state, "Unknown state")

    def get_estimated_completion_seconds(self) -> Optional[int]:
        """
        Estimate seconds until completion.

        Returns:
            Estimated seconds or None if unknown
        """
        # Rough estimates based on typical processing times
        estimates = {
            DisputeState.PENALTY_UPLOADED: 120,
            DisputeState.EXTRACTING_DETAILS: 90,
            DisputeState.DETAILS_EXTRACTED: 80,
            DisputeState.GATHERING_EVIDENCE: 70,
            DisputeState.EVIDENCE_GATHERED: 60,
            DisputeState.ANALYZING: 45,
            DisputeState.ANALYSIS_COMPLETE: 30,
            DisputeState.GENERATING_RESPONSE: 15,
            DisputeState.RESPONSE_GENERATED: 0,
            DisputeState.USER_REVIEWING: 0,  # Waiting for user
            DisputeState.APPROVED: 5,
            DisputeState.EXPORTED: 0,
            DisputeState.FAILED: 0,
        }
        return estimates.get(self.dispute.state)

    def mark_failed(self, error_message: str):
        """
        Mark dispute as failed.

        Args:
            error_message: Error description
        """
        self.dispute.error_message = error_message
        try:
            self.transition_to(DisputeState.FAILED, message=error_message)
        except ValueError:
            # Already in a terminal state, just update error message
            logger.warning(
                "cannot_transition_to_failed",
                dispute_id=self.dispute.id,
                current_state=self.dispute.state.value,
            )

    def is_terminal_state(self) -> bool:
        """Check if current state is terminal."""
        return self.dispute.state in [DisputeState.EXPORTED, DisputeState.FAILED]

    def is_processing(self) -> bool:
        """Check if dispute is currently being processed."""
        processing_states = [
            DisputeState.EXTRACTING_DETAILS,
            DisputeState.GATHERING_EVIDENCE,
            DisputeState.ANALYZING,
            DisputeState.GENERATING_RESPONSE,
        ]
        return self.dispute.state in processing_states
