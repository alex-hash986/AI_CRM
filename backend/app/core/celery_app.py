from celery import Celery

from app.core.config import get_settings

celery_app = Celery(
    "ai_sales_crm",
    broker=get_settings().redis_url,
    include=["app.tasks.ai_tasks"],
)
celery_app.conf.update(
    result_backend=get_settings().redis_url,
    accept_content=["json"],
    task_serializer="json",
    task_ignore_result=False,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
)
