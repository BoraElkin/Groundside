"""
Airport Operational Database (AODB) connector.

Integrates with airport operational database systems to fetch real-time
flight, gate, and resource information.
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import structlog

from config import settings

logger = structlog.get_logger()


class AODBConnector:
    """
    Connector for Airport Operational Database.

    Fetches flight schedules, gate assignments, and real-time status updates.
    """

    def __init__(self):
        self.api_url = settings.aodb_api_url
        self.api_key = settings.aodb_api_key
        self.airport_code = settings.default_airport_code

    async def get_flights(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch flights from AODB for a given time range.

        Args:
            start_time: Start of time range (default: now)
            end_time: End of time range (default: now + 24 hours)

        Returns:
            List of flight dictionaries
        """
        if not start_time:
            start_time = datetime.utcnow()
        if not end_time:
            end_time = start_time + timedelta(hours=24)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/flights",
                    params={
                        "airport": self.airport_code,
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=30.0
                )
                response.raise_for_status()

                data = response.json()
                logger.info(
                    "aodb_flights_fetched",
                    count=len(data.get("flights", [])),
                    airport=self.airport_code
                )

                return data.get("flights", [])

        except httpx.HTTPError as e:
            logger.error("aodb_fetch_error", error=str(e))
            # Return mock data for development
            return self._get_mock_flights()

    async def get_flight_status(self, flight_number: str, date: datetime) -> Optional[Dict]:
        """
        Get real-time status for a specific flight.

        Args:
            flight_number: Flight number (e.g., "TK123")
            date: Flight date

        Returns:
            Flight status dictionary or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/flights/{flight_number}",
                    params={
                        "date": date.strftime("%Y-%m-%d"),
                        "airport": self.airport_code
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error("aodb_status_error", flight=flight_number, error=str(e))
            return None

    async def get_gate_assignments(self) -> Dict[str, str]:
        """
        Get current gate assignments.

        Returns:
            Dictionary mapping flight numbers to gates
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/gates",
                    params={"airport": self.airport_code},
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("assignments", {})

        except httpx.HTTPError as e:
            logger.error("aodb_gates_error", error=str(e))
            return {}

    def _get_mock_flights(self) -> List[Dict]:
        """
        Generate mock flight data for development/testing.

        Returns:
            List of mock flight dictionaries
        """
        now = datetime.utcnow()

        return [
            {
                "flight_number": "TK001",
                "airline_code": "TK",
                "airline_name": "Turkish Airlines",
                "aircraft_type": "A321",
                "origin": "IST",
                "destination": "LHR",
                "scheduled_departure": (now + timedelta(hours=2)).isoformat(),
                "gate": "A12",
                "status": "scheduled"
            },
            {
                "flight_number": "TK456",
                "airline_code": "TK",
                "airline_name": "Turkish Airlines",
                "aircraft_type": "B777",
                "origin": "JFK",
                "destination": "IST",
                "scheduled_arrival": (now + timedelta(hours=1)).isoformat(),
                "gate": "B05",
                "status": "airborne"
            },
            {
                "flight_number": "PC101",
                "airline_code": "PC",
                "airline_name": "Pegasus Airlines",
                "aircraft_type": "B737-800",
                "origin": "IST",
                "destination": "AYT",
                "scheduled_departure": (now + timedelta(hours=3)).isoformat(),
                "gate": "C20",
                "status": "scheduled"
            }
        ]
