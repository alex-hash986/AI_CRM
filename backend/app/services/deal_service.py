import logging
from datetime import datetime, timezone

from fastapi import HTTPException
from kombu.exceptions import OperationalError
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models import Client, CommunicationLog, Deal, PipelineStage
from app.schemas.deal import DealCreate, DealUpdate
from app.tasks.ai_tasks import score_deal_task

logger = logging.getLogger(__name__)


async def get_deal(db: AsyncSession, deal_id: int, *, for_update: bool = False) -> Deal:
    deal = await db.get(Deal, deal_id, with_for_update=for_update)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


async def require_client(db: AsyncSession, client_id: int) -> None:
    client = await db.get(Client, client_id, with_for_update={"read": True, "key_share": True})
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")


async def require_stage(db: AsyncSession, stage_id: int) -> PipelineStage:
    stage = await db.get(
        PipelineStage, stage_id, with_for_update={"read": True, "key_share": True}
    )
    if stage is None:
        raise HTTPException(status_code=404, detail="Pipeline stage not found")
    return stage


async def save_deal(db: AsyncSession, deal: Deal) -> Deal:
    await db.flush()
    await db.refresh(deal)
    await db.commit()
    return deal


async def create_deal(db: AsyncSession, data: DealCreate) -> Deal:
    await require_client(db, data.client_id)
    stage = await require_stage(db, data.stage_id)
    deal = Deal(**data.model_dump())
    if stage.is_won or stage.is_lost:
        deal.closed_at = datetime.now(timezone.utc)
    db.add(deal)
    return await save_deal(db, deal)


async def update_deal(db: AsyncSession, deal_id: int, data: DealUpdate) -> Deal:
    deal = await get_deal(db, deal_id, for_update=True)
    if data.client_id is not None and data.client_id != deal.client_id:
        await require_client(db, data.client_id)
        existing_log = await db.scalar(
            select(CommunicationLog.id).where(CommunicationLog.deal_id == deal.id).limit(1)
        )
        if existing_log is not None:
            raise HTTPException(
                status_code=400, detail="Cannot change the client of a deal with communications"
            )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(deal, field, value)
    return await save_deal(db, deal)


async def enqueue_deal_scoring(deal_id: int) -> str | None:
    try:
        task = await run_in_threadpool(score_deal_task.delay, deal_id)
        return task.id
    except (OperationalError, RedisError):
        logger.exception("Could not enqueue scoring for deal %s", deal_id)
        return None


async def change_deal_stage(db: AsyncSession, deal_id: int, new_stage_id: int) -> Deal:
    deal = await get_deal(db, deal_id, for_update=True)
    new_stage = await require_stage(db, new_stage_id)
    stage_changed = deal.stage_id != new_stage.id
    if stage_changed:
        current_stage = await require_stage(db, deal.stage_id)
        if current_stage.pipeline_id != new_stage.pipeline_id:
            raise HTTPException(status_code=400, detail="Target stage belongs to another pipeline")
        deal.stage_id = new_stage.id
    if new_stage.is_won or new_stage.is_lost:
        if stage_changed or deal.closed_at is None:
            deal.closed_at = datetime.now(timezone.utc)
    else:
        deal.closed_at = None
    await save_deal(db, deal)
    if stage_changed and not (new_stage.is_won or new_stage.is_lost):
        await enqueue_deal_scoring(deal.id)
    return deal
