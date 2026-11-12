from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Pipeline, PipelineStage


async def get_kanban_board(db: AsyncSession, pipeline_id: int | None) -> Pipeline | None:
    query = select(Pipeline).options(
        selectinload(Pipeline.stages).selectinload(PipelineStage.deals)
    )
    if pipeline_id is None:
        query = query.order_by(Pipeline.id).limit(1)
    else:
        query = query.where(Pipeline.id == pipeline_id)

    # Pipeline.stages defines its ordering by PipelineStage.order.
    return await db.scalar(query)
