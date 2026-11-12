import logging
from email.message import EmailMessage
from typing import Literal

import aiosmtplib
from aiosmtplib.errors import SMTPException
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import CommunicationLog
from app.schemas.integrations import EmailSendRequest
from app.services.deal_service import get_deal

logger = logging.getLogger(__name__)


async def send_email(
    db: AsyncSession, data: EmailSendRequest
) -> tuple[CommunicationLog, Literal["smtp", "demo"]]:
    deal = await get_deal(db, data.deal_id, for_update=True)
    settings = get_settings()
    log = CommunicationLog(
        deal_id=deal.id,
        client_id=deal.client_id,
        channel="email",
        direction="outbound",
        content=f"To: {data.to_email}\nSubject: {data.subject}\n\n{data.body}",
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)

    mode: Literal["smtp", "demo"] = "demo"
    if settings.smtp_host:
        sender = settings.smtp_from_email or settings.smtp_username
        if not sender:
            raise HTTPException(status_code=503, detail="SMTP sender is not configured")
        message = EmailMessage()
        message["From"] = sender
        message["To"] = data.to_email
        message["Subject"] = data.subject
        message.set_content(data.body)
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username or None,
                password=settings.smtp_password.get_secret_value() if settings.smtp_password else None,
                use_tls=settings.smtp_tls == "implicit",
                start_tls=settings.smtp_tls == "starttls",
                timeout=10,
            )
        except (SMTPException, OSError, TimeoutError, ValueError):
            logger.warning("SMTP delivery failed for deal %s", deal.id)
            raise HTTPException(status_code=502, detail="SMTP delivery failed") from None
        mode = "smtp"
    else:
        logger.info("Simulated email delivery for deal %s", deal.id)

    await db.commit()
    return log, mode
