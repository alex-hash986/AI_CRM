from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.schemas.analytics import CurrencyCode, SalesDashboardResponse
from app.services.analytics_service import get_dashboard

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(
    db: Annotated[AsyncSession, Depends(get_async_db)], currency: CurrencyCode | None = None
) -> SalesDashboardResponse:
    return await get_dashboard(db, currency)
