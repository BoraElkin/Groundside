"""
Celery tasks for data ingestion.
"""
from celery import shared_task
import structlog
from datetime import datetime, timedelta

from workers.celery_app import celery_app
from services.ingestion.aodb_connector import AODBConnector
from services.ingestion.handler_api import GroundHandlerAPI

logger = structlog.get_logger()


@celery_app.task(name="workers.ingestion_tasks.ingest_flight_data")
def ingest_flight_data():
    """
    Periodic task to ingest flight data from AODB.

    Runs every 5 minutes to fetch latest flight schedules and updates.
    """
    try:
        logger.info("ingestion_task_started", task="flight_data")

        connector = AODBConnector()

        # Fetch flights for next 24 hours
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=24)

        # This would be async in production
        # For now, we'll just log
        logger.info(
            "flight_ingestion_completed",
            start=start_time.isoformat(),
            end=end_time.isoformat()
        )

        return {"status": "success", "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error("ingestion_task_error", task="flight_data", error=str(e))
        raise


@celery_app.task(name="workers.ingestion_tasks.update_turnaround_status")
def update_turnaround_status():
    """
    Periodic task to update turnaround activity status.

    Runs every 2 minutes to fetch latest activity updates from ground handlers.
    """
    try:
        logger.info("ingestion_task_started", task="turnaround_status")

        handler_api = GroundHandlerAPI()

        # In production, this would query active turnarounds and update them
        logger.info("turnaround_status_updated")

        return {"status": "success", "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error("ingestion_task_error", task="turnaround_status", error=str(e))
        raise
