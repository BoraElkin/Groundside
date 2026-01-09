"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from config import settings

# Create Celery app
celery_app = Celery(
    "ground_ops",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "workers.ingestion_tasks",
        "workers.prediction_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    "ingest-flight-data": {
        "task": "workers.ingestion_tasks.ingest_flight_data",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    "update-turnaround-status": {
        "task": "workers.ingestion_tasks.update_turnaround_status",
        "schedule": crontab(minute="*/2"),  # Every 2 minutes
    },
    "run-delay-predictions": {
        "task": "workers.prediction_tasks.predict_delays",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "analyze-delay-cascades": {
        "task": "workers.prediction_tasks.analyze_cascades",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
