"""
Ground handler API integration.

Integrates with ground handling companies' systems to fetch
turnaround activity data and resource assignments.
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime
import structlog

from config import settings

logger = structlog.get_logger()


class GroundHandlerAPI:
    """
    Integration with ground handler APIs.

    Fetches turnaround activities, crew assignments, and equipment status.
    """

    def __init__(self, handler_code: str = "TGS"):
        self.api_url = settings.handler_api_url
        self.api_key = settings.handler_api_key
        self.handler_code = handler_code

    async def get_turnaround_activities(
        self,
        flight_number: str,
        date: datetime
    ) -> List[Dict]:
        """
        Get turnaround activities for a flight.

        Args:
            flight_number: Flight number
            date: Flight date

        Returns:
            List of activity dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/turnarounds/{flight_number}",
                    params={
                        "date": date.strftime("%Y-%m-%d"),
                        "handler": self.handler_code
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()

                data = response.json()
                return data.get("activities", [])

        except httpx.HTTPError as e:
            logger.error(
                "handler_api_error",
                flight=flight_number,
                handler=self.handler_code,
                error=str(e)
            )
            return self._get_mock_activities(flight_number)

    async def get_crew_assignments(self, gate: str) -> List[Dict]:
        """
        Get crew assignments for a gate.

        Args:
            gate: Gate identifier

        Returns:
            List of crew assignment dictionaries
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/crews",
                    params={
                        "gate": gate,
                        "handler": self.handler_code
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("crews", [])

        except httpx.HTTPError as e:
            logger.error("crew_fetch_error", gate=gate, error=str(e))
            return []

    async def get_equipment_status(self) -> Dict[str, Dict]:
        """
        Get status of ground support equipment.

        Returns:
            Dictionary of equipment status by type
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/equipment",
                    params={"handler": self.handler_code},
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json().get("equipment", {})

        except httpx.HTTPError as e:
            logger.error("equipment_fetch_error", error=str(e))
            return {}

    async def update_activity_status(
        self,
        activity_id: str,
        status: str,
        progress: float
    ) -> bool:
        """
        Update the status of a turnaround activity.

        Args:
            activity_id: Activity identifier
            status: New status
            progress: Progress percentage (0-100)

        Returns:
            Success status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_url}/activities/{activity_id}",
                    json={
                        "status": status,
                        "progress": progress
                    },
                    headers={"X-API-Key": self.api_key},
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info("activity_updated", activity_id=activity_id, status=status)
                return True

        except httpx.HTTPError as e:
            logger.error("activity_update_error", activity_id=activity_id, error=str(e))
            return False

    def _get_mock_activities(self, flight_number: str) -> List[Dict]:
        """
        Generate mock turnaround activity data.

        Args:
            flight_number: Flight number

        Returns:
            List of mock activity dictionaries
        """
        now = datetime.utcnow()

        return [
            {
                "activity_type": "passenger_deboarding",
                "activity_name": "Passenger Deboarding",
                "status": "completed",
                "scheduled_duration": 15,
                "actual_duration": 12,
                "crew_count": 4,
                "service_provider": self.handler_code
            },
            {
                "activity_type": "cleaning",
                "activity_name": "Cabin Cleaning",
                "status": "in_progress",
                "scheduled_duration": 25,
                "progress": 60.0,
                "crew_count": 6,
                "service_provider": self.handler_code
            },
            {
                "activity_type": "refueling",
                "activity_name": "Aircraft Refueling",
                "status": "in_progress",
                "scheduled_duration": 20,
                "progress": 45.0,
                "crew_count": 2,
                "service_provider": "Turkish Petroleum"
            },
            {
                "activity_type": "catering",
                "activity_name": "Catering Service",
                "status": "pending",
                "scheduled_duration": 18,
                "crew_count": 3,
                "service_provider": "DO&CO"
            },
            {
                "activity_type": "passenger_boarding",
                "activity_name": "Passenger Boarding",
                "status": "pending",
                "scheduled_duration": 30,
                "crew_count": 5,
                "service_provider": self.handler_code
            }
        ]
