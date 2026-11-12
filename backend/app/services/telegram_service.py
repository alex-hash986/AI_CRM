import asyncio
import json
import logging
from decimal import Decimal
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Client, CommunicationLog, Deal, PipelineStage
from app.schemas.integrations import TelegramUpdate, TelegramWebhookResponse

logger = logging.getLogger(__name__)
HOT_LEAD_SCORE = 80


async def ingest_update(db: AsyncSession, update: TelegramUpdate) -> tuple[TelegramWebhookResponse, int | None]:
    if update.message is not None:
        chat = update.message.chat
        if chat.type != "private":
            return TelegramWebhookResponse(status="ignored"), None
        chat_id = chat.id
        content = (update.message.text or "").strip()
        name = " ".join(part for part in (chat.first_name, chat.last_name) if part) or chat.username
    else:
        chat_id, content, name = update.chat_id, update.text, update.username

    if chat_id is None or not 0 < chat_id < 2**52 or not content:
        return TelegramWebhookResponse(status="ignored"), None

    # Serialize first-contact creation and repeated updates for this chat.
    await db.execute(text("SELECT pg_advisory_xact_lock(:chat_id)"), {"chat_id": chat_id})
    if update.update_id is not None:
        existing = await db.scalar(
            select(CommunicationLog.id).where(CommunicationLog.telegram_update_id == update.update_id)
        )
        if existing is not None:
            return TelegramWebhookResponse(status="duplicate", communication_id=existing), None

    client = await db.scalar(select(Client).where(Client.telegram_chat_id == chat_id))
    if client is None:
        client = Client(name=(name or f"Telegram {chat_id}")[:255], telegram_chat_id=chat_id)
        db.add(client)
        await db.flush()

    deal = await db.scalar(
        select(Deal)
        .join(Deal.stage)
        .where(
            Deal.client_id == client.id, Deal.closed_at.is_(None),
            ~PipelineStage.is_won, ~PipelineStage.is_lost,
        )
        .order_by(Deal.created_at.desc(), Deal.id.desc())
        .limit(1)
        .with_for_update(of=Deal)
    )
    if deal is None:
        stage_id = await db.scalar(
            select(PipelineStage.id)
            .where(~PipelineStage.is_won, ~PipelineStage.is_lost)
            .order_by(PipelineStage.pipeline_id, PipelineStage.order, PipelineStage.id)
            .limit(1)
            .with_for_update(read=True, key_share=True)
        )
        if stage_id is None:
            raise HTTPException(status_code=409, detail="Create an open pipeline stage first")
        deal = Deal(
            title=f"Telegram: {client.name}"[:255], budget=Decimal("0"),
            currency=get_settings().telegram_lead_currency, stage_id=stage_id, client_id=client.id,
        )
        db.add(deal)
        await db.flush()

    log = CommunicationLog(
        deal_id=deal.id, client_id=client.id, channel="telegram", direction="inbound",
        content=content, telegram_update_id=update.update_id,
    )
    db.add(log)
    await db.flush()
    response = TelegramWebhookResponse(status="accepted", communication_id=log.id, deal_id=deal.id)
    await db.commit()
    return response, deal.id


def send_manager_message(token: str, chat_id: str, message: str) -> None:
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": message}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=8) as response:
        if not json.load(response).get("ok"):
            raise ValueError("Telegram rejected the notification")


async def notify_hot_lead(deal_id: int, title: str, score: int) -> None:
    settings = get_settings()
    if score < HOT_LEAD_SCORE or not settings.telegram_bot_token or not settings.telegram_manager_chat_id:
        return
    try:
        await asyncio.to_thread(
            send_manager_message,
            settings.telegram_bot_token.get_secret_value(),
            settings.telegram_manager_chat_id,
            f"Горячий лид #{deal_id}\n{title}\nAI-скоринг: {score}/100",
        )
    except (URLError, OSError, ValueError):
        logger.warning("Telegram notification failed for deal %s", deal_id)
