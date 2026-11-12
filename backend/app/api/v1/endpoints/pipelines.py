from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.common import EntityId
from app.schemas.pipeline import BoardResponse, BoardStageResponse
from app.services import pipeline_service

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("/board")
async def get_board(
    db: Annotated[AsyncSession, Depends(get_async_db)], pipeline_id: EntityId | None = None
) -> BoardResponse:
    pipeline = await pipeline_service.get_kanban_board(db, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return BoardResponse(
        pipeline_id=pipeline.id,
        stages=[BoardStageResponse.model_validate(stage) for stage in pipeline.stages],
    )
