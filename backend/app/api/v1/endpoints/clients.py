from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.client import ClientCreate, ClientDetailResponse, ClientResponse
from app.schemas.common import EntityId, PaginatedResponse
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["clients"])
Database = Annotated[AsyncSession, Depends(get_async_db)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_client(data: ClientCreate, db: Database) -> ClientResponse:
    client = await client_service.create_client(db, data)
    return ClientResponse.model_validate(client)


@router.get("/")
async def list_clients(
    db: Database,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaginatedResponse[ClientResponse]:
    clients, total = await client_service.list_clients(db, limit, offset)
    return PaginatedResponse[ClientResponse](
        items=[ClientResponse.model_validate(client) for client in clients],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{id}")
async def get_client(id: EntityId, db: Database) -> ClientDetailResponse:
    client = await client_service.get_client(db, id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientDetailResponse.model_validate(client)
