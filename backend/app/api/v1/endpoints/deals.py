from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.common import EntityId
from app.schemas.deal import DealCreate, DealResponse, DealStageUpdate, DealUpdate
from app.services import deal_service

router = APIRouter(prefix="/deals", tags=["deals"])
Database = Annotated[AsyncSession, Depends(get_async_db)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_deal(data: DealCreate, db: Database) -> DealResponse:
    deal = await deal_service.create_deal(db, data)
    return DealResponse.model_validate(deal)


@router.get("/{id}")
async def get_deal(id: EntityId, db: Database) -> DealResponse:
    deal = await deal_service.get_deal(db, id)
    return DealResponse.model_validate(deal)


@router.patch("/{id}")
async def update_deal(id: EntityId, data: DealUpdate, db: Database) -> DealResponse:
    deal = await deal_service.update_deal(db, id, data)
    return DealResponse.model_validate(deal)


@router.patch("/{id}/stage")
async def change_deal_stage(id: EntityId, data: DealStageUpdate, db: Database) -> DealResponse:
    deal = await deal_service.change_deal_stage(db, id, data.stage_id)
    return DealResponse.model_validate(deal)
