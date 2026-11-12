from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Client
from app.schemas.client import ClientCreate


async def create_client(db: AsyncSession, data: ClientCreate) -> Client:
    client = Client(**data.model_dump())
    db.add(client)
    await db.flush()
    await db.refresh(client)
    await db.commit()
    return client


async def list_clients(
    db: AsyncSession, limit: int, offset: int
) -> tuple[list[Client], int]:
    query = select(Client).order_by(Client.id).limit(limit).offset(offset)
    clients = list(await db.scalars(query))
    total = await db.scalar(select(func.count()).select_from(Client))
    return clients, total or 0


async def get_client(db: AsyncSession, client_id: int) -> Client | None:
    query = select(Client).where(Client.id == client_id).options(selectinload(Client.deals))
    return await db.scalar(query)
