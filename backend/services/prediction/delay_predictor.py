"""
ML-based delay prediction service.

Predicts aircraft turnaround delays using machine learning models
trained on historical operational data.
"""
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import structlog
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os

from config import settings

logger = structlog.get_logger()


class DelayPredictor:
    """
    Delay prediction service using scikit-learn.

    Predicts turnaround delays based on multiple operational factors.
    """

    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            "hour_of_day",
            "day_of_week",
            "aircraft_size_code",
            "inbound_delay_minutes",
            "gate_congestion_score",
            "weather_score",
            "passenger_count",
            "turnaround_complexity"
        ]
        self._initialize_model()

    def _initialize_model(self):
        """
        Initialize or load the ML model.

        If a trained model exists, load it. Otherwise, create a new model.
        """
        model_path = "ml/models/delay_predictor.joblib"

        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                logger.info("delay_model_loaded", path=model_path)
            except Exception as e:
                logger.error("model_load_error", error=str(e))
                self._create_default_model()
        else:
            self._create_default_model()

    def _create_default_model(self):
        """Create a default Random Forest model."""
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        logger.info("default_model_created")

    def predict_delay(
        self,
        flight_data: Dict,
        turnaround_data: Dict
    ) -> Dict[str, float]:
        """
        Predict turnaround delay for a flight.

        Args:
            flight_data: Flight information dictionary
            turnaround_data: Turnaround context dictionary

        Returns:
            Dictionary with prediction, confidence, and risk level
        """
        # Extract features
        features = self._extract_features(flight_data, turnaround_data)

        # If model is not trained, use rule-based estimation
        if not hasattr(self.model, 'estimators_'):
            return self._rule_based_prediction(features)

        # Prepare features for prediction
        X = np.array([list(features.values())])

        try:
            # Make prediction
            predicted_delay = self.model.predict(X)[0]

            # Get prediction confidence from tree variance
            predictions = np.array([tree.predict(X)[0] for tree in self.model.estimators_])
            std_dev = np.std(predictions)
            confidence = max(0.0, min(1.0, 1.0 - (std_dev / 30.0)))  # Normalize to 0-1

            # Determine risk level
            risk_level = self._calculate_risk_level(predicted_delay, confidence)

            logger.info(
                "delay_predicted",
                flight=flight_data.get("flight_number"),
                predicted_delay=round(predicted_delay, 2),
                confidence=round(confidence, 2),
                risk=risk_level
            )

            return {
                "predicted_delay_minutes": max(0, round(predicted_delay, 2)),
                "confidence": round(confidence, 2),
                "risk_level": risk_level,
                "prediction_interval_lower": max(0, round(predicted_delay - std_dev, 2)),
                "prediction_interval_upper": round(predicted_delay + std_dev, 2)
            }

        except Exception as e:
            logger.error("prediction_error", error=str(e))
            return self._rule_based_prediction(features)

    def _extract_features(
        self,
        flight_data: Dict,
        turnaround_data: Dict
    ) -> Dict[str, float]:
        """
        Extract features from flight and turnaround data.

        Args:
            flight_data: Flight information
            turnaround_data: Turnaround context

        Returns:
            Dictionary of feature values
        """
        # Time-based features
        scheduled_time = flight_data.get("scheduled_time", datetime.utcnow())
        if isinstance(scheduled_time, str):
            scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

        hour_of_day = scheduled_time.hour
        day_of_week = scheduled_time.weekday()

        # Aircraft size encoding
        aircraft_type = flight_data.get("aircraft_type", "A321")
        aircraft_size_code = self._encode_aircraft_size(aircraft_type)

        # Delay propagation
        inbound_delay = flight_data.get("inbound_delay", 0)

        # Operational context
        gate_congestion = turnaround_data.get("gate_congestion_score", 0.3)
        weather_score = flight_data.get("weather_score", 0.1)
        passenger_count = flight_data.get("passenger_count", 150)

        # Turnaround complexity
        turnaround_complexity = self._calculate_turnaround_complexity(
            aircraft_type,
            passenger_count,
            flight_data.get("has_cargo", False)
        )

        return {
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "aircraft_size_code": aircraft_size_code,
            "inbound_delay_minutes": inbound_delay,
            "gate_congestion_score": gate_congestion,
            "weather_score": weather_score,
            "passenger_count": passenger_count,
            "turnaround_complexity": turnaround_complexity
        }

    def _encode_aircraft_size(self, aircraft_type: str) -> int:
        """
        Encode aircraft type to size code.

        Args:
            aircraft_type: Aircraft type (e.g., "A321", "B777")

        Returns:
            Size code (1=small, 2=medium, 3=large, 4=wide-body)
        """
        wide_body = ["A330", "A340", "A350", "A380", "B777", "B787", "B747"]
        large_narrow = ["A321", "B757"]
        medium = ["A320", "B737", "B738"]

        if aircraft_type in wide_body:
            return 4
        elif aircraft_type in large_narrow:
            return 3
        elif aircraft_type in medium:
            return 2
        else:
            return 1

    def _calculate_turnaround_complexity(
        self,
        aircraft_type: str,
        passenger_count: int,
        has_cargo: bool
    ) -> float:
        """
        Calculate turnaround complexity score.

        Args:
            aircraft_type: Aircraft type
            passenger_count: Number of passengers
            has_cargo: Whether flight has cargo

        Returns:
            Complexity score (0-10)
        """
        complexity = 0.0

        # Aircraft size factor
        size_code = self._encode_aircraft_size(aircraft_type)
        complexity += size_code * 1.5

        # Passenger load factor
        complexity += (passenger_count / 50) * 1.0

        # Cargo factor
        if has_cargo:
            complexity += 2.0

        return min(10.0, complexity)

    def _calculate_risk_level(self, predicted_delay: float, confidence: float) -> str:
        """
        Calculate risk level based on prediction.

        Args:
            predicted_delay: Predicted delay in minutes
            confidence: Prediction confidence (0-1)

        Returns:
            Risk level string
        """
        if predicted_delay < 5:
            return "low"
        elif predicted_delay < 15:
            return "medium" if confidence > 0.7 else "low"
        elif predicted_delay < 30:
            return "high" if confidence > 0.6 else "medium"
        else:
            return "critical"

    def _rule_based_prediction(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Fallback rule-based prediction when ML model is not available.

        Args:
            features: Feature dictionary

        Returns:
            Prediction dictionary
        """
        # Simple rule-based estimation
        delay = 0.0

        # Inbound delay propagation (70% carries over)
        delay += features["inbound_delay_minutes"] * 0.7

        # Gate congestion impact
        delay += features["gate_congestion_score"] * 15

        # Weather impact
        delay += features["weather_score"] * 20

        # Complexity impact
        delay += features["turnaround_complexity"] * 1.5

        # Peak hour penalty
        if 6 <= features["hour_of_day"] <= 9 or 17 <= features["hour_of_day"] <= 20:
            delay += 5

        risk_level = self._calculate_risk_level(delay, 0.6)

        return {
            "predicted_delay_minutes": max(0, round(delay, 2)),
            "confidence": 0.6,
            "risk_level": risk_level,
            "prediction_interval_lower": max(0, round(delay * 0.7, 2)),
            "prediction_interval_upper": round(delay * 1.3, 2)
        }

    def get_contributing_factors(self, features: Dict[str, float]) -> List[str]:
        """
        Identify main contributing factors to delay prediction.

        Args:
            features: Feature dictionary

        Returns:
            List of contributing factor descriptions
        """
        factors = []

        if features["inbound_delay_minutes"] > 15:
            factors.append(f"Inbound delay of {features['inbound_delay_minutes']} minutes")

        if features["gate_congestion_score"] > 0.6:
            factors.append("High gate congestion")

        if features["weather_score"] > 0.5:
            factors.append("Adverse weather conditions")

        if features["turnaround_complexity"] > 7:
            factors.append("Complex turnaround requirements")

        if 6 <= features["hour_of_day"] <= 9:
            factors.append("Morning peak hour operations")
        elif 17 <= features["hour_of_day"] <= 20:
            factors.append("Evening peak hour operations")

        return factors if factors else ["Normal operational conditions"]
