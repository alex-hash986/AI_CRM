import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime

from pydantic import JsonValue
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import joinedload
from sqlalchemy.pool import NullPool

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.models import CommunicationLog, Deal
from app.schemas.ai import EmailGenerateRequest
from app.services.ai_service import AIService, Context
from app.services.telegram_service import HOT_LEAD_SCORE, notify_hot_lead


@dataclass(frozen=True)
class DealContext:
    deal: Context
    client: Context
    logs: list[Context]
    updated_at: datetime
    latest_log_id: int | None


@asynccontextmanager
async def task_sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    # Each prefork task owns its engine and asyncio loop.
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        yield async_sessionmaker(engine)
    finally:
        await engine.dispose()


def deal_logs(deal_id: int, client_id: int) -> Select[tuple[CommunicationLog]]:
    return (
        select(CommunicationLog)
        .where(CommunicationLog.deal_id == deal_id, CommunicationLog.client_id == client_id)
        .order_by(CommunicationLog.created_at.desc(), CommunicationLog.id.desc())
    )


async def load_context(db: AsyncSession, deal_id: int) -> DealContext:
    deal = await db.scalar(
        select(Deal).where(Deal.id == deal_id).options(joinedload(Deal.client), joinedload(Deal.stage))
    )
    if deal is None:
        raise ValueError("Deal not found")
    logs = list(await db.scalars(deal_logs(deal_id, deal.client_id).limit(8)))
    return DealContext(
        deal={
            "title": deal.title,
            "budget": str(deal.budget),
            "currency": deal.currency,
            "stage": deal.stage.name,
            "stage_order": deal.stage.order,
            "is_won": deal.stage.is_won,
            "is_lost": deal.stage.is_lost,
            "company": deal.client.company,
        },
        client={"name": deal.client.name, "company": deal.client.company},
        logs=[
            {
                "channel": log.channel,
                "direction": log.direction,
                "created_at": log.created_at.isoformat(),
                "content": log.content[:1500],
            }
            for log in reversed(logs)
        ],
        updated_at=deal.updated_at,
        latest_log_id=logs[0].id if logs else None,
    )


async def score_deal(deal_id: int) -> dict[str, JsonValue]:
    async with task_sessions() as sessions:
        async with sessions() as db:
            context = await load_context(db, deal_id)
        output = await AIService().score_deal(context.deal, context.logs)
        async with sessions.begin() as db:
            deal = await db.get(Deal, deal_id, with_for_update=True)
            if deal is None or deal.updated_at != context.updated_at:
                raise RuntimeError("Deal changed during scoring")
            latest = await db.scalar(deal_logs(deal_id, deal.client_id).limit(1))
            if (latest.id if latest else None) != context.latest_log_id:
                raise RuntimeError("Deal communications changed during scoring")
            was_hot = deal.ai_score is not None and deal.ai_score >= HOT_LEAD_SCORE
            title = deal.title
            deal.ai_score = output.score
            deal.ai_win_probability = output.win_probability
            deal.ai_next_step = output.next_step
            deal.ai_risk_assessment = output.risk_assessment
    if not was_hot and output.score >= HOT_LEAD_SCORE:
        await notify_hot_lead(deal_id, title, output.score)
    return output.model_dump(mode="json")


async def generate_email(request: EmailGenerateRequest) -> dict[str, JsonValue]:
    async with task_sessions() as sessions, sessions() as db:
        context = await load_context(db, request.deal_id)
    output = await AIService().generate_sales_email(
        context.deal, context.client, context.logs, request
    )
    return output.model_dump(mode="json")


@celery_app.task(name="crm.ai.score_deal", track_started=True, ignore_result=False)
def score_deal_task(deal_id: int) -> dict[str, JsonValue]:
    return asyncio.run(score_deal(deal_id))


@celery_app.task(name="crm.ai.generate_email", track_started=True, ignore_result=False)
def generate_email_task(request_data: dict[str, JsonValue]) -> dict[str, JsonValue]:
    request = EmailGenerateRequest.model_validate(request_data)
    return asyncio.run(generate_email(request))
