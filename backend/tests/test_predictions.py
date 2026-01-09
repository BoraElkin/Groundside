"""
Tests for prediction services.
"""
import pytest
from datetime import datetime

from services.prediction.delay_predictor import DelayPredictor
from services.prediction.turnaround_estimator import TurnaroundEstimator
from services.prediction.cascade_analyzer import CascadeAnalyzer


def test_delay_predictor_initialization():
    """Test delay predictor initialization."""
    predictor = DelayPredictor()
    assert predictor is not None
    assert predictor.model is not None


def test_delay_prediction():
    """Test basic delay prediction."""
    predictor = DelayPredictor()

    flight_data = {
        "flight_number": "TK001",
        "aircraft_type": "A321",
        "scheduled_time": datetime.utcnow(),
        "inbound_delay": 10,
        "passenger_count": 150
    }

    turnaround_data = {
        "gate_congestion_score": 0.5,
        "has_cargo": True
    }

    result = predictor.predict_delay(flight_data, turnaround_data)

    assert "predicted_delay_minutes" in result
    assert "confidence" in result
    assert "risk_level" in result
    assert result["predicted_delay_minutes"] >= 0
    assert 0 <= result["confidence"] <= 1
    assert result["risk_level"] in ["low", "medium", "high", "critical"]


def test_turnaround_estimator():
    """Test turnaround duration estimation."""
    estimator = TurnaroundEstimator()

    result = estimator.estimate_turnaround(
        aircraft_type="A321",
        flight_type="short",
        passenger_count=150,
        has_cargo=True,
        is_international=False
    )

    assert "estimated_duration_minutes" in result
    assert "baseline_duration_minutes" in result
    assert "activities" in result
    assert "critical_path_activities" in result
    assert result["estimated_duration_minutes"] > 0
    assert len(result["activities"]) > 0


def test_cascade_analyzer():
    """Test delay cascade analysis."""
    analyzer = CascadeAnalyzer()

    scheduled_departures = [
        {
            "flight_number": "TK002",
            "scheduled_time": datetime.utcnow(),
            "scheduled_arrival": datetime.utcnow()
        },
        {
            "flight_number": "TK003",
            "scheduled_time": datetime.utcnow(),
            "scheduled_arrival": datetime.utcnow()
        }
    ]

    result = analyzer.analyze_cascade(
        initial_delay=30,
        aircraft_registration="TC-ABC",
        scheduled_departures=scheduled_departures
    )

    assert "initial_delay_minutes" in result
    assert "affected_flights_count" in result
    assert "cascade_severity" in result
    assert "mitigation_recommendations" in result
    assert result["initial_delay_minutes"] == 30
