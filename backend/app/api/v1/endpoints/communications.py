from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.common import EntityId
from app.schemas.communication import (
    CommunicationCreateResponse, CommunicationLogCreate, CommunicationLogResponse,
)
from app.services import communication_service

router = APIRouter(tags=["communications"])
Database = Annotated[AsyncSession, Depends(get_async_db)]


@router.get("/deals/{deal_id}/communications")
async def deal_history(deal_id: EntityId, db: Database) -> list[CommunicationLogResponse]:
    logs = await communication_service.list_communications(db, deal_id=deal_id)
    return [CommunicationLogResponse.model_validate(log) for log in logs]


@router.get("/clients/{client_id}/communications")
async def client_history(client_id: EntityId, db: Database) -> list[CommunicationLogResponse]:
    logs = await communication_service.list_communications(db, client_id=client_id)
    return [CommunicationLogResponse.model_validate(log) for log in logs]


@router.post("/communications", status_code=status.HTTP_201_CREATED)
async def create_communication(data: CommunicationLogCreate, db: Database) -> CommunicationCreateResponse:
    log, task_id = await communication_service.create_communication(db, data)
    return CommunicationCreateResponse(
        **CommunicationLogResponse.model_validate(log).model_dump(), task_id=task_id
    )
