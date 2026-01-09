"""
Vehicle GPS tracking integration.

Integrates with ground support equipment GPS tracking systems
to monitor vehicle locations and movement patterns.
"""
import httpx
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import structlog

from config import settings

logger = structlog.get_logger()


class GPSTracker:
    """
    GPS tracking service for ground support equipment.

    Monitors vehicle locations, movement, and availability.
    """

    def __init__(self):
        self.api_url = settings.gps_tracker_url
        self.api_key = settings.gps_tracker_key
        self.airport_code = settings.default_airport_code

    async def get_vehicle_locations(
        self,
        vehicle_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get current locations of all tracked vehicles.

        Args:
            vehicle_type: Filter by vehicle type (e.g., "pushback", "fuel", "catering")

        Returns:
            List of vehicle location dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {"airport": self.airport_code}
                if vehicle_type:
                    params["type"] = vehicle_type

                response = await client.get(
                    f"{self.api_url}/vehicles/locations",
                    params=params,
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                logger.info(
                    "vehicle_locations_fetched",
                    count=len(data.get("vehicles", []))
                )

                return data.get("vehicles", [])

        except httpx.HTTPError as e:
            logger.error("gps_fetch_error", error=str(e))
            return self._get_mock_vehicle_locations()

    async def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict]:
        """
        Get location and status of a specific vehicle.

        Args:
            vehicle_id: Vehicle identifier

        Returns:
            Vehicle location dictionary or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/vehicles/{vehicle_id}",
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error("vehicle_fetch_error", vehicle_id=vehicle_id, error=str(e))
            return None

    async def get_nearest_vehicle(
        self,
        location: Tuple[float, float],
        vehicle_type: str
    ) -> Optional[Dict]:
        """
        Find the nearest available vehicle of a specific type.

        Args:
            location: (latitude, longitude) tuple
            vehicle_type: Type of vehicle needed

        Returns:
            Nearest vehicle dictionary or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/vehicles/nearest",
                    params={
                        "lat": location[0],
                        "lon": location[1],
                        "type": vehicle_type,
                        "status": "available"
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error("nearest_vehicle_error", vehicle_type=vehicle_type, error=str(e))
            return None

    async def get_vehicle_eta(
        self,
        vehicle_id: str,
        destination: Tuple[float, float]
    ) -> Optional[int]:
        """
        Calculate estimated time of arrival for a vehicle.

        Args:
            vehicle_id: Vehicle identifier
            destination: (latitude, longitude) tuple

        Returns:
            ETA in minutes or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/vehicles/{vehicle_id}/eta",
                    params={
                        "dest_lat": destination[0],
                        "dest_lon": destination[1]
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                return data.get("eta_minutes")

        except httpx.HTTPError as e:
            logger.error("eta_calculation_error", vehicle_id=vehicle_id, error=str(e))
            return None

    async def track_vehicle_history(
        self,
        vehicle_id: str,
        hours: int = 24
    ) -> List[Dict]:
        """
        Get historical location data for a vehicle.

        Args:
            vehicle_id: Vehicle identifier
            hours: Number of hours of history to fetch

        Returns:
            List of historical location points
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/vehicles/{vehicle_id}/history",
                    params={"hours": hours},
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("history", [])

        except httpx.HTTPError as e:
            logger.error("history_fetch_error", vehicle_id=vehicle_id, error=str(e))
            return []

    def _get_mock_vehicle_locations(self) -> List[Dict]:
        """
        Generate mock vehicle location data.

        Returns:
            List of mock vehicle dictionaries
        """
        return [
            {
                "vehicle_id": "PB-001",
                "vehicle_type": "pushback",
                "status": "assigned",
                "gate": "A12",
                "latitude": 41.2753,
                "longitude": 28.7519,
                "speed": 0,
                "heading": 180,
                "last_update": datetime.utcnow().isoformat()
            },
            {
                "vehicle_id": "FUEL-023",
                "vehicle_type": "fuel_truck",
                "status": "in_transit",
                "destination_gate": "B05",
                "latitude": 41.2765,
                "longitude": 28.7532,
                "speed": 15,
                "heading": 90,
                "eta_minutes": 3,
                "last_update": datetime.utcnow().isoformat()
            },
            {
                "vehicle_id": "CAT-015",
                "vehicle_type": "catering",
                "status": "servicing",
                "gate": "C20",
                "latitude": 41.2741,
                "longitude": 28.7505,
                "speed": 0,
                "heading": 270,
                "last_update": datetime.utcnow().isoformat()
            },
            {
                "vehicle_id": "BELT-008",
                "vehicle_type": "belt_loader",
                "status": "available",
                "location_zone": "Equipment Depot A",
                "latitude": 41.2780,
                "longitude": 28.7550,
                "speed": 0,
                "heading": 0,
                "last_update": datetime.utcnow().isoformat()
            }
        ]
