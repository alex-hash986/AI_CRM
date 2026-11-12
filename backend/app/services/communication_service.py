from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client, CommunicationLog
from app.schemas.communication import CommunicationLogCreate
from app.services.deal_service import enqueue_deal_scoring, get_deal


async def list_communications(
    db: AsyncSession, *, deal_id: int | None = None, client_id: int | None = None
) -> list[CommunicationLog]:
    query = select(CommunicationLog).order_by(
        CommunicationLog.created_at.desc(), CommunicationLog.id.desc()
    )
    if deal_id is not None:
        await get_deal(db, deal_id)
        query = query.where(CommunicationLog.deal_id == deal_id)
    else:
        if await db.get(Client, client_id) is None:
            raise HTTPException(status_code=404, detail="Client not found")
        query = query.where(CommunicationLog.client_id == client_id)
    return list(await db.scalars(query))


async def create_communication(
    db: AsyncSession, data: CommunicationLogCreate
) -> tuple[CommunicationLog, str | None]:
    if data.deal_id is not None:
        deal = await get_deal(db, data.deal_id, for_update=True)
        if deal.client_id != data.client_id:
            raise HTTPException(status_code=400, detail="Deal does not belong to this client")
    elif await db.get(Client, data.client_id, with_for_update={"read": True, "key_share": True}) is None:
        raise HTTPException(status_code=404, detail="Client not found")

    log = CommunicationLog(**data.model_dump())
    db.add(log)
    await db.flush()
    await db.refresh(log)
    await db.commit()
    if log.deal_id is not None and (log.channel == "note" or log.direction == "inbound"):
        return log, await enqueue_deal_scoring(log.deal_id)
    return log, None
