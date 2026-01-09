"""
Tests for flight API endpoints.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_get_flights(client: AsyncClient):
    """Test getting list of flights."""
    response = await client.get("/api/v1/flights/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_flight(client: AsyncClient):
    """Test creating a new flight."""
    flight_data = {
        "flight_number": "TK001",
        "airline_code": "TK",
        "airline_name": "Turkish Airlines",
        "flight_type": "departure",
        "aircraft_type": "A321",
        "origin_airport": "IST",
        "destination_airport": "LHR",
        "scheduled_time": (datetime.utcnow() + timedelta(hours=2)).isoformat()
    }

    response = await client.post("/api/v1/flights/", json=flight_data)
    assert response.status_code == 201
    data = response.json()
    assert data["flight_number"] == "TK001"
    assert data["airline_code"] == "TK"


@pytest.mark.asyncio
async def test_get_flight_by_id(client: AsyncClient):
    """Test getting a specific flight by ID."""
    # First create a flight
    flight_data = {
        "flight_number": "TK002",
        "airline_code": "TK",
        "airline_name": "Turkish Airlines",
        "flight_type": "arrival",
        "aircraft_type": "B777",
        "origin_airport": "JFK",
        "destination_airport": "IST",
        "scheduled_time": datetime.utcnow().isoformat()
    }

    create_response = await client.post("/api/v1/flights/", json=flight_data)
    flight_id = create_response.json()["id"]

    # Now get it
    response = await client.get(f"/api/v1/flights/{flight_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == flight_id
    assert data["flight_number"] == "TK002"


@pytest.mark.asyncio
async def test_get_nonexistent_flight(client: AsyncClient):
    """Test getting a flight that doesn't exist."""
    response = await client.get("/api/v1/flights/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_flight(client: AsyncClient):
    """Test updating a flight."""
    # Create flight
    flight_data = {
        "flight_number": "TK003",
        "airline_code": "TK",
        "airline_name": "Turkish Airlines",
        "flight_type": "departure",
        "aircraft_type": "A321",
        "origin_airport": "IST",
        "destination_airport": "AYT",
        "scheduled_time": datetime.utcnow().isoformat()
    }

    create_response = await client.post("/api/v1/flights/", json=flight_data)
    flight_id = create_response.json()["id"]

    # Update it
    update_data = {
        "status": "delayed",
        "departure_delay": 15
    }

    response = await client.patch(f"/api/v1/flights/{flight_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "delayed"
    assert data["departure_delay"] == 15
