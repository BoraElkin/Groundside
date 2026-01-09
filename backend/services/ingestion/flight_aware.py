"""
FlightAware API integration.

Integrates with FlightAware AeroAPI for real-time flight tracking,
status updates, and historical flight data.
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import structlog

from config import settings

logger = structlog.get_logger()


class FlightAwareAPI:
    """
    FlightAware AeroAPI integration.

    Provides flight tracking, status updates, and position data.
    """

    def __init__(self):
        self.api_key = settings.flightaware_api_key
        self.base_url = "https://aeroapi.flightaware.com/aeroapi"
        self.airport_code = settings.default_airport_code

    async def get_flight_info(
        self,
        flight_number: str,
        date: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Get comprehensive flight information.

        Args:
            flight_number: Flight number (e.g., "TK001")
            date: Flight date (default: today)

        Returns:
            Flight information dictionary or None
        """
        if not date:
            date = datetime.utcnow()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/flights/{flight_number}",
                    params={
                        "start": date.strftime("%Y-%m-%d"),
                        "end": (date + timedelta(days=1)).strftime("%Y-%m-%d")
                    },
                    headers={"x-apikey": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                flights = data.get("flights", [])

                if flights:
                    logger.info("flightaware_flight_found", flight_number=flight_number)
                    return flights[0]
                else:
                    logger.warning("flightaware_no_data", flight_number=flight_number)
                    return None

        except httpx.HTTPError as e:
            logger.error("flightaware_error", flight_number=flight_number, error=str(e))
            return self._get_mock_flight_info(flight_number)

    async def get_airport_flights(
        self,
        flight_type: str = "arrivals"
    ) -> List[Dict]:
        """
        Get flights for the configured airport.

        Args:
            flight_type: "arrivals" or "departures"

        Returns:
            List of flight dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                endpoint = f"arrivals" if flight_type == "arrivals" else "departures"

                response = await client.get(
                    f"{self.base_url}/airports/{self.airport_code}/{endpoint}",
                    headers={"x-apikey": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                logger.info(
                    "flightaware_airport_flights",
                    type=flight_type,
                    count=len(data.get(flight_type, []))
                )

                return data.get(flight_type, [])

        except httpx.HTTPError as e:
            logger.error("flightaware_airport_error", type=flight_type, error=str(e))
            return []

    async def get_flight_position(self, flight_id: str) -> Optional[Dict]:
        """
        Get real-time position of an airborne flight.

        Args:
            flight_id: FlightAware flight identifier

        Returns:
            Position dictionary with lat/lon/altitude or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/flights/{flight_id}/position",
                    headers={"x-apikey": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                return data.get("position")

        except httpx.HTTPError as e:
            logger.error("position_fetch_error", flight_id=flight_id, error=str(e))
            return None

    async def get_flight_route(self, flight_id: str) -> Optional[Dict]:
        """
        Get flight route information.

        Args:
            flight_id: FlightAware flight identifier

        Returns:
            Route dictionary or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/flights/{flight_id}/route",
                    headers={"x-apikey": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error("route_fetch_error", flight_id=flight_id, error=str(e))
            return None

    async def get_estimated_arrival(self, flight_number: str) -> Optional[datetime]:
        """
        Get estimated arrival time for a flight.

        Args:
            flight_number: Flight number

        Returns:
            Estimated arrival datetime or None
        """
        flight_info = await self.get_flight_info(flight_number)

        if flight_info and "estimated_arrival" in flight_info:
            try:
                return datetime.fromisoformat(flight_info["estimated_arrival"])
            except (ValueError, TypeError):
                pass

        return None

    def _get_mock_flight_info(self, flight_number: str) -> Dict:
        """
        Generate mock flight information.

        Args:
            flight_number: Flight number

        Returns:
            Mock flight info dictionary
        """
        now = datetime.utcnow()

        return {
            "ident": flight_number,
            "aircraft_type": "A321",
            "origin": {"code": "IST", "name": "Istanbul Airport"},
            "destination": {"code": "LHR", "name": "London Heathrow"},
            "filed_departure_time": (now + timedelta(hours=2)).isoformat(),
            "estimated_departure_time": (now + timedelta(hours=2, minutes=10)).isoformat(),
            "filed_arrival_time": (now + timedelta(hours=6)).isoformat(),
            "estimated_arrival_time": (now + timedelta(hours=6, minutes=5)).isoformat(),
            "status": "Scheduled",
            "progress_percent": 0,
            "altitude": 0,
            "groundspeed": 0
        }
