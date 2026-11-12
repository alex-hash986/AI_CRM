from typing import Annotated
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from kombu.exceptions import OperationalError
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.celery_app import celery_app
from app.core.database import get_async_db
from app.schemas.ai import EmailGenerateRequest, TaskStatusResponse
from app.schemas.common import EntityId
from app.services.deal_service import get_deal
from app.tasks.ai_tasks import generate_email_task, score_deal_task

router = APIRouter(tags=["ai"])
Database = Annotated[AsyncSession, Depends(get_async_db)]


@router.post("/deals/{deal_id}/score", status_code=status.HTTP_202_ACCEPTED)
async def queue_score(deal_id: EntityId, db: Database) -> TaskStatusResponse:
    await get_deal(db, deal_id)
    try:
        task = await run_in_threadpool(score_deal_task.delay, deal_id)
    except (OperationalError, RedisError) as exc:
        raise HTTPException(status_code=503, detail="Task queue unavailable") from exc
    return TaskStatusResponse(task_id=task.id, status="PENDING")


@router.post("/emails/generate", status_code=status.HTTP_202_ACCEPTED)
async def queue_email(data: EmailGenerateRequest, db: Database) -> TaskStatusResponse:
    await get_deal(db, data.deal_id)
    try:
        task = await run_in_threadpool(generate_email_task.delay, data.model_dump(mode="json"))
    except (OperationalError, RedisError) as exc:
        raise HTTPException(status_code=503, detail="Task queue unavailable") from exc
    return TaskStatusResponse(task_id=task.id, status="PENDING")


@router.get("/tasks/{task_id}")
def get_task_status(task_id: UUID) -> TaskStatusResponse:
    task = AsyncResult(str(task_id), app=celery_app)
    try:
        state = task.state
        if state == "SUCCESS":
            result = task.result
        elif state == "FAILURE":
            result = {"error": "AI task failed"}
        else:
            result = None
    except (OperationalError, RedisError) as exc:
        raise HTTPException(status_code=503, detail="Task result backend unavailable") from exc
    return TaskStatusResponse(task_id=str(task_id), status=state, result=result)
