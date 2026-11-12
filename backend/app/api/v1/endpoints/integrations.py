from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_async_db
from app.schemas.communication import CommunicationLogResponse
from app.schemas.integrations import (
    EmailSendRequest,
    EmailSendResponse,
    TelegramUpdate,
    TelegramWebhookResponse,
)
from app.services.deal_service import enqueue_deal_scoring
from app.services.email_service import send_email
from app.services.telegram_service import ingest_update

router = APIRouter(prefix="/integrations", tags=["integrations"])
Database = Annotated[AsyncSession, Depends(get_async_db)]


@router.post("/email/send")
async def send_sales_email(data: EmailSendRequest, db: Database) -> EmailSendResponse:
    log, mode = await send_email(db, data)
    return EmailSendResponse(
        delivery_mode=mode, communication=CommunicationLogResponse.model_validate(log)
    )


@router.post("/telegram/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    db: Database,
    secret_header: Annotated[str | None, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = None,
) -> TelegramWebhookResponse:
    settings = get_settings()
    secret = settings.telegram_webhook_secret
    if secret:
        if not compare_digest((secret_header or "").encode(), secret.get_secret_value().encode()):
            raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")
    elif settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram webhook secret is not configured")

    response, deal_id = await ingest_update(db, update)
    if deal_id is not None:
        response.task_id = await enqueue_deal_scoring(deal_id)
    return response
