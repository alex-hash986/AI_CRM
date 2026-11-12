from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import Numeric, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Deal, PipelineStage
from app.schemas.analytics import SalesDashboardResponse, StageMetrics

ZERO = Decimal("0")


async def get_dashboard(db: AsyncSession, currency: str | None) -> SalesDashboardResponse:
    active = and_(Deal.closed_at.is_(None), ~PipelineStage.is_won, ~PipelineStage.is_lost)
    probability = func.coalesce(cast(Deal.ai_win_probability, Numeric), Decimal("0.2"))
    join_condition = PipelineStage.id == Deal.stage_id
    if currency is not None:
        join_condition = and_(join_condition, Deal.currency == currency)

    rows = (
        await db.execute(
            select(
                PipelineStage.id,
                PipelineStage.name,
                PipelineStage.is_won,
                PipelineStage.is_lost,
                Deal.currency,
                func.count(Deal.id).label("deal_count"),
                func.sum(Deal.budget).label("total"),
                func.sum(Deal.budget).filter(active).label("active_total"),
                func.sum(Deal.budget * probability).filter(active).label("weighted"),
                func.sum(Deal.ai_score).filter(active).label("score_sum"),
                func.count(Deal.ai_score).filter(active).label("score_count"),
            )
            .outerjoin(Deal, join_condition)
            .group_by(PipelineStage.id, Deal.currency)
            .order_by(PipelineStage.pipeline_id, PipelineStage.order, PipelineStage.id)
        )
    ).all()

    currencies = {row.currency for row in rows if row.currency is not None}
    if len(currencies) > 1:
        raise HTTPException(status_code=400, detail="Specify currency for a multi-currency dashboard")

    won = sum(row.deal_count for row in rows if row.is_won)
    lost = sum(row.deal_count for row in rows if row.is_lost)
    score_count = sum(row.score_count for row in rows)
    return SalesDashboardResponse(
        currency=currency or next(iter(currencies), None),
        total_pipeline_value=sum((row.active_total or ZERO for row in rows), ZERO),
        weighted_forecast_value=sum((row.weighted or ZERO for row in rows), ZERO),
        won_deals_revenue=sum((row.total or ZERO for row in rows if row.is_won), ZERO),
        average_ai_score=(
            sum(row.score_sum or 0 for row in rows) / score_count if score_count else None
        ),
        conversion_rate=100 * won / (won + lost) if won + lost else 0.0,
        stages_breakdown=[
            StageMetrics(
                stage_id=row.id, stage_name=row.name, deal_count=row.deal_count,
                total_amount=row.total or ZERO, weighted_amount=row.weighted or ZERO,
            )
            for row in rows
        ],
    )
