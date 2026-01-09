"""
Alert rules engine and triggering system.

Evaluates operational conditions and triggers alerts based on
configured rules and thresholds.
"""
from typing import Dict, List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class AlertEngine:
    """
    Rules-based alert triggering engine.

    Evaluates conditions and determines when to create alerts.
    """

    def __init__(self):
        self.rules = self._load_alert_rules()

    def _load_alert_rules(self) -> List[Dict]:
        """
        Load alert rules configuration.

        Returns:
            List of alert rule dictionaries
        """
        return [
            {
                "rule_id": "delay_prediction_high",
                "condition": "predicted_delay >= 30",
                "severity": "critical",
                "alert_type": "delay_prediction"
            },
            {
                "rule_id": "delay_prediction_medium",
                "condition": "predicted_delay >= 15",
                "severity": "warning",
                "alert_type": "delay_prediction"
            },
            {
                "rule_id": "turnaround_at_risk",
                "condition": "risk_score >= 0.7",
                "severity": "warning",
                "alert_type": "turnaround_at_risk"
            },
            {
                "rule_id": "cascade_detected",
                "condition": "affected_flights_count >= 3",
                "severity": "critical",
                "alert_type": "cascade_delay"
            },
            {
                "rule_id": "gate_conflict",
                "condition": "gate_overlap > 0",
                "severity": "critical",
                "alert_type": "gate_conflict"
            }
        ]

    def evaluate_delay_prediction(
        self,
        flight_data: Dict,
        prediction: Dict
    ) -> Optional[Dict]:
        """
        Evaluate if delay prediction should trigger an alert.

        Args:
            flight_data: Flight information
            prediction: Delay prediction results

        Returns:
            Alert data if conditions met, None otherwise
        """
        predicted_delay = prediction.get("predicted_delay_minutes", 0)
        confidence = prediction.get("confidence", 0)
        risk_level = prediction.get("risk_level", "low")

        # Only alert on high confidence predictions
        if confidence < 0.6:
            return None

        # Determine severity
        severity = None
        if predicted_delay >= 30:
            severity = "critical"
        elif predicted_delay >= 15:
            severity = "warning"
        elif predicted_delay >= 10 and risk_level in ["high", "critical"]:
            severity = "warning"

        if not severity:
            return None

        logger.info(
            "delay_alert_triggered",
            flight=flight_data.get("flight_number"),
            predicted_delay=predicted_delay,
            severity=severity
        )

        return {
            "alert_type": "delay_prediction",
            "severity": severity,
            "flight_id": flight_data.get("id"),
            "flight_number": flight_data.get("flight_number"),
            "predicted_delay_minutes": predicted_delay,
            "confidence_score": confidence,
            "title": f"Delay Predicted: {flight_data.get('flight_number')}",
            "message": f"Flight {flight_data.get('flight_number')} is predicted to experience a {predicted_delay} minute delay with {confidence*100:.0f}% confidence.",
            "triggered_at": datetime.utcnow()
        }

    def evaluate_turnaround_risk(
        self,
        turnaround: Dict
    ) -> Optional[Dict]:
        """
        Evaluate if turnaround risk should trigger an alert.

        Args:
            turnaround: Turnaround data

        Returns:
            Alert data if conditions met, None otherwise
        """
        risk_score = turnaround.get("risk_score", 0)
        status = turnaround.get("status")

        # Alert on high risk or at-risk status
        if risk_score < 0.7 and status != "at_risk":
            return None

        severity = "critical" if risk_score >= 0.8 else "warning"

        return {
            "alert_type": "turnaround_at_risk",
            "severity": severity,
            "turnaround_id": turnaround.get("turnaround_id"),
            "flight_number": turnaround.get("flight_number"),
            "gate": turnaround.get("gate"),
            "risk_score": risk_score,
            "title": f"Turnaround At Risk: {turnaround.get('flight_number')}",
            "message": f"Turnaround {turnaround.get('turnaround_id')} at gate {turnaround.get('gate')} is at risk with score {risk_score:.2f}.",
            "triggered_at": datetime.utcnow()
        }

    def evaluate_cascade(
        self,
        cascade_analysis: Dict
    ) -> Optional[Dict]:
        """
        Evaluate if delay cascade should trigger an alert.

        Args:
            cascade_analysis: Cascade analysis results

        Returns:
            Alert data if conditions met, None otherwise
        """
        affected_count = cascade_analysis.get("affected_flights_count", 0)
        severity_level = cascade_analysis.get("cascade_severity", "low")

        if affected_count < 2:
            return None

        severity = "critical" if affected_count >= 5 else "warning"

        return {
            "alert_type": "cascade_delay",
            "severity": severity,
            "affected_resource": f"{affected_count} flights",
            "impact_score": affected_count / 10.0,
            "title": f"Delay Cascade: {affected_count} Flights Affected",
            "message": f"Delay cascade affecting {affected_count} downstream flights detected.",
            "triggered_at": datetime.utcnow()
        }

    def evaluate_resource_shortage(
        self,
        resource_type: str,
        availability: float,
        demand: float
    ) -> Optional[Dict]:
        """
        Evaluate resource shortage conditions.

        Args:
            resource_type: Type of resource
            availability: Available units
            demand: Required units

        Returns:
            Alert data if shortage detected
        """
        shortage_pct = max(0, (demand - availability) / demand * 100)

        if shortage_pct < 20:
            return None

        severity = "critical" if shortage_pct >= 50 else "warning"

        return {
            "alert_type": "resource_shortage",
            "severity": severity,
            "affected_resource": resource_type,
            "title": f"{resource_type.title()} Shortage Alert",
            "message": f"{resource_type.title()} shortage: {shortage_pct:.0f}% under capacity.",
            "triggered_at": datetime.utcnow()
        }

    def should_suppress_alert(
        self,
        alert: Dict,
        recent_alerts: List[Dict],
        suppression_window_minutes: int = 30
    ) -> bool:
        """
        Determine if alert should be suppressed to avoid spam.

        Args:
            alert: New alert to check
            recent_alerts: Recent alerts
            suppression_window_minutes: Time window for suppression

        Returns:
            True if alert should be suppressed
        """
        cutoff_time = datetime.utcnow().timestamp() - (suppression_window_minutes * 60)

        for recent in recent_alerts:
            recent_time = recent.get("triggered_at")
            if isinstance(recent_time, datetime):
                recent_timestamp = recent_time.timestamp()
            else:
                continue

            # Check if same type and resource within window
            if (recent_timestamp > cutoff_time and
                recent.get("alert_type") == alert.get("alert_type") and
                recent.get("flight_number") == alert.get("flight_number")):
                return True

        return False
